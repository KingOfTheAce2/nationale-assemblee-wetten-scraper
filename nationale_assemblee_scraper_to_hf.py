import os
import subprocess
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pdfminer.high_level import extract_text as pdfminer_extract_text
from datasets import Dataset
from huggingface_hub import HfApi

# Configuration
# Target URLs from SRIS
URLS = [
    "https://www.sris.sr/administratief-recht/",
    "https://www.sris.sr/burgerlijk-recht/",
    "https://www.sris.sr/burgerlijk-procesrecht/",
    "https://www.sris.sr/staatsrecht/",
    "https://www.sris.sr/strafrecht/",
    "https://www.sris.sr/strafprocesrecht/",
    "https://www.sris.sr/wettenarchief/",
]
BASE_DOMAIN = urlparse(URLS[0]).netloc
OUTPUT_DIR = "downloaded_pdfs"
HF_REPO_ID = "vGassen/Surinam-Dutch-Legislation"
SOURCE_NAME = "Nationale Assemblee Suriname"
DB_TABLE = "nationale_assemblee_docs"  # optional SQLite for tracking

os.makedirs(OUTPUT_DIR, exist_ok=True)

visited_urls = set()
docs = []


def is_valid_pdf_link(href: str) -> bool:
    return href and href.lower().endswith('.pdf')


def is_internal_link(href: str) -> bool:
    parsed = urlparse(href)
    return not parsed.netloc or parsed.netloc == BASE_DOMAIN


def convert_pdf_to_text(pdf_bytes: bytes) -> str:
    """Convert PDF bytes to text.

    The function first tries ``pdftotext`` and falls back to ``pdfminer.six`` if
    no text was extracted. This helps catch cases where ``pdftotext`` fails even
    though the PDF contains selectable text.
    """

    text = ""

    try:
        proc = subprocess.run(
            ["pdftotext", "-q", "-", "-"],
            input=pdf_bytes,
            capture_output=True,
            check=True,
        )
        text = proc.stdout.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"pdftotext failed: {e}")

    if not text.strip():
        try:
            text = pdfminer_extract_text(BytesIO(pdf_bytes))
            if text.strip():
                print("Extracted text using pdfminer fallback")
        except Exception as e:
            print(f"pdfminer fallback failed: {e}")

    return text


def download_and_extract(pdf_url: str) -> None:
    filename = os.path.basename(urlparse(pdf_url).path)
    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        print(f"Skipping already downloaded: {filename}")
    else:
        try:
            resp = requests.get(pdf_url)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to download {pdf_url}: {e}")
            return

        pdf_data = resp.content
        if not pdf_data.startswith(b"%PDF"):
            ct = resp.headers.get("Content-Type", "")
            print(
                f"Skipping {pdf_url} - content does not look like PDF (content-type: {ct})"
            )
            return

        with open(filepath, "wb") as f:
            f.write(pdf_data)
        print(f"Downloaded: {filename}")

    with open(filepath, "rb") as f:
        text = convert_pdf_to_text(f.read())
    if text.strip():
        docs.append({
            "URL": pdf_url,
            "content": text,
            "source": SOURCE_NAME
        })
    else:
        print(f"Empty text for {filename}, skipping.")


def scrape(url: str) -> None:
    if url in visited_urls:
        return
    visited_urls.add(url)
    print(f"Visiting: {url}")
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to access {url}: {e}")
        return
    soup = BeautifulSoup(resp.text, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        full = urljoin(url, href)
        if is_valid_pdf_link(full):
            download_and_extract(full)
        elif is_internal_link(full):
            scrape(full)


def push_to_hf(docs_list: list, repo_id: str) -> None:
    if not docs_list:
        print("No documents to push.")
        return
    ds = Dataset.from_list(docs_list)
    local_path = "data.parquet"
    ds.to_parquet(local_path)
    api = HfApi()
    api.upload_file(
        path_or_fileobj=local_path,
        path_in_repo="data/latest.parquet",
        repo_id=repo_id,
        repo_type="dataset",
    )
    print(f"Uploaded {len(docs_list)} docs to {repo_id}")


if __name__ == '__main__':
    for start_url in URLS:
        scrape(start_url)
    push_to_hf(docs, HF_REPO_ID)
