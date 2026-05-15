from typing import List, Dict, Any, Optional
from ..storage.vector_stores import VectorStoreManager  
from ..knowledge_graph.graph_store import Neo4jMedicalGraph  
from ..ingestion.embedder import MedicalEmbedder  
from ..config import settings  
from ..logger import get_logger  

logger = get_logger(__name__)

class HybridMedicalRetriever:
    """
    Combines vector search (semantic similarity) with graph traversal
    (relationship reasoning) for enriched retrieval.
    """
    def __init__(self):
        global logger

        self.embedder = MedicalEmbedder(settings.embedding_model)
        self.vector_store = VectorStoreManager(
            persist_dir=settings.chroma_persist_dir,
            embedder = self.embedder
        )
        self.graph_store = Neo4jMedicalGraph()

    def retrieve(self,query:str, k:int=5,use_graph:bool=True)->Dict[str,Any]:
        """
        Retrieve relevant context using hybrid approach.
        Returns: {"chunks": [...], "graph_context": "...", "citations": [...]}
        """
        #vector search for semantically similar chunks
        vector_results = self._vector_search(query,k)

        #extract entities from query and search graph
        graph_context = ""
        if use_graph:
            graph_context = self._graph_search(query,vector_results)
        #combine the results
        return{
            "chunks":vector_results,
            "graph_context":graph_context,
            "citations":self._build_citations(vector_results)
        }
    def _vector_search(self,query:str,k:int)->List[Dict]:
         """Search across all medical collections."""
         all_results = []
         collections = [settings.collection_dailymed,settings.collection_gale,settings.collection_pubmed]
         for coll in collections:
             results = self.vector_store.search(coll,query,k=k//3)
             for r in results:
                 r["metadata"]["collection"] = coll
             all_results.extend(results)
         seen = set()
         unique = []
         for r in sorted(all_results, key=lambda x :x["distance"]):
             if r["text"] not in seen:
                 seen.add(r["text"])
                 unique.append(r)
         return unique[:k]
    def _graph_search(self,query:str, vector_results:List[Dict])->str:
        """Extract entities from query and vector results, then traverse graph"""
        try:
            #simple keyword extraction (can be enhanced with LLM)
            keywords = query.lower().split()

            #search graph for matching entities
            context_lines = []

            for keyword in keywords[:5]: #limited for performance, it is possible to get all keywords
                entities = self.graph_store.search_entities(keyword,limit=3)
                for entity in entities:
                    #get 1-hop relationships
                    rels = self.graph_store.query_relationship(entity["id"],depth=1)
                    if rels:
                        context_lines.append(f"\n### {entity['type']}: {entity['id']}")
                        for rel in rels:
                            context_lines.append(f"- {rel['source']} [{rel['rel_type']}] -> {rel['target']}")

            if not context_lines:
                return "[INFO] No relevant graph relationships found"
            return "\n".join(context_lines)
        except Exception as e:
            logger.warning(f"Graph search unavailable: {e}. proceeding with vector only")
            return ""
    
    def _build_citations(self,chunks:List[Dict])->List[Dict]:
        citations = []
        for i, chunk in enumerate(chunks[:5]):
            meta = chunk.get('metadata',{})
            citations.append({
                "id": i +1,
                "text_snippet": chunk["text"][:200],
                "source": meta.get("source", meta.get("collection","unknown")),
                "score": 1- chunk.get("distance",1)
            })
        return citations 
        