import os
from pathlib import Path
from pydantic_settings import BaseSettings
from src.logger import get_logger

logger = get_logger(__name__)

class Settings(BaseSettings):
    vision_agent_api_key = os.getenv('VISION_AGENT_API_KEY','N/A')

    data_raw_dir: Path = Path(os.getenv("DATA_RAW_DIR","C:\\Users\\LENOVO\\Desktop\\healthcare-assistant-prototype\\HC-Assistant-Prototype\\data\\raw"))
    chroma_persist_dir: Path = Path(os.getenv("CHROMA_PERSIST_DIR","C:\\Users\\LENOVO\\Desktop\\healthcare-assistant-prototype\\HC-Assistant-Prototype\\data\\chroma_db"))

    collection_gale: str = os.getenv("COLLECTION_GALE","gale_encyclopedia")
    collection_dailymed: str = os.getenv("COLLECTION_DAILYMED","daily_med")
    collection_pubmed: str = os.getenv("COLLECTION_PUBMED","pubmed_central")

    embedding_model:str = os.getenv("EMBEDDING_MODEL","sentence-transformers/all-MiniLM-L6-v2")

    class config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

if __name__ == "__main__":
    logger.info(f'Settings class created successfully!!')