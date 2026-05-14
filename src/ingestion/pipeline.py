from pathlib import Path
from typing import Dict, Any
from src.config import settings
from src.ingestion.landingai_parser import ADEParser
from src.ingestion.embedder import MedicalEmbedder
from src.storage.vector_stores import VectorStoreManager
from src.logger import get_logger

logger = get_logger(__name__)

class IngestionPipeline:
    """
    Multi-source ingestion pipeline using LandingAI ADE.
    Routes documents to appropriate Chroma collections based on source.
    """
    SOURCE_TO_COLLECTION =  {
        "gale": settings.collection_gale,
        "dailymed": settings.collection_dailymed,
        "pubmed": settings.collection_pubmed
    }

    def __init__(self):
        global logger
        self.parser = ADEParser()
        self.embedder = MedicalEmbedder(settings.embedding_model)
        self.store = VectorStoreManager(persist_dir=str(settings.chroma_persist_dir),
                                        embedder=self.embedder)
        
    def ingest_file(self,file_path: Path, 
                    source: str, 
                    extra_metadata:Dict=None):
        """
        Ingest a single file.
        source: 'gale', 'dailymed', or 'pubmed'
        """
        if source not in self.SOURCE_TO_COLLECTION:
            raise ValueError(f"Unknown source: {source}. Kindly use the following: {list(self.SOURCE_TO_COLLECTION.keys())}")
        
        collection_name = self.SOURCE_TO_COLLECTION[source]

        chunks = self.parser.parse_document(file_path)
        if not chunks:
            logger.info(f'No chunks extracted  from {file_path.name}')
            return 0
        source_metadata = {"source": source, "original_file":file_path.name}
        
        if extra_metadata:
            source_metadata.update(extra_metadata)
        
        self.store.add_chunks(collection_name,chunks,source_metadata)
        logger.info(f'Added chunks to store: {len(chunks)}')
        return len(chunks)
    
    def ingest_directory(self,directory: Path, source: str, file_extensions=[".pdf",".jpg",".png"]):
        """Ingest all files in a directory with given extensions."""
        total = 0
        for ext in file_extensions:
            for f in directory.glob(f"*{ext}"):
                total += self.ingest_file(f,source)
        logger.info(f"Ingested {total} chunks from {directory} into {source}")
        return total