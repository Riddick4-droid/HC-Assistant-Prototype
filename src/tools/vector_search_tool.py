from langchain.tools import tool
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from src.storage.vector_stores import VectorStoreManager
from src.ingestion.embedder import MedicalEmbedder
from src.config import settings
from src.logger import get_logger

logger  = get_logger(__name__)

_store_manager = None
_embedder = None

def get_store():
    global _store_manager, _embedder, logger
    if _store_manager is None:
        _embedder = MedicalEmbedder(settings.embedding_model)
        _store_manager = VectorStoreManager(
            persist_dir=str(settings.chroma_persist_dir),
            embedder=_embedder
        )
    logger.info("store manager created")
    return _store_manager

@tool
def search_collection(query: str, collection_name:str, k:int=5)->List[Dict[str,Any]]:
    """
    Search a specific vector collection and return top k results.
    Collections: 'gale_encyclopedia', 'daily_med', 'pubmed_central'
    """
    store = get_store()
    results = store.search(collection_name=collection_name,query=query,k=k)

    for r in results:
        r['metadatas']['collection'] = collection_name
    return results

tools = [
    search_collection,
]

def get_tools_for_collections(collections: List[str])->List:
    """Return a list of tools bound to specific collections"""
    from functools import partial
    bound_tools = []
    for coll in collections:
        tool_func = partial(search_collection,collection_name=coll)
        tool_func.__name__ = f"search_{coll}"
        tool_func.__doc__ = f"search the {coll} collection for medical information"
        bound_tools.append(tool_func)
    return bound_tools

if __name__ == "__main__":
    get_store()
    logger.info('Store created successfully!')