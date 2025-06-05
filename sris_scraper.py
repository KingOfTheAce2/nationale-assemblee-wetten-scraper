import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Target URLs from SRIS
URLS = [
    "https://www.sris.sr/administratief-recht/",
    "https://www.sris.sr/burgerlijk-recht/",
    "https://www.sris.sr/burgerlijk-procesrecht/",
    "https://www.sris.sr/staatsrecht/",
    "https://www.sris.sr/strafrecht/",
    "https://www.sris.sr/strafprocesrecht/",
    "https://www.sris.sr/wettenarchief/"
]

OUTPUT_DIR = "sris_pdfs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_valid_pdf(href):
    return href and href.lower().endswith(".pdf")

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in "._- ")

def download_pdf(url):
    filename = sanitize_filename(os.path.basename(urlparse(url).path))
    filepath = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(filepath):
        print(f"Already downloaded: {filename}")
        return

    print(f"Downloading: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"Saved: {filepath}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def scrape_pdfs_from_page(url):
    print(f"\nScanning: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    for link in soup.find_all("a", href=True):
        pdf_url = urljoin(url, link["href"])
        if is_valid_pdf(pdf_url):
            download_pdf(pdf_url)

# Process all URLs
for url in URLS:
    scrape_pdfs_from_page(url)
