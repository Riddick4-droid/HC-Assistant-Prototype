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
    "gale_like": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7717717/pdf/medi-99-e22452.pdf",   # COVID-19 article
    "dailymed_like": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7124014/pdf/978-981-13-6689-5_Chapter_8.pdf", # Vitamin D
    "pubmed_central": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8136423/pdf/mm7020e1.pdf", # Long COVID
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
    settings.data_raw_dir.mkdir(parents=True,exist_ok=True)

    for source, url in  PMC_SAMPLES.items():
        dest = settings.data_raw_dir/ f"{source}.pdf"
        download_file(url,dest)
    logger.info(f"\n Sample medical PDFs downloaded to: {settings.data_raw_dir}")
    logger.info(f"now run: python scripts/ingest_all.py")

if __name__ == "__main__":
    main()