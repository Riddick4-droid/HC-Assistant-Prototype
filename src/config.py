# src/config.py
import os
from pathlib import Path
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # LandingAI
    vision_agent_api_key: str = Field(default="", alias="VISION_AGENT_API_KEY")
    
    # Data paths
    data_raw_dir: Path = Field(default=Path("./data/raw"), alias="DATA_RAW_DIR")
    chroma_persist_dir: Path = Field(default=Path("./data/chroma_db"), alias="CHROMA_PERSIST_DIR")
    
    # Chroma collections
    collection_gale: str = Field(default="gale_encyclopedia", alias="COLLECTION_GALE")
    collection_dailymed: str = Field(default="daily_med", alias="COLLECTION_DAILYMED")
    collection_pubmed: str = Field(default="pubmed_central", alias="COLLECTION_PUBMED")
    
    # Embedding
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL"
    )
    
    # LLM – Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: Optional[str] = Field(default=None, alias="OLLAMA_MODEL")
    
    # LLM – OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    
    # Synthesis model choice
    synthesis_model: Literal["openai", "deepseek"] = Field(default="openai", alias="SYNTHESIS_MODEL")
    
    # DeepSeek via HuggingFace
    deepseek_model_id: Optional[str] = Field(default=None, alias="DEEPSEEK_MODEL_ID")
    
    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="password123", alias="NEO4J_PASSWORD")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
def ensure_directories():
    dirs = [
        settings.data_raw_dir,
        settings.chroma_persist_dir,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

ensure_directories()

if __name__ == "__main__":
    print("=== Configuration ===")
    for key, value in settings.model_dump().items():
        print(f"{key}: {value}")