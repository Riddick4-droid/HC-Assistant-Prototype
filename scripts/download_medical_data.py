#note that:  you need actual pdf links to download the data from the sources
#this demonstrates how to perform the data extraction from the sources
#check the settings module if you want to modify the destination of files stored.

import urllib.request
from pathlib import Path
import sys
import os
import requests


sys.path.append(str(Path(__file__).parent.parent))
from src.config import settings
from src.logger import get_logger

logger = get_logger(__name__)

# List of open‑access medical PDFs from PubMed Central (real examples)
# These are small, safe, and publicly available
PDF_SOURCES = {
    "gale_like": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    "dailymed_like": "https://www.africau.edu/images/default/sample.pdf",
    "pubmed_central": "https://arxiv.org/pdf/2301.07041.pdf",  # real medical-like paper
}


def download_file(url:str, dest:Path):
    global logger
    logger.info(f"Downloading {dest.name}...")
    try:
        urllib.request.urlretrieve(url,dest)
        with open(dest,'rb') as f:
            header = f.read(5)
            if header != b'%PDF-':
                raise ValueError(f'Downloaded file is not a PDF (header: {header})')
            logger.info(f'Saved and verified: {dest}')
    except Exception as e:
        logger.info(f'Failed: {e}')
        if dest.exists():
            dest.unlink()

def main():
    #create raw data dir
    global logger 
    settings.data_raw_dir.mkdir(parents=True, exist_ok=True)

    for source, url in  PDF_SOURCES.items():
        dest = settings.data_raw_dir/ f"{source}.pdf"
        download_file(url,dest)
    logger.info(f"\n Sample medical PDFs downloaded to: {settings.data_raw_dir}")
    logger.info(f"now run: python scripts/ingest_all.py")

if __name__ == "__main__":
    main()