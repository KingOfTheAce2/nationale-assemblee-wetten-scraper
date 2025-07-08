import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import subprocess
from datasets import Dataset
from huggingface_hub import HfApi

# Configuration
BASE_URL = "https://www.dna.sr/wetgeving/surinaamse-wetten/"
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
    return not parsed.netloc or parsed.netloc == urlparse(BASE_URL).netloc


def convert_pdf_to_text(pdf_bytes: bytes) -> str:
    """Convert PDF bytes to text using pdftotext."""
    try:
        proc = subprocess.run(
            ["pdftotext", "-q", "-", "-"],
            input=pdf_bytes,
            capture_output=True,
            check=True
        )
        return proc.stdout.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Failed to convert PDF: {e}")
        return ""


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
        with open(filepath, 'wb') as f:
            f.write(resp.content)
        print(f"Downloaded: {filename}")
    # Convert
    with open(filepath, 'rb') as f:
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
        elif is_internal_link(href) and BASE_URL in full:
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
    scrape(BASE_URL)
    push_to_hf(docs, HF_REPO_ID)
