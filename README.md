# Nationale Assemblee Wetten Scraper

This repository provides small Python scripts to download Surinamese legislation PDFs and optionally push them to the Hugging Face Hub or Google Drive.

## Overview

- `nationale_assemblee_scraper_to_hf.py` downloads PDFs from the Suriname Rechtsinstituut (SRIS), extracts their text and pushes a dataset to Hugging Face.
- `sris_scrape_upload_hf.py` performs the same task for SRIS while also uploading the results to Hugging Face.
- `sru_scraper.py` recursively downloads PDFs from the site without uploading them anywhere.
- `sris_scraper.py` *only* downloads legislation PDFs from SRIS – it does not upload to Hugging Face.
- `upload_to_drive.py` uploads a zipped folder of PDFs to Google Drive using PyDrive.

## Installation

Python 3.8 or newer is recommended. Install the Python dependencies with

```bash
pip install -r requirements.txt
```

`pdftotext` from the `poppler-utils` package must be available on your system for text extraction. On Debian/Ubuntu you can install it with:

```bash
sudo apt-get install poppler-utils
```

## Usage

Set the `HF_TOKEN` environment variable if you plan to upload to Hugging Face.
Then run one of the upload scripts:

```bash
python nationale_assemblee_scraper_to_hf.py  # Scrape SRIS and upload
python sris_scrape_upload_hf.py              # Alternative SRIS uploader
```

These scripts download PDFs to `downloaded_pdfs/` (or `sris_pdfs/`), extract
text and upload `data/latest.parquet` to the dataset configured inside the
script.

Other utilities can be executed directly:

```bash
python sru_scraper.py     # Download PDFs from dna.sr
python sris_scrape_upload_hf.py # Download from sris.sr and upload to HF
python sris_scraper.py    # Download PDFs from sris.sr
python upload_to_drive.py # Upload clean_pdfs.zip to Google Drive
```

Each script prints progress information while running.

## License

This project is licensed under the terms of the MIT license. See the
[LICENSE](LICENSE) file for details.
