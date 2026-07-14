# EPUB Language Identifier

EPUB Language Identifier scans the current directory tree for `.epub` and `.mobi` files and reports likely book language from available metadata. For EPUB files, it also tries to identify language from ISBN-derived information and sampled text detection.

The main script is `identify-epub-language.py`. It writes a pipe-delimited `output3.txt` report with these columns:

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

Run the script from the directory that contains the ebook files you want to inspect:

```bash
python /path/to/identify-epub-language.py
```

Or copy the script into the target folder and run:

```bash
python identify-epub-language.py
```

The script recursively scans below the current working directory for `.epub` and `.mobi` files. EPUB language detection reads book contents to sample text, while MOBI handling is limited to metadata fetched through `ebookatty`.

## Notes

`output3.txt` is overwritten each time the script runs. Keep ebook files outside the repository; `.epub`, `.mobi`, and generated output files are ignored by Git.
