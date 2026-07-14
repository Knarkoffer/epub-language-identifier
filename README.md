# EPUB Language Identifier

EPUB Language Identifier scans `.epub` and `.mobi` files and writes a CSV language report. It checks ebook metadata for both formats. For EPUB files, it also reads book text once and reuses that extracted text for ISBN-based language lookup and sampled text language detection.

The report columns are:

```csv
FILENAME,FROM_METADATA,FROM_ISBN,FROM_DETECTION
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Scan the current directory recursively and write `language-report.csv`:

```bash
python3 identify-epub-language.py
```

Scan a specific directory:

```bash
python3 identify-epub-language.py --path /path/to/books
```

Choose a report path:

```bash
python3 identify-epub-language.py --path /path/to/books --output /tmp/language-report.csv
```

Scan only the selected directory:

```bash
python3 identify-epub-language.py --path /path/to/books --no-recursive
```

Show per-file warnings:

```bash
python3 identify-epub-language.py --path /path/to/books --verbose
```

Warnings cover metadata lookup, EPUB parsing, ISBN lookup, and text language detection failures. Without `--verbose`, files with failed detection steps are still included in the report with `?` for unknown values.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Notes

The CSV report is overwritten on each run. Keep ebook files outside the repository; `.epub`, `.mobi`, and generated report files are ignored by Git.
