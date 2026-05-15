# Critical Fixes - Implementation Guide

## 1. FIX: Retrieval Agent Logic Error

### Location
`src/agents/retrieval_agent.py` - Lines 68-75

### Current Code (BROKEN)
```python
def __call__(self, state:AgentState)->dict:
    all_chunks = []
    for plan in state['plans']:
        chunks = self.retrieve(plan,state)
        all_chunks.extend(chunks)

    seen_docs = set()
    unique = []

    for chunk in all_chunks:
        text = chunk['text']
        if text not in seen_docs:
            seen_docs.add(text)
            unique.extend(chunk)  # ❌ BUG: extends dict keys, not appending chunk
    unique.sort(key=lambda x : x['distance'],reverse=False)
    unique = unique[:10]
    return {'retrieved_chunks':unique}
```

### Fixed Code
```python
def __call__(self, state:AgentState)->dict:
    all_chunks = []
    for plan in state['plans']:
        chunks = self.retrieve(plan,state)
        all_chunks.extend(chunks)

    seen_docs = set()
    unique = []

    for chunk in all_chunks:
        text = chunk['text']
        if text not in seen_docs:
            seen_docs.add(text)
            unique.append(chunk)  # ✅ FIXED: append chunk dict
    unique.sort(key=lambda x : x['distance'],reverse=False)
    unique = unique[:10]
    return {'retrieved_chunks':unique}
```

### Why It Breaks
- `extend()` unpacks dictionary keys: `{"text": "...", "metadata": {...}}` becomes `["text", "metadata"]`
- Results in corrupted data structure
- Causes KeyError when accessing `x['distance']` in sort

---

## 2. FIX: Neo4j Parameter Order Error

### Location
`src/knowledge_graph/graph_store.py` - Line 52

### Current Code (BROKEN)
```python
def ingest_entities(self, extraction: Dict):
    """Bulk insert nodes and relationships from extraction output"""
    for node in extraction.get("nodes", []):
        self.add_node(node["id"], node["node_type"], node.get("properties", {}))
    for rel in extraction.get("relationships", []):
        self.add_relationship(
            rel["source"],
            rel["type"],  # ❌ BUG: 3rd param is target_id, not rel_type!
            rel.get("properties")
        )
```

### Function Signature
```python
def add_relationship(self, source_id: str, target_id: str, rel_type: str, properties: Dict = None):
```

### Fixed Code
```python
def ingest_entities(self, extraction: Dict):
    """Bulk insert nodes and relationships from extraction output"""
    for node in extraction.get("nodes", []):
        self.add_node(node["id"], node["node_type"], node.get("properties", {}))
    for rel in extraction.get("relationships", []):
        self.add_relationship(
            source_id=rel["source"],
            target_id=rel["target"],  # ✅ FIXED: Added missing target
            rel_type=rel["type"],      # ✅ FIXED: Moved to correct position
            properties=rel.get("properties")
        )
```

### Why It Breaks
- `rel["type"]` (string) passed as `target_id` (should be node ID)
- Cypher query: `MATCH (a {id: $source}), (b {id: $target})` will fail when `$target` is "TREATS" instead of node ID

---

## 3. FIX: Entity Extractor Method Typo

### Location
`src/knowledge_graph/extractor.py` - Line 29

### Current Code (BROKEN)
```python
def extract_from_chunk(self, chunk_text: str, chunk_metadata: Dict) -> Dict:
    """Extract nodes and relationships from a text chunk."""
    schema_prompt = get_schema_prompt()
    response = self.llm.invoke(
        [SystemMessage(content="You are a medical information extraction system"),
         HumanMessage(content=schema_prompt)]
    )
    try:
        content = response.content.strip() 
        if content.starstwith("```json"):  # ❌ TYPO!
            content = content[7:]
        if content.endswith("```"):
            return json.loads(content)
    except Exception as e:
        logger.info(f"Extraction error: {e}")
        return {"nodes": [], "relationships": []}
```

### Fixed Code
```python
def extract_from_chunk(self, chunk_text: str, chunk_metadata: Dict) -> Dict:
    """Extract nodes and relationships from a text chunk."""
    schema_prompt = get_schema_prompt()
    response = self.llm.invoke(
        [SystemMessage(content="You are a medical information extraction system"),
         HumanMessage(content=schema_prompt)]
    )
    try:
        content = response.content.strip() 
        if content.startswith("```json"):  # ✅ FIXED: startswith
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]  # ✅ Also remove trailing ```
        return json.loads(content)
    except Exception as e:
        logger.error(f"Extraction error: {e}")  # ✅ Use logger.error
        return {"nodes": [], "relationships": []}
```

### Why It Breaks
- `AttributeError: 'str' object has no attribute 'starstwith'`
- Stops entity extraction completely
- Returns empty results even if valid data

---

## 4. FIX: Return Inside Loop

### Location
`src/storage/hybrid_retriever.py` - Lines 65-73

### Current Code (BROKEN)
```python
def _build_citations(self, chunks: List[Dict]) -> List[Dict]:
    citations = []
    for i, chunk in enumerate(chunks[:5]):
        meta = chunk.get('metadata', {})
        citation = {
            "id": i + 1,
            "text_snippet": chunk["text"][:200],
            "source": meta.get("source", meta.get("collection", "unkown")),
            "score": 1 - chunk.get("distance", 1)
        }
        citations.append(citation)
        return citations  # ❌ BUG: Returns after first iteration!
```

### Fixed Code
```python
def _build_citations(self, chunks: List[Dict]) -> List[Dict]:
    citations = []
    for i, chunk in enumerate(chunks[:5]):
        meta = chunk.get('metadata', {})
        citation = {
            "id": i + 1,
            "text_snippet": chunk["text"][:200],
            "source": meta.get("source", meta.get("collection", "unknown")),  # Fixed typo
            "score": 1 - chunk.get("distance", 1)
        }
        citations.append(citation)
    return citations  # ✅ FIXED: Return after loop completes
```

### Why It Breaks
- Only 1 citation created instead of up to 5
- User sees incomplete source attribution
- Loop counter never reaches i=1, so citation ID is always 1

---

## 5. FIX: Metadata Key Inconsistency

### Location: Multiple files

### Current Code (INCONSISTENT)

**Vector Stores** (`src/storage/vector_stores.py` - Line 80):
```python
return [{"text": d, "metadatas": m, "distance": dist} for d, m, dist in ...]
                       ^^^^^^^^^ plural
```

**Hybrid Retriever** (`src/storage/hybrid_retriever.py` - Line 40):
```python
meta = chunk.get('metadata', {})  # singular
```

**Synthesis Agent** (`src/agents/synthesis_agent.py` - Line 22):
```python
meta = chunk.get('metadata', {})  # singular
```

### Fixed Code: Standardize on singular "metadata"

**In vector_stores.py** - Change line 80:
```python
# FROM:
return [{"text": d, "metadatas": m, "distance": dist} for d, m, dist in zip(docs, metas, dists)]

# TO:
return [{"text": d, "metadata": m, "distance": dist} for d, m, dist in zip(docs, metas, dists)]
```

**Add a comment in vector_stores.py**:
```python
def search(self, collection_name: str, query: str, k: int = 5):
    """Search within a single collection.
    
    Returns: List[Dict] with keys: text, metadata, distance
    """
```

---

## 6. FIX: Thread-Unsafe Global Singleton

### Location
`src/tools/vector_search_tool.py` - Lines 10-24

### Current Code (BROKEN)
```python
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
```

### Fixed Code: Initialize once at startup

**In src/api/main.py**, add initialization:
```python
from fastapi import FastAPI
from src.ingestion.embedder import MedicalEmbedder
from src.storage.vector_stores import VectorStoreManager
from src.config import settings
from src.logger import get_logger

app = FastAPI(title='Healthcare Assistant API', version="1.0.0")
logger = get_logger(__name__)

# Initialize stores at startup (thread-safe)
@app.on_event("startup")
async def startup_event():
    global store_manager, embedder
    embedder = MedicalEmbedder(settings.embedding_model)
    store_manager = VectorStoreManager(
        persist_dir=str(settings.chroma_persist_dir),
        embedder=embedder
    )
    logger.info("Store manager initialized at startup")

# Make available to tools
def get_initialized_store():
    if store_manager is None:
        raise RuntimeError("Store manager not initialized. Check startup.")
    return store_manager
```

**In src/tools/vector_search_tool.py**:
```python
@tool
def search_collection(query: str, collection_name: str, k: int = 5) -> List[Dict[str, Any]]:
    """Search a specific vector collection and return top k results."""
    from src.api.main import get_initialized_store
    store = get_initialized_store()
    results = store.search(collection_name=collection_name, query=query, k=k)
    for r in results:
        r['metadata']['collection'] = collection_name
    return results
```

### Why It Breaks
- Multiple threads call `get_store()` simultaneously
- Race condition creates multiple VectorStoreManager instances
- Memory leak (multiple Chroma clients)
- Inconsistent embedding dimensions

---

## 7. FIX: Import Path Issues

### Location: Multiple files

### Current Code (FRAGILE)
```python
# src/api/main.py, line 9
sys.path.append(str(Path(__file__).parent.parent))
from src.agents.graph_builder import build_medical_graph
```

### Fixed Code: Use relative imports

**Option A: Relative imports (RECOMMENDED)**
```python
# src/api/main.py
from ..agents.graph_builder import build_medical_graph
from ..agents.state import create_initial_state
from ..logger import get_logger
```

**Option B: Proper package structure**
- Ensure `__init__.py` exists in all directories
- Run with: `python -m src.api.main` or `python -m uvicorn src.api.main:app`

**Option C: Environment setup**
```bash
# In Docker or CI/CD
export PYTHONPATH="${PYTHONPATH}:/path/to/project"
python src/api/main.py
```

### Files to update:
- `src/api/main.py` - Line 9-10
- `src/agents/planner_agent.py` - Line 7-8
- `src/agents/retrieval_agent.py` - Line 5-6
- `src/agents/reasoning_agent.py` - Line 6-7
- `src/tools/vector_search_tool.py` - Line 6-7

---

## 8. FIX: Neo4j Query Parameter Issues

### Location
`src/knowledge_graph/graph_store.py` - Line 72

### Current Code (POTENTIALLY BROKEN)
```python
def query_relationship(self, entity_id: str, relationship_type: str = None, depth: int = 1) -> List[Dict]:
    """Traverse graph to find connected entities"""
    with self.driver.session() as session:
        rel_filter = f":{relationship_type}" if relationship_type else ""
        query = f"""
            MATCH path = (a {{id: $entity}})-[r{rel_filter}*1..{depth}]-(b)
            RETURN a.id AS source, type(r[0]) AS rel_type, b.id AS target, r[0].evidence AS evidence
            LIMIT 50
        """
        result = session.run(query=query, entity=entity_id, depth=depth)
        return [dict(record) for record in result]
```

### Fixed Code
```python
def query_relationship(self, entity_id: str, relationship_type: str = None, depth: int = 1) -> List[Dict]:
    """Traverse graph to find connected entities"""
    with self.driver.session() as session:
        rel_filter = f":{relationship_type}" if relationship_type else ""
        query = f"""
            MATCH path = (a {{id: $entity_id}})-[r{rel_filter}*1..{depth}]-(b)
            RETURN a.id AS source, type(r[0]) AS rel_type, b.id AS target, r[0].evidence AS evidence
            LIMIT 50
        """
        # ✅ FIXED: Use entity_id parameter name consistently
        result = session.run(query=query, entity_id=entity_id, depth=depth)
        return [dict(record) for record in result]
```

Also fix the Cypher query string injection issue - use parameterization:
```python
def query_relationship(self, entity_id: str, relationship_type: str = None, depth: int = 1) -> List[Dict]:
    """Traverse graph to find connected entities"""
    with self.driver.session() as session:
        # Safely handle depth parameter
        depth = min(depth, 5)  # Limit depth for performance
        
        rel_type_clause = f":{relationship_type}" if relationship_type else ""
        query = f"""
            MATCH path = (a {{id: $entity_id}})-[r{rel_type_clause}*1..{depth}]-(b)
            RETURN a.id AS source, type(r[0]) AS rel_type, b.id AS target, r[0].evidence AS evidence
            LIMIT 50
        """
        result = session.run(query, entity_id=entity_id)
        return [dict(record) for record in result]
```

---

## 9. FIX: Logger Method Call Issues

### Location
`src/agents/graph_builder.py` - Line 60

### Current Code (BROKEN)
```python
logger.info("final answer:", result["final_answer"][:500])
logger.info("\nCitations:", result["citations"])
```

### Fixed Code
```python
logger.info(f"final answer: {result['final_answer'][:500]}")
logger.info(f"Citations: {result['citations']}")
```

### All Instances to Fix:

**File: src/agents/planner_agent.py**
```python
# Line 40 - FROM:
logger.info(f'Planner error: {e}\n Response: {response.content}')
# TO:
logger.error(f'Planner error: {e}\nResponse: {response.content}')

# Line 51 - FROM:
logger.info("plans: ")
# TO:
logger.debug("Generated plans:")
```

**File: src/knowledge_graph/extractor.py**
```python
# Line 34 - FROM:
logger.info(f"Extraction error: {e}")
# TO:
logger.error(f"Extraction error: {e}")
```

**File: src/storage/vector_stores.py**
```python
# Line 70 - FROM:
logger.info('Searching database...')
# TO:
logger.debug('Searching vector database for query')
```

---

## 10. FIX: Missing Response Validation

### Location
`src/agents/synthesis_agent.py` - Line 52

### Current Code (FRAGILE)
```python
def __call__(self, state: AgentState) -> dict:
    answer, citations = self.synthesize(
        state["user_query"],
        state["reasoned_evidence"],
        state["retrieved_chunks"]
    )
    return {"final_answer": answer, "citations": citations}
```

### Fixed Code
```python
def __call__(self, state: AgentState) -> dict:
    try:
        if not state.get("retrieved_chunks"):
            logger.warning("No retrieved chunks available for synthesis")
            return {
                "final_answer": "I don't have enough information to answer this question.",
                "citations": []
            }
        
        answer, citations = self.synthesize(
            state["user_query"],
            state["reasoned_evidence"],
            state["retrieved_chunks"]
        )
        
        if not answer or not answer.strip():
            logger.error("LLM returned empty answer")
            raise ValueError("LLM synthesis failed")
            
        return {"final_answer": answer, "citations": citations}
    except Exception as e:
        logger.error(f"Synthesis agent failed: {e}")
        raise
```

---

## Priority Implementation Order

1. **Immediately** (Blocks execution):
   - Fix #3: `starstwith` → `startswith`
   - Fix #1: `unique.extend(chunk)` → `unique.append(chunk)`
   - Fix #2: Neo4j parameter order

2. **Before Testing** (Causes silent failures):
   - Fix #4: Return inside loop
   - Fix #5: Metadata key consistency

3. **Before Production** (Causes crashes):
   - Fix #6: Thread-unsafe singleton
   - Fix #7: Import paths
   - Fix #9: Logger calls

4. **Code Quality** (Prevents future bugs):
   - Fix #8: Query parameters
   - Fix #10: Response validation
