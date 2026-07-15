from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

import identify_epub_language

REPO_ROOT = Path(__file__).resolve().parents[1]


def dependency_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


class IdentifyEpubLanguageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = identify_epub_language

    def test_find_ebook_files_is_case_insensitive_and_recursive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "nested"
            nested.mkdir()
            epub_file = root / "Example.EPUB"
            mobi_file = nested / "Book.MoBi"
            text_file = nested / "notes.txt"
            epub_file.write_text("", encoding="utf-8")
            mobi_file.write_text("", encoding="utf-8")
            text_file.write_text("", encoding="utf-8")

            recursive = self.module.find_ebook_files(root)
            shallow = self.module.find_ebook_files(root, recursive=False)

            self.assertEqual(recursive, [epub_file.resolve(), mobi_file.resolve()])
            self.assertEqual(shallow, [epub_file.resolve()])

    def test_write_report_uses_comma_delimited_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "report.csv"
            result = self.module.LanguageResult(
                filename="book,with-delimiter.epub",
                from_metadata="English",
                from_isbn="?",
                from_detection="Swedish",
            )

            self.module.write_report([result], output_file)

            with output_file.open(encoding="utf-8", newline="") as file_handle:
                rows = list(csv.reader(file_handle))

            self.assertEqual(rows[0], list(self.module.REPORT_COLUMNS))
            self.assertEqual(rows[1], list(result.as_row()))

    def test_main_writes_empty_report_for_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_file = root / "report.csv"

            exit_code = self.module.main(
                ["--path", str(root), "--output", str(output_file)]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                output_file.read_text(encoding="utf-8"),
                "FILENAME,FROM_METADATA,FROM_ISBN,FROM_DETECTION\n",
            )

    @unittest.skipUnless(
        dependency_available("bs4") and dependency_available("ebooklib"),
        "EPUB generation dependencies are not installed",
    )
    def test_get_epub_texts_reads_generated_epub_content(self) -> None:
        from ebooklib import epub

        with tempfile.TemporaryDirectory() as temp_dir:
            epub_file = Path(temp_dir) / "generated.epub"
            book = epub.EpubBook()
            book.set_identifier("generated-test-book")
            book.set_title("Generated Test Book")
            book.set_language("en")

            chapter = epub.EpubHtml(
                title="Chapter 1",
                file_name="chapter.xhtml",
                lang="en",
            )
            chapter.content = (
                "<html><body><p>"
                "This is generated EPUB content for tests."
                "</p></body></html>"
            )
            book.add_item(chapter)
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = ["nav", chapter]

            epub.write_epub(str(epub_file), book)

            texts = self.module.get_epub_texts(epub_file)

            self.assertTrue(
                any("generated EPUB content for tests" in text for text in texts)
            )


if __name__ == "__main__":
    unittest.main()
