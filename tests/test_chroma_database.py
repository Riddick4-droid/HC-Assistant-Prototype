from src.storage.vector_stores import VectorStoreManager
from src.ingestion.embedder import MedicalEmbedder
from src.config import settings

embedder = MedicalEmbedder(settings.embedding_model)
store = VectorStoreManager(str(settings.chroma_persist_dir), embedder)

collections = [
    settings.collection_gale,
    settings.collection_dailymed,
    settings.collection_pubmed
]

for coll in collections:
    try:
        col = store.get_collection(coll)
        count = col.count()
        print(f"✅ {coll}: {count} chunks")
    except Exception as e:
        print(f"❌ {coll}: error - {e}")