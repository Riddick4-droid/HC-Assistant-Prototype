import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.ingestion.pipeline import IngestionPipeline
from src.config import settings
from src.logger import get_logger

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
    logger("\nIngestion complete. You can now query via agent")

if __name__ == "__main__":
    main()