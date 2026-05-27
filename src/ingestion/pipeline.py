from pathlib import Path
from typing import Dict, Any

from ..config import settings  
from ..ingestion.landingai_parser import ADEParser  
from ..ingestion.embedder import MedicalEmbedder  
from ..storage.vector_stores import VectorStoreManager  
from ..knowledge_graph.extractor import MedicalEntityExtractor  
from ..knowledge_graph.graph_store import Neo4jMedicalGraph  
from ..logger import get_logger  

logger = get_logger(__name__)

class IngestionPipeline:
    """
    Multi-source ingestion pipeline using LandingAI ADE.
    Routes documents to appropriate Chroma collections based on source.
    """
    #this is where the raw data is and needs to be parsered, embedded and ingested 
    SOURCE_TO_COLLECTION =  {
        "gale": settings.collection_gale,
        "dailymed": settings.collection_dailymed,
        "pubmed": settings.collection_pubmed
    }

    def __init__(self):
        global logger
        self.parser = ADEParser() #initializes the ADE parser-if failure check your quota
        self.embedder = MedicalEmbedder(settings.embedding_model)
        self.store = VectorStoreManager(persist_dir=str(settings.chroma_persist_dir),
                                        embedder=self.embedder)
        self.extractor = MedicalEntityExtractor()
        self.graph_store = Neo4jMedicalGraph()
        
    def ingest_file(self, file_path: Path, source: str, extra_metadata: Dict = None):
        if source not in self.SOURCE_TO_COLLECTION:
            raise ValueError(f"Unknown source: {source}. Use: {list(self.SOURCE_TO_COLLECTION.keys())}")

        collection_name = self.SOURCE_TO_COLLECTION[source]

        chunks = self.parser.parse_document(file_path)
        if not chunks:
            logger.info(f'No chunks extracted from {file_path.name}')
            return 0

        source_metadata = {"source": source, "original_file": file_path.name}
        if extra_metadata:
            source_metadata.update(extra_metadata)

        # Vector store
        self.store.add_chunks(collection_name, chunks, source_metadata)
        logger.info(f'Added chunks to Chroma: {len(chunks)}')

         # Graph extraction
        # if settings.enable_graph_extraction:
        #     for chunk in chunks:
        #         try:
        #             extraction = self.extractor.extract_from_chunk(
        #                 chunk_text=chunk["text"],
        #                 chunk_metadata={"source": file_path.name, "page": chunk.get("page")}
        #             )
        #             if extraction.get("nodes") or extraction.get("relationships"):
        #                 self.graph_store.ingest_entities(extraction)
        #                 logger.debug(f"Added {len(extraction.get('nodes', []))} nodes and "
        #                      f"{len(extraction.get('relationships', []))} relationships from chunk")
        #             else:
        #                 logger.debug("No entities extracted from chunk")
        #         except Exception as e:
        #             logger.error(f"Graph extraction failed for chunk: {e}")

        logger.info(f'Finished ingestion for {file_path.name}')
        return len(chunks)
    
    def ingest_directory(self,directory: Path, source: str, file_extensions=[".pdf",".jpg",".png"]):
        """Ingest all files in a directory with given extensions."""
        total = 0
        for ext in file_extensions:
            for f in directory.glob(f"*{ext}"):
                total += self.ingest_file(f,source)
        logger.info(f"Ingested {total} chunks from {directory} into {source}")
        return total