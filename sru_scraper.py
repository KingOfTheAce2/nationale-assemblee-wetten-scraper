import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE_URL = "https://www.dna.sr/wetgeving/surinaamse-wetten/"
OUTPUT_DIR = "downloaded_pdfs"

visited_urls = set()
os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_valid_pdf_link(href):
    return href and href.lower().endswith(".pdf")

def is_internal_link(href):
    return href and not urlparse(href).netloc or urlparse(href).netloc == urlparse(BASE_URL).netloc

def scrape_page_for_links(url):
    if url in visited_urls:
        return
    visited_urls.add(url)

    try:
        print(f"Visiting: {url}")
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Error visiting {url}: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", href=True)

    for link in links:
        href = link['href']
        full_url = urljoin(url, href)

        if is_valid_pdf_link(full_url):
            download_pdf(full_url)
        elif is_internal_link(href) and "wetgeving/surinaamse-wetten" in full_url:
            scrape_page_for_links(full_url)

def download_pdf(pdf_url):
    filename = os.path.basename(urlparse(pdf_url).path)
    filepath = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(filepath):
        print(f"Already downloaded: {filename}")
        return

    try:
        print(f"Downloading: {pdf_url}")
        response = requests.get(pdf_url)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"Saved: {filepath}")
    except Exception as e:
        print(f"Failed to download {pdf_url}: {e}")

# Start
scrape_page_for_links(BASE_URL)
