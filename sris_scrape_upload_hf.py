import os
import subprocess
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pdfminer.high_level import extract_text as pdfminer_extract_text
from datasets import Dataset
from huggingface_hub import HfApi

# Use a persistent session with a browser-like user agent to avoid 406 errors
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/118.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,*/*;q=0.8"
    ),
}

session = requests.Session()
session.headers.update(HEADERS)

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
OUTPUT_DIR = "sris_pdfs"
HF_REPO_ID = "vGassen/Surinam-Dutch-Legislation"
SOURCE_NAME = "Suriname Rechtsinstituut"

os.makedirs(OUTPUT_DIR, exist_ok=True)

visited_urls = set()
docs = []

def is_valid_pdf_link(href: str) -> bool:
    return href and href.lower().endswith(".pdf")


def is_internal_link(href: str) -> bool:
    parsed = urlparse(href)
    return not parsed.netloc or parsed.netloc == BASE_DOMAIN

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in "._- ")

def convert_pdf_to_text(pdf_bytes: bytes) -> str:
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


def download_and_extract(url: str) -> None:
    filename = sanitize_filename(os.path.basename(urlparse(url).path))
    filepath = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(filepath):
        print(f"Skipping already downloaded: {filename}")
    else:
        print(f"Downloading: {url}")
        try:
            response = session.get(url)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return

        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"Saved: {filepath}")

    with open(filepath, "rb") as f:
        text = convert_pdf_to_text(f.read())

    if text.strip():
        docs.append({
            "URL": url,
            "content": text,
            "source": SOURCE_NAME,
        })
    else:
        print(f"No text extracted for {filename}")

def scrape(url: str) -> None:
    if url in visited_urls:
        return
    visited_urls.add(url)
    print(f"Visiting: {url}")
    try:
        response = session.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    for link in soup.find_all("a", href=True):
        href = link["href"]
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


if __name__ == "__main__":
    for start_url in URLS:
        scrape(start_url)
    push_to_hf(docs, HF_REPO_ID)
