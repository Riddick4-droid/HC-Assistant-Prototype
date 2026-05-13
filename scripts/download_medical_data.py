import urllib.request
from pathlib import Path
import sys
import os


sys.path.append(str(Path(__file__).parent.parent))
from src.config import settings
from src.logger import get_logger

logger = get_logger(__name__)

# List of open‑access medical PDFs from PubMed Central (real examples)
# These are small, safe, and publicly available
PMC_SAMPLES = {
    "gale_like": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7717717/pdf/main.pdf",   # COVID-19 article
    "dailymed_like": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7124014/pdf/main.pdf", # Vitamin D
    "pubmed_central": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8136423/pdf/main.pdf", # Long COVID
}

def download_file(url:str, dest:Path):
    global logger
    logger.info(f"Downloading {dest.name}...")
    urllib.request.urlretrieve(url,dest)
    logger.info(f"Saved to {dest}")

def main():
    #create raw data dir
    global logger 
    settings.data_raw_dir.mkdir(parents=True,exist_ok=True)

    for source, url in  PMC_SAMPLES.items():
        dest = settings.data_raw_dir/ f"{source}.pdf"
        download_file(url,dest)
    logger.info(f"\n Sample medical PDFs downloaded to: {settings.data_raw_dir}")
    logger.info(f"now run: python scripts/ingest_all.py")

if __name__ == "__main__":
    main()