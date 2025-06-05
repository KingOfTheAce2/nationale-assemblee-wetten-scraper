import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Base URL of the website
BASE_URL = "https://www.dna.sr/wetgeving/surinaamse-wetten/"
OUTPUT_DIR = "downloaded_pdfs"

# Make sure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_valid_pdf_link(href):
    return href and href.lower().endswith(".pdf")

def scrape_page_for_links(url):
    print(f"Visiting: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all links
    links = soup.find_all("a", href=True)
    
    for link in links:
        href = link['href']
        full_url = urljoin(url, href)

        if is_valid_pdf_link(href):
            download_pdf(full_url)
        elif is_internal_link(href):
            scrape_page_for_links(full_url)

def is_internal_link(href):
    parsed = urlparse(href)
    return parsed.netloc == '' or parsed.netloc == urlparse(BASE_URL).netloc

def download_pdf(pdf_url):
    filename = os.path.basename(urlparse(pdf_url).path)
    filepath = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(filepath):
        print(f"Already downloaded: {filename}")
        return

    print(f"Downloading: {pdf_url}")
    response = requests.get(pdf_url)
    if response.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"Saved: {filepath}")
    else:
        print(f"Failed to download: {pdf_url}")

# Start the scraping from the base URL
scrape_page_for_links(BASE_URL)
