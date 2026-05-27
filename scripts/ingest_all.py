##the ingestion pipeline includes the 

import sys
import io
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.ingestion.pipeline import IngestionPipeline
from src.config import settings
from src.logger import get_logger

logger = get_logger(__name__)

def main():
    global logger
    pipeline = IngestionPipeline()

    raw_dir = settings.data_raw_dir

    for pdf_path in raw_dir.glob("*.pdf"):
        if "gale" in pdf_path.name.lower():
            source = "gale"
        elif "dailymed" in pdf_path.name.lower():
            source="dailymed"
        else:
            source="pubmed"
        
        logger.info(f"\nIngesting {pdf_path.name} as source={source}")
        pipeline.ingest_file(pdf_path,source)
    logger.info("\nIngestion complete. You can now query via agent")

if __name__ == "__main__":
    main()