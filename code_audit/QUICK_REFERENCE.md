# Quick Reference - Breaking Points Checklist

## 🔴 CRITICAL BUGS (Fix Immediately - App Won't Work)

- [ ] **retrieval_agent.py:73** - `unique.extend(chunk)` → `unique.append(chunk)`
  - **Error:** TypeError when sorting results
  - **Impact:** Chat endpoint returns corrupted data

- [ ] **extractor.py:29** - `content.starstwith()` → `content.startswith()`
  - **Error:** AttributeError
  - **Impact:** Entity extraction crashes immediately

- [ ] **graph_store.py:52** - Fix Neo4j parameter order in `ingest_entities()`
  - **Error:** Cypher query binding fails
  - **Impact:** Knowledge graph won't ingest any data

- [ ] **hybrid_retriever.py:72** - Move `return citations` outside the loop
  - **Error:** Only 1 citation returned instead of 5
  - **Impact:** Incomplete citations in responses

---

## 🟠 HIGH PRIORITY (Fix Before Testing)

- [ ] **vector_stores.py:80 & all consumers** - Standardize `metadata` vs `metadatas`
  - **Error:** KeyError when accessing metadata
  - **Impact:** Missing source attribution in responses

- [ ] **All files** - Replace `sys.path.append()` with relative imports
  - **Error:** ImportError in production environments
  - **Impact:** App won't run in Docker, CI/CD, or as installed package

- [ ] **vector_search_tool.py** - Fix thread-unsafe global singleton
  - **Error:** Memory leaks and race conditions
  - **Impact:** High resource usage, inconsistent behavior under load

- [ ] **config.py:40, 42** - Remove hardcoded password and database ID
  - **Error:** Wrong database connection
  - **Impact:** App uses wrong Neo4j instance or exposed password in git

---

## 🟡 MEDIUM PRIORITY (Fix Before Production)

- [ ] **All agent files** - Use `logger.error()` instead of `logger.info()` for errors
  - **Impact:** Cannot debug production issues
  
- [ ] **planner_agent.py:34** - Use config values for collection names
  - **Impact:** Collection name changes break agents

- [ ] **All classes** - Add null/empty response validation
  - **Impact:** Silent failures mask bugs

- [ ] **main.py** - Initialize stores at startup, not on-demand
  - **Impact:** First request takes extra time for initialization

---

## File-by-File Fixes Needed

### src/agents/retrieval_agent.py
```
Line 73: extend() → append()
Line 66: Consistent with vector_stores result structure
```

### src/knowledge_graph/extractor.py
```
Line 29: starstwith() → startswith()
Line 34: logger.info() → logger.error()
Line 37: Remove return statement inside loop
```

### src/knowledge_graph/graph_store.py
```
Line 52: Fix parameter order: add target_id
Line 72: Parameter name consistency ($entity vs entity_id)
```

### src/storage/hybrid_retriever.py
```
Line 72: Move return outside loop
Line 40: Use "metadata" not "metadata" consistency check
Line 65: Fix typo "unkown" → "unknown"
```

### src/storage/vector_stores.py
```
Line 80: Change "metadatas" → "metadata" for consistency
```

### src/tools/vector_search_tool.py
```
Line 10-24: Move store initialization to main.py startup
Line 78: Use consistent "metadata" key
```

### src/api/main.py
```
Line 9: Remove sys.path.append()
Add: @app.on_event("startup") to initialize stores
Add: Startup validation function
```

### src/agents/planner_agent.py
```
Line 7: Remove sys.path.append(), use relative imports
Line 34: Use settings for collection names instead of hardcoding
Line 40: Use logger.error() not logger.info()
```

### src/agents/reasoning_agent.py
```
Line 6: Remove sys.path.append(), use relative imports
```

### src/config.py
```
Line 40: Remove hardcoded password, make required
Line 42: Change database ID to standard "neo4j"
Add: validate_required_settings() function
```

---

## Environment Setup Checklist

Before running the app:

- [ ] **Ollama or OpenAI token ready**
  - If Ollama: `ollama pull mistral` and run `ollama serve`
  - If OpenAI: Set `OPENAI_API_KEY` in `.env`

- [ ] **Neo4j running**
  - Docker: `docker run --name neo4j -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest`
  - Change password from `password123` in `.env`

- [ ] **Chroma database**
  - Directory `data/chroma_db/` will be created automatically
  - Ensure `data/` directory is writable

- [ ] **Create .env file**
  ```bash
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=mistral
  CHROMA_PERSIST_DIR=./data/chroma_db
  NEO4J_URI=bolt://localhost:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=your_secure_password
  NEO4J_DATABASE=neo4j
  ```

---

## Testing Checklist After Fixes

1. **Import Test**
   ```bash
   python -m pytest tests/ -v
   ```

2. **Configuration Test**
   ```python
   from src.config import settings
   print(settings.model_dump())  # Verify all settings loaded
   ```

3. **Logger Test**
   ```python
   from src.logger import get_logger
   logger = get_logger(__name__)
   logger.info("Test message")
   ```

4. **Vector Store Test**
   ```python
   from src.storage.vector_stores import VectorStoreManager
   from src.ingestion.embedder import MedicalEmbedder
   # Try to initialize
   ```

5. **Graph Store Test**
   ```python
   from src.knowledge_graph.graph_store import Neo4jMedicalGraph
   graph = Neo4jMedicalGraph()
   # Verify connection
   ```

6. **End-to-End Test**
   ```bash
   python -m src.api.main
   # Test endpoint: curl -X POST http://localhost:8000/chat -d '{"query":"..."}'
   ```

---

## Quick Dependency Check

### Services Required
- ✅ Ollama (port 11434) OR OpenAI API key
- ✅ Neo4j (port 7687)
- ✅ Python 3.9+ with dependencies installed

### Common Startup Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'src'` | Python path issue | Run with `python -m src.api.main` or add to PYTHONPATH |
| `ConnectionRefusedError: [Errno 111] Connection refused` | Ollama/Neo4j not running | Start services: `ollama serve` and Neo4j container |
| `neo4j.exceptions.AuthError: Unauthorized` | Wrong Neo4j password | Update `.env` with correct `NEO4J_PASSWORD` |
| `AttributeError: 'str' object has no attribute 'starstwith'` | Typo in code (not fixed) | Apply critical fix #3 from CRITICAL_FIXES_GUIDE.md |
| `KeyError: 'metadata'` | Using "metadatas" in code | Apply high priority fix: standardize on "metadata" |
| `TypeError: 'dict' object is not iterable` | Using extend() instead of append() | Apply critical fix #1 from CRITICAL_FIXES_GUIDE.md |

---

## Priority Matrix

```
         │ Easy to Fix │ Hard to Fix
─────────┼─────────────┼────────────
High     │   Typos     │ Singleton
Impact   │ Log levels  │ Import paths
         │             │
─────────┼─────────────┼────────────
Low      │  Docstring  │ Refactoring
Impact   │  Comments   │ Full redesign
         │             │
```

**Focus on: High Impact + Easy to Fix first**
1. Typos (5 min) - starstwith, extend vs append
2. Log levels (10 min) - Replace info/debug with error where appropriate
3. Return statements (5 min) - Move outside loops
4. Metadata keys (15 min) - Find and replace
5. Config values (10 min) - Use settings instead of hardcoding

---

## Documentation Files Generated

1. **CODE_AUDIT_REPORT.md** - Comprehensive audit with all issues
2. **CRITICAL_FIXES_GUIDE.md** - Detailed code examples for each fix
3. **CONFIG_DEPENDENCIES_ANALYSIS.md** - Configuration and dependency consistency
4. **This file** - Quick reference checklist

---

## Next Steps

1. **Week 1**: Apply all CRITICAL fixes (4 items, ~1 hour total)
2. **Week 2**: Apply HIGH PRIORITY fixes (5 items, ~2 hours total)  
3. **Week 3**: Apply MEDIUM PRIORITY fixes and add tests (8 items, ~4 hours total)
4. **Week 4**: Performance testing and production readiness

**Estimated Total Time: 7-8 hours of focused development**

---

## Backup Before Making Changes

```bash
# Create a backup branch
git checkout -b backup/pre-audit-fixes
git push origin backup/pre-audit-fixes

# Or zip the directory
zip -r hc-assistant-backup.zip .
```

Then proceed with fixes on a feature branch:
```bash
git checkout -b feat/fix-critical-bugs
# Make changes
git commit -m "Fix: critical bugs from code audit"
git push origin feat/fix-critical-bugs
# Create PR for review
```
