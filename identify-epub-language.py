#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_OUTPUT = "language-report.csv"
EBOOK_SUFFIXES = {".epub", ".mobi"}
REPORT_COLUMNS = ("FILENAME", "FROM_METADATA", "FROM_ISBN", "FROM_DETECTION")
SKIPPED_EPUB_DOCUMENTS = {
    "toc.ncx",
    "OEBPS/stylesheet.css",
    "OEBPS/title_page.xhtml",
}


class LanguageIdentificationError(Exception):
    """Raised when a single detection strategy fails for a specific file."""


@dataclass(frozen=True)
class LanguageResult:
    filename: str
    from_metadata: str = "?"
    from_isbn: str = "?"
    from_detection: str = "?"

    def as_row(self) -> tuple[str, str, str, str]:
        """Return the result fields in CSV column order."""
        return (
            self.filename,
            self.from_metadata,
            self.from_isbn,
            self.from_detection,
        )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the ebook language scanner."""
    parser = argparse.ArgumentParser(
        description="Identify likely languages for EPUB and MOBI files."
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.cwd(),
        help="Directory to scan. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(DEFAULT_OUTPUT),
        help=f"Report path. Defaults to {DEFAULT_OUTPUT}.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-file warnings to stderr.",
    )

    recursion = parser.add_mutually_exclusive_group()
    recursion.add_argument(
        "--recursive",
        dest="recursive",
        action="store_true",
        default=True,
        help="Scan subdirectories. This is the default.",
    )
    recursion.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Only scan the selected directory.",
    )

    return parser.parse_args(argv)


def find_ebook_files(root: Path, recursive: bool = True) -> list[Path]:
    """Return EPUB and MOBI files under root, sorted case-insensitively by path."""
    root = root.expanduser()
    pattern = "**/*" if recursive else "*"
    return sorted(
        (
            path.resolve()
            for path in root.glob(pattern)
            if path.is_file() and path.suffix.lower() in EBOOK_SUFFIXES
        ),
        key=lambda path: str(path).casefold(),
    )


def most_frequent(values: Iterable[str]) -> str | None:
    """Return the most common value, or None when the iterable is empty."""
    counter = Counter(values)
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def language_name(language_code: str) -> str:
    """Resolve an ISO 639 language code to its English language name."""
    try:
        from iso639 import Lang
    except ImportError as exc:
        raise LanguageIdentificationError("Missing dependency: iso639-lang") from exc

    try:
        return Lang(str(language_code)).name
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise LanguageIdentificationError(
            f"Could not resolve language code {language_code!r}"
        ) from exc


def get_metadata_language(book_file: Path) -> str | None:
    """Read ebook metadata and return the declared language name when present."""
    try:
        from ebookatty import MetadataFetcher
    except ImportError as exc:
        raise LanguageIdentificationError("Missing dependency: ebookatty") from exc

    try:
        metadata = MetadataFetcher(str(book_file)).get_metadata()
    except (AttributeError, LookupError, OSError, TypeError, ValueError) as exc:
        raise LanguageIdentificationError(f"Could not read metadata: {exc}") from exc

    if not metadata or not metadata.get("language"):
        return None

    return language_name(metadata["language"])


def get_epub_texts(epub_file: Path) -> list[str]:
    """Extract readable text chunks from content documents inside an EPUB file."""
    try:
        from bs4 import BeautifulSoup
        from ebooklib import epub
    except ImportError as exc:
        raise LanguageIdentificationError(f"Missing dependency: {exc.name}") from exc

    try:
        book = epub.read_epub(str(epub_file))
    except (AttributeError, LookupError, OSError, TypeError, ValueError) as exc:
        raise LanguageIdentificationError(f"Could not read EPUB: {exc}") from exc

    texts: list[str] = []
    for item in book.get_items():
        file_name = getattr(item, "file_name", "")
        if file_name in SKIPPED_EPUB_DOCUMENTS:
            continue

        content = getattr(item, "content", b"")
        if not isinstance(content, bytes):
            continue

        html = content.decode("utf-8", "ignore")
        text = BeautifulSoup(html, features="lxml").get_text(" ", strip=True)
        if text:
            texts.append(text)

    return texts


def get_isbn_language(texts: Iterable[str]) -> str | None:
    """Find the first ISBN-13 in the text and return isbnlib's language result."""
    try:
        import isbnlib
    except ImportError as exc:
        raise LanguageIdentificationError("Missing dependency: isbnlib") from exc

    for text in texts:
        for candidate in isbnlib.get_isbnlike(text, level="normal"):
            if isbnlib.is_isbn13(candidate):
                language = isbnlib.info(candidate)
                suffix = " language"
                if language.endswith(suffix):
                    language = language[: -len(suffix)]
                return language

    return None


def detect_text_language(texts: Iterable[str]) -> str | None:
    """Detect the most frequent language across sampled sentences from ebook text."""
    try:
        import langdetect
    except ImportError as exc:
        raise LanguageIdentificationError("Missing dependency: langdetect") from exc

    detected_languages: list[str] = []
    for text in texts:
        if "@" in text or "<" in text:
            continue

        sentences = re.findall(r".*?[.!?]+", text)
        if len(sentences) <= 10:
            continue

        try:
            for sentence in sentences[:10]:
                detected_languages.append(langdetect.detect(sentence))
        except langdetect.lang_detect_exception.LangDetectException:
            continue

    language_code = most_frequent(detected_languages)
    if not language_code:
        return None

    return language_name(language_code)


def analyze_file(book_file: Path) -> tuple[LanguageResult, list[str]]:
    """Run available language detection strategies for one ebook file."""
    warnings: list[str] = []
    metadata_language = "?"
    isbn_language = "?"
    detected_language = "?"

    try:
        metadata_language = get_metadata_language(book_file) or "?"
    except LanguageIdentificationError as exc:
        warnings.append(f"{book_file.name}: metadata detection failed: {exc}")

    if book_file.suffix.lower() == ".epub":
        try:
            epub_texts = get_epub_texts(book_file)
        except LanguageIdentificationError as exc:
            epub_texts = []
            warnings.append(f"{book_file.name}: EPUB text extraction failed: {exc}")

        if epub_texts:
            try:
                isbn_language = get_isbn_language(epub_texts) or "?"
            except LanguageIdentificationError as exc:
                warnings.append(f"{book_file.name}: ISBN lookup failed: {exc}")

            try:
                detected_language = detect_text_language(epub_texts) or "?"
            except LanguageIdentificationError as exc:
                warnings.append(f"{book_file.name}: language detection failed: {exc}")

    return (
        LanguageResult(
            filename=book_file.name,
            from_metadata=metadata_language,
            from_isbn=isbn_language,
            from_detection=detected_language,
        ),
        warnings,
    )


def write_report(results: Iterable[LanguageResult], output_file: Path) -> None:
    """Write language identification results to a CSV report file."""
    output_file = output_file.expanduser()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.writer(file_handle, lineterminator="\n")
        writer.writerow(REPORT_COLUMNS)
        for result in results:
            writer.writerow(result.as_row())


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line scanner and return a process exit code."""
    args = parse_args(argv)
    ebook_files = find_ebook_files(args.path, recursive=args.recursive)
    results: list[LanguageResult] = []
    warnings: list[str] = []
    stdout_writer = csv.writer(sys.stdout, lineterminator="\n")

    for ebook_file in ebook_files:
        result, file_warnings = analyze_file(ebook_file)
        results.append(result)
        warnings.extend(file_warnings)
        stdout_writer.writerow(result.as_row())

    write_report(results, args.output)

    if args.verbose:
        for warning in warnings:
            print(warning, file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
