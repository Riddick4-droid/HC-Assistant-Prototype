# Code Audit Report - Healthcare Assistant Prototype

## Executive Summary
This document identifies **critical breaking points** and **consistency issues** that may cause the application to fail. The analysis focuses on import consistency, logger usage, configuration, data type mismatches, and logical errors.

---

## 🔴 CRITICAL BREAKING POINTS

### 1. **Retrieval Agent - Logic Error (BLOCKER)**
**File:** `src/agents/retrieval_agent.py` - Line ~73
```python
# WRONG - This will fail!
unique.extend(chunk)  # chunk is a dict, not iterable
```
**Issue:** `extend()` unpacks the dictionary keys instead of appending the chunk object.  
**Fix:**
```python
unique.append(chunk)  # Append the chunk dict directly
```
**Impact:** Retrieval will produce corrupted data and crash during citation building.

---

### 2. **Neo4j Graph - Wrong Parameter Order (CRITICAL)**
**File:** `src/knowledge_graph/graph_store.py` - Line ~52
```python
# In ingest_entities() method
self.add_relationship(rel["source"],rel["type"],rel.get("properties"))
                                      ^^^^^^
```
**Issue:** `rel["type"]` passed where `target_id` expected. Function signature is `add_relationship(source_id, target_id, rel_type, properties)`.  
**Fix:**
```python
self.add_relationship(
    source_id=rel["source"],
    target_id=rel["target"],  # Missing this!
    rel_type=rel["type"],
    properties=rel.get("properties")
)
```
**Impact:** All graph relationships will fail to create, breaking knowledge graph completely.

---

### 3. **Knowledge Graph Extractor - Method Typo (BLOCKER)**
**File:** `src/knowledge_graph/extractor.py` - Line ~29
```python
if content.starstwith("```json"):  # TYPO!
    content = content[7:]
```
**Issue:** Method name is `startswith()` not `starstwith()`. This will throw `AttributeError`.  
**Fix:**
```python
if content.startswith("```json"):
    content = content[7:]
```
**Impact:** Entity extraction will crash whenever attempting to parse JSON responses.

---

### 4. **Hybrid Retriever - Return Inside Loop (LOGIC ERROR)**
**File:** `src/storage/hybrid_retriever.py` - Lines ~65-73
```python
def _build_citations(self, chunks: List[Dict]) -> List[Dict]:
    citations = []
    for i, chunk in enumerate(chunks[:5]):
        meta = chunk.get('metadata', {})
        citations.append({...})
        return citations  # ❌ RETURNS ON FIRST ITERATION!
```
**Issue:** Returns after first chunk, so only 1 citation created instead of up to 5.  
**Fix:**
```python
def _build_citations(self, chunks: List[Dict]) -> List[Dict]:
    citations = []
    for i, chunk in enumerate(chunks[:5]):
        meta = chunk.get('metadata', {})
        citations.append({...})
    return citations  # ✅ After loop completes
```
**Impact:** Users will see only 1 citation regardless of how many chunks were retrieved.

---

### 5. **Vector Search Tool - Global State Issue (CONCURRENCY BUG)**
**File:** `src/tools/vector_search_tool.py` - Lines ~10-24
```python
_store_manager = None
_embedder = None

def get_store():
    global _store_manager, _embedder, logger
    if _store_manager is None:
        # ❌ Lazy initialization in global scope
```
**Issue:** Thread-unsafe singleton pattern. Multiple concurrent requests may create multiple instances.  
**Fix:** Initialize in `main.py` during startup, not lazily on demand.
**Impact:** Memory leaks and inconsistent embeddings in production with concurrent users.

---

## 🟠 HIGH PRIORITY ISSUES

### 6. **Metadata Key Inconsistency**
**Files:**
- `src/storage/vector_stores.py` - uses `"metadatas"` (line 76)
- `src/storage/hybrid_retriever.py` - uses `"metadata"` (line 40)
- `src/agents/synthesis_agent.py` - uses `"metadata"` (line 22)

**Issue:** Keys are inconsistent throughout codebase.
```python
# Vector stores returns:
{"text": d, "metadatas": m, "distance": dist}  # ❌ "metadatas"

# But synthesis agent expects:
meta = chunk.get("metadata", {})  # ❌ "metadata"
```
**Fix:** Standardize on `"metadata"` (singular) everywhere.
**Impact:** `None` values returned, missing metadata in citations.

---

### 7. **Import Path Consistency - Fragile sys.path Usage**
**Files affected:**
- `src/api/main.py` - Line 9
- `src/agents/planner_agent.py` - Line 7
- `src/agents/retrieval_agent.py` - Line 5
- `src/tools/vector_search_tool.py` - Line 6

```python
sys.path.append(str(Path(__file__).parent.parent))
from src.agents.graph_builder import build_medical_graph
```

**Issue:** When running from different directories, imports may fail.  
**Fix:** Use relative imports or ensure PYTHONPATH includes project root:
```python
# Option 1: Relative imports (preferred)
from ..agents.graph_builder import build_medical_graph

# Option 2: Use -m flag when running
# python -m src.api.main
```
**Impact:** ImportError when running from non-standard directories (Docker, CI/CD, etc).

---

### 8. **Logger Parameter Mismatch**
**File:** `src/agents/graph_builder.py` - Line ~60
```python
logger.info("final answer:", result["final_answer"][:500])
                                                        ↑
# logger.info() doesn't accept positional args after message
```
**Issue:** Incorrect logging call syntax.  
**Fix:**
```python
logger.info(f"final answer: {result['final_answer'][:500]}")
```
**Impact:** TypeError in test/debug code.

---

### 9. **Neo4j Query Parameter Mismatch**
**File:** `src/knowledge_graph/graph_store.py` - Line ~72
```python
result = session.run(query=query, entity=entity_id, depth=depth)
                                          ↑
# But query uses $entity as placeholder
```
**Issue:** The query uses `$entity` but code should pass as `entity_id`.  
**Fix:**
```python
result = session.run(query=query, entity=entity_id, depth=depth)
# Ensure Cypher query parameterizes correctly
```
**Impact:** Neo4j parameter binding failures.

---

### 10. **Missing Error Handling in Graph Search**
**File:** `src/storage/hybrid_retriever.py` - Lines ~35-50
```python
def _graph_search(self, query: str, vector_results: List[Dict]) -> str:
    try:
        # ...
    except Exception as e:
        logger.warning(f"Graph search unavailable: {e}. proceeding with vector only")
        return ""
```
**Issue:** Returns empty string on ANY error, including connection failures. Silent failure masks problems.  
**Fix:**
```python
except ConnectionError as e:
    logger.error(f"Neo4j connection failed: {e}")
    raise
except Exception as e:
    logger.warning(f"Graph search failed (non-critical): {e}")
    return ""
```
**Impact:** Silent failures make debugging difficult in production.

---

## 🟡 MEDIUM PRIORITY - CONSISTENCY ISSUES

### 11. **Logger Usage Inconsistency**
**Instances of incorrect log levels:**

File: `src/agents/planner_agent.py` - Line ~40
```python
logger.info(f'Planner error: {e}...')  # ❌ Should be logger.error()
```

File: `src/knowledge_graph/extractor.py` - Line ~34
```python
logger.info(f"Extraction error: {e}")  # ❌ Should be logger.error()
```

File: `src/storage/vector_stores.py` - Line ~70
```python
logger.info('Searching database...')  # ✅ OK, but could be DEBUG
```

**Fix:** Use correct log levels:
- `logger.debug()` - debugging info
- `logger.info()` - general info
- `logger.warning()` - unexpected but recoverable
- `logger.error()` - errors
- `logger.critical()` - app-breaking errors

---

### 12. **Configuration Hardcoded Values**
**File:** `src/config.py` - Line ~40
```python
neo4j_database: str = Field(default="38f4f491", alias="NEO4J_DATABASE")
```
**Issue:** UUID-like string is hardcoded. Looks like specific database identifier.  
**Fix:** Make this a required environment variable or use standard database name:
```python
neo4j_database: str = Field(
    default="neo4j",  # Standard default
    alias="NEO4J_DATABASE"
)
```
**Impact:** Wrong database used if not explicitly set in `.env`.

---

### 13. **Missing Null/Empty Checks**
**File:** `src/agents/synthesis_agent.py` - Line ~24
```python
response = self.llm.invoke(messages)
return response.content, citations  # ❌ No check if response has content
```
**Fix:**
```python
if not hasattr(response, 'content') or not response.content:
    raise ValueError("LLM returned empty response")
return response.content, citations
```

---

### 14. **Inconsistent Collection Names**
**Files:** Multiple agent files
```python
# planner_agent.py expects:
"gale_encyclopedia", "daily_med", "pubmed_central"

# config.py defines:
collection_gale = "gale_encyclopedia"
collection_dailymed = "daily_med"  # ❌ "dailymed" vs "daily_med"
collection_pubmed = "pubmed_central"
```
**Issue:** Collection name mapping could break if values don't match.  
**Fix:** Use config settings consistently instead of hardcoding strings.

---

### 15. **Missing Dependencies / Optional Features Not Handled**
**File:** `src/tools/drug_interaction_tool.py` - Empty  
**File:** `src/tools/web_search_tool.py` - Empty  

**Issue:** Files imported/mentioned but not implemented. Code references them but will fail if called.  
**Fix:** Either implement or remove imports. Add feature flags if optional.

---

## 🔵 LOW PRIORITY - CODE QUALITY

### 16. **Global Logger Anti-Pattern**
**Multiple files use:**
```python
global logger
logger = get_logger(__name__)
```
**Issue:** Using `global` for module-level variable is unnecessary.  
**Fix:**
```python
logger = get_logger(__name__)  # Just assign at module level
```

---

### 17. **Missing Type Hints**
**File:** `src/storage/vector_stores.py` - Line ~76
```python
def search(self, collection_name: str, query: str, k: int = 5):
    # ... returns list but no return type hint
```
**Fix:**
```python
def search(self, collection_name: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
```

---

### 18. **Unused Imports**
**File:** `src/agents/reasoning_agent.py`
```python
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline  # Not used
```

---

## 📋 SUMMARY TABLE

| Priority | File | Issue | Impact |
|----------|------|-------|--------|
| 🔴 CRITICAL | `retrieval_agent.py` | `extend()` instead of `append()` | Data corruption |
| 🔴 CRITICAL | `graph_store.py` | Wrong parameter order in `add_relationship()` | Graph ingestion fails |
| 🔴 CRITICAL | `extractor.py` | Typo: `starstwith()` → `startswith()` | Extraction crashes |
| 🔴 CRITICAL | `hybrid_retriever.py` | Return inside loop | Only 1 citation returned |
| 🟠 HIGH | `vector_search_tool.py` | Thread-unsafe singleton | Concurrency bugs |
| 🟠 HIGH | Multiple | Metadata key inconsistency | Missing metadata |
| 🟠 HIGH | Multiple | Fragile `sys.path` usage | Import failures |
| 🟡 MEDIUM | Multiple | Logger level misuse | Poor debugging |
| 🟡 MEDIUM | `config.py` | Hardcoded Neo4j database | Wrong DB selected |

---

## 🛠️ RECOMMENDED ACTIONS

### Immediate (Before Production):
1. ✅ Fix all 4 CRITICAL issues (lines 1-4)
2. ✅ Standardize metadata key across all files
3. ✅ Fix import paths to use project root or relative imports
4. ✅ Replace hardcoded collection names with config values

### Short-term:
5. ✅ Implement proper logging levels
6. ✅ Add null/empty response checks
7. ✅ Fix global logger pattern
8. ✅ Thread-safe store initialization

### Long-term:
9. ✅ Add comprehensive error handling and recovery
10. ✅ Implement config validation on startup
11. ✅ Add unit tests for data transformations
12. ✅ Set up CI/CD to catch these issues

---

## 🧪 TESTING RECOMMENDATIONS

Create test files to verify:
```python
# test_integration.py
def test_retrieval_returns_proper_structure()
def test_graph_relationship_creation()
def test_entity_extraction_parsing()
def test_metadata_consistency()
def test_concurrent_store_access()
```
