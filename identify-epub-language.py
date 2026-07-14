#!/usr/bin/env python3
# encoding: utf-8

import random
import os
import re
from pathlib import Path

import isbnlib  # pip install isbnlib
import langdetect  # pip install langdetect
from ebooklib import epub  # pip install EbookLib
from bs4 import BeautifulSoup  # pip install beautifulsoup4
from iso639 import Lang  # pip install iso639-lang
from ebookatty import MetadataFetcher  # pip install ebookatty


path = os.getcwd()
#path = r"/mnt/l/TEMP/ScriptedBookDownloads"
#path = r"L:\TEMP\ScriptedBookDownloads\ALL"
#path = r"C:\KKo"
#path = r"/mnt/c/KKo"
all_files = (p.resolve() for p in Path(path).glob("**/*") if p.suffix in {".mobi", ".epub"})


def most_frequent(input_list):
    return max(set(input_list), key=input_list.count)


def get_epub_isbn(epub_file):

    unwanted_doc_files = [r'toc.ncx', r'OEBPS/stylesheet.css', r'OEBPS/title_page.xhtml']

    book_entity = epub.read_epub(epub_file)

    for doc in book_entity.get_items():

        if doc.file_name not in unwanted_doc_files:

            doc_content = str(doc.content.decode('utf-8', 'ignore'))
            soup_content = BeautifulSoup(doc_content, features="lxml")

            chapter_text = soup_content.get_text()

            all = isbnlib.get_isbnlike(chapter_text, level='normal')

            for candidate in all:
                if isbnlib.is_isbn13(candidate):
                    return candidate

    return None


def get_epub_language(epub_file):

    unwanted_doc_files = [r'toc.ncx', r'OEBPS/stylesheet.css', r'OEBPS/title_page.xhtml']

    book_entity = epub.read_epub(epub_file)

    for doc in book_entity.get_items():

        if doc.file_name not in unwanted_doc_files:

            doc_content = str(doc.content.decode('utf-8', 'ignore'))
            soup_content = BeautifulSoup(doc_content, features="lxml")

            chapter_text = soup_content.get_text()

            # Unwanted chars
            unwanted_chars = ["@", "<"]

            if not any(x in unwanted_chars for x in chapter_text):
                sentences = re.findall(r".*?[\.\!\?]+", chapter_text)

                detected_languages = []
                if sentences:
                    try:
                        if len(sentences) > 10:
                            random_sentances = random.sample(sentences, 10)

                            for sentance in random_sentances:
                                language_shortcode = langdetect.detect(sentance)
                                detected_languages.append(language_shortcode)

                            if detected_languages:
                                return most_frequent(detected_languages)

                    except langdetect.lang_detect_exception.LangDetectException:
                        pass

    return None


output_file = r"output3.txt"

with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"FILENAME|FROM_METADATA|FROM_ISBN|FROM_DETECTION\n")


#print(f"Will now iterate over {len(list(all_files))} files")
for item in all_files:

    book_language_md = "?"
    book_language_isbn = "?"
    book_language_detect = "?"

    file_path = os.path.join(path, item)
    file_name = item.stem + item.suffix
    file_extension = item.suffix.lstrip(".").upper()

    book_language = ""

    # Figure it out based on metadata
    try:
        book_metadata = MetadataFetcher(file_path)
        book_md = book_metadata.get_metadata()
        if book_md:
            if book_md.get("language"):
                book_language_short = book_md.get("language")
                book_language_md = Lang(book_language_short).name
    except:
        pass

    # Figure it out based on ISBN
    try:
        if str(item).lower().endswith(".epub"):
            book_isbn = get_epub_isbn(file_path)

            if book_isbn:
                book_language_isbn = isbnlib.info(book_isbn)
                if book_language_isbn.endswith(" language"):
                    book_language_isbn = book_language_isbn[:-len(" language")]
    except Exception as e:
        print(f"Exception: {e}")
        pass

    # Figure it out based on language detection
    try:
        if str(item).lower().endswith(".epub"):
            book_language_detect_short = get_epub_language(file_path)
            if book_language_detect_short:
                book_language_detect = Lang(str(book_language_detect_short)).name
    except:
        pass

    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"{file_name}|{book_language_md}|{book_language_isbn}|{book_language_detect}\n")

    print(f"{file_name}|{book_language_md}|{book_language_isbn}|{book_language_detect}")
