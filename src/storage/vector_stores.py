import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List,Dict,Any,Optional
from src.logger import get_logger
import os
import uuid

logger = get_logger(__name__)

class VectorStoreManager:
    """manages multiple chroma collections(there are several datasources so we need multiple collections)"""

    def __init__(self,persist_dir:str,embedder):
        global logger
        self.client = chromadb.PersistClient(
            path = persist_dir,
            settings = ChromaSettings(anonymized_telemetry=False)
        )
        self.embedder = embedder
        self.collections = {} #caching

    def get_collection(self,name:str):
        """get or create a collection by its name"""
        if name not in self.collections:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space":"cosine"}
            )
        return self.collections[name]
    
    def add_chunks(self,collection_name:str,
                   chunks:List[Dict[str,Any]],
                   source_metadata:Dict = None):
        """
        Add chunks to a specific collection.
        Each chunk dict must have 'text' and optionally 'type', 'page', 'bbox'.
        """
        collection = self.get_collection(collection_name)

        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            documents.append(chunk['text'])

            emb = self.embedder.embed_texts([chunk['text']])[0]
            embeddings.append(emb.tolist())

            meta = {
                "type":chunk.get("type","text"),
                "page": chunk.get("page","N/A"),
                "bbox": chunk.get("bbox")
            }

            if source_metadata:
                meta.update(source_metadata)
            metadatas.append(meta)

        collection.add(
            ids = ids,
            documents = documents,
            embeddings = embeddings,
            metadatas = metadatas
        )
        logger.info(f"[VectorStore] Added {len(ids)} chunks to '{collection_name}'")
        return ids
    
    def search(self,collection_name:str,query:str,k:int=5):
        """search within a single collection"""
        logger.info('Searching database...')
        collection = self.get_collection(collection_name)
        query_emb = self.embedder.embed_query(query) #[query]
        results = collection.query(
            query_embeddings = [query_emb],
            n_results=k,
            include = ["documents","metadatas","distances"]
        )
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        dists = results["distances"][0] if results["distances"] else []
        return [{"text":d, "metadatas":m, "distance":dist} for d,m,dist in zip(docs,metas,dists)]


