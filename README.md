# EPUB Language Identifier

EPUB Language Identifier scans a directory tree for `.epub` and `.mobi` files and reports likely book language from available metadata. For EPUB files, it also tries to identify language from ISBN-derived information and sampled text detection.

The main script is `identify-epub-language.py`. It writes a pipe-delimited CSV report with these columns:

```text
FILENAME|FROM_METADATA|FROM_ISBN|FROM_DETECTION
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Usage

Scan the current directory recursively and write `output3.txt`:

```bash
python identify-epub-language.py
```

Scan a specific directory:

```bash
python identify-epub-language.py --path /path/to/books
```

Write the report to a specific file:

```bash
python identify-epub-language.py --path /path/to/books --output language-report.txt
```

Only scan the selected directory, without descending into subdirectories:

```bash
python identify-epub-language.py --path /path/to/books --no-recursive
```

Print per-file warnings for metadata, EPUB parsing, ISBN, or language-detection failures:

```bash
python identify-epub-language.py --path /path/to/books --verbose
```

The script recursively scans below the current working directory for `.epub` and `.mobi` files. EPUB language detection reads book contents to sample text, while MOBI handling is limited to metadata fetched through `ebookatty`.

## Tests

Run the test suite with:

```bash
python -m unittest discover -s tests
```

## Notes

The output file is overwritten each time the script runs. Keep ebook files outside the repository; `.epub`, `.mobi`, and generated output files are ignored by Git.
