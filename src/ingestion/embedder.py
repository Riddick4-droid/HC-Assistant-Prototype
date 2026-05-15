from sentence_transformers import SentenceTransformer
import numpy as np
# FIX: Using relative imports for consistency
from ..logger import get_logger  # ✅ FIXED: Using relative imports
from typing import List,Dict,Any

logger = get_logger(__name__)

class MedicalEmbedder:
    def  __init__(self,model_name:str):
        global logger
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_embedding_dimension()
        logger.info(f"[Embedder] Loaded {model_name} (dim={self.dim})")

    def embed_texts(self,texts:List[str])->np.ndarray:
        """Return numpy array of embeddings"""
        if not texts:
            return np.array([])
        logger.info("Embedding texts....")
        return self.model.encode(texts,show_progress_bar=True)
    
    def embed_query(self,query:str)->List[float]:
        logger.info("Embedding query...")
        return self.model.encode([query],show_progress_bar=True)[0].tolist()

