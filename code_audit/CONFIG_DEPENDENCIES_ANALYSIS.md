# Configuration & Dependencies Consistency Analysis

## Module Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                     API Entry Point                         │
│                    src/api/main.py                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Logger    │  │   Config     │  │GraphBuilder  │
    │logger.py    │  │config.py     │  │graph_builder │
    └─────────────┘  └──────────────┘  └──────────────┘
            ▲              ▲                    │
            │              │                    └─────────┐
            │              │                              ▼
            │              │                    ┌──────────────────┐
            │              │                    │   Agent State    │
            │              │                    │state.py          │
            │              │                    └──────────────────┘
            │              │                              │
            │              │                              ├─┬─┬─┐
            │              │                              │ │ │ ▼
            │              │                    ┌─────────┴─┴─┴─────────┐
            │              │                    │   Agent Instances    │
            │              │    ┌───────────────┤  (Planner, Reasoner  │
            │              │    │               │   Synthesis, etc)    │
            │              │    │               └──────────────────────┘
            │              │    │                        │
            │              │    ▼                        ▼
            │              │  ┌──────────┐   ┌─────────────────────┐
            │              │  │  Neo4j   │   │  HybridRetriever    │
            │              │  │graph_store   │hybrid_retriever.py  │
            │              │  └──────────┘   └─────────┬───────────┘
            │              │                           │
            │              │        ┌──────────────────┼───────────────┐
            │              │        │                  │               │
            │              ▼        ▼                  ▼               ▼
            │       ┌──────────────┐  ┌──────────────────┐  ┌────────────────┐
            │       │  Embedder    │  │ VectorStoreManager│  │ GraphQueryAgent│
            │       │embedder.py   │  │vector_stores.py  │  │graph_query_agent
            │       └──────────────┘  └──────────────────┘  └────────────────┘
            │              ▲                  ▲
            │              │                  │
            └──────────────┴──────────────────┘
```

---

## Configuration Values - Consistency Check

### Settings Object Initialization
**File:** `src/config.py`

| Setting | Default Value | Used In | Status |
|---------|--------------|---------|--------|
| `embedding_model` | `sentence-transformers/all-MiniLM-L6-v2` | `MedicalEmbedder`, `HybridRetriever`, `VectorStoreManager` | ✅ Consistent |
| `ollama_base_url` | `http://localhost:11434` | `PlannerAgent`, `ReasoningAgent`, `SynthesisAgent` | ✅ Consistent |
| `ollama_model` | `None` | All agents check this | ✅ Consistent |
| `collection_gale` | `gale_encyclopedia` | `HybridRetriever`, `IngestionPipeline` | ⚠️ Hardcoded in planner_agent |
| `collection_dailymed` | `daily_med` | `HybridRetriever`, `IngestionPipeline` | ⚠️ Mismatch: `daily_med` vs `dailymed` |
| `collection_pubmed` | `pubmed_central` | `HybridRetriever`, `IngestionPipeline` | ✅ Consistent |
| `chroma_persist_dir` | `./data/chroma_db` | `VectorStoreManager`, `HybridRetriever`, `IngestionPipeline` | ✅ Consistent |
| `neo4j_uri` | `bolt://localhost:7687` | `Neo4jMedicalGraph`, `GraphQueryAgent` | ✅ Consistent |
| `neo4j_user` | `neo4j` | `Neo4jMedicalGraph`, `GraphQueryAgent` | ✅ Consistent |
| `neo4j_password` | `password123` | `Neo4jMedicalGraph`, `GraphQueryAgent` | ❌ Default password! |
| `neo4j_database` | `38f4f491` | `GraphQueryAgent` | ❌ Hardcoded UUID |

---

## Critical Configuration Issues

### Issue 1: Collection Names Hardcoded in Agents
**File:** `src/agents/planner_agent.py` - Line 34
```python
return [{'query':user_query,'collections':["gale_encyclopedia", "daily_med", "pubmed_central"], "priority": 1}]
                                           ^^^^^^^^^^^^^^^^^^^^
```
Should use:
```python
from src.config import settings

collections = [
    settings.collection_gale,
    settings.collection_dailymed,
    settings.collection_pubmed
]
```

---

### Issue 2: Neo4j Database Identifier
**File:** `src/config.py` - Line 42
```python
neo4j_database: str = Field(default="38f4f491", alias="NEO4J_DATABASE")
```

This appears to be a specific database instance ID. **Problems:**
1. UUID format suggests it's database-specific
2. If changed in .env, code may use wrong database
3. Should probably default to `neo4j` (standard)

**Recommendation:**
```python
neo4j_database: str = Field(
    default="neo4j",  # Standard Neo4j default database
    alias="NEO4J_DATABASE"
)
```

---

### Issue 3: Default Password in Config
**File:** `src/config.py` - Line 40
```python
neo4j_password: str = Field(default="password123", alias="NEO4J_PASSWORD")
```
**Problem:** Hardcoded default password in code.  
**Risk:** Code checked into version control with exposed password.

**Recommendation:**
```python
neo4j_password: str = Field(
    default="",  # Empty = required
    alias="NEO4J_PASSWORD"
)

# At startup validation:
if not settings.neo4j_password:
    raise ValueError("NEO4J_PASSWORD environment variable is required")
```

---

## Logger Configuration Consistency

### Current Setup
**File:** `src/logger.py` - Lines 67-85

```python
"loggers": {
    "": {"level": "DEBUG", ...},           # Root logger
    "src.agents": {"level": "DEBUG", ...},
    "src.api": {"level": "INFO", ...},      # ⚠️ Different level
    "src.ingestion": {"level": "DEBUG", ...},
    "src.storage": {"level": "DEBUG", ...},
    "src.tools": {"level": "DEBUG", ...},
}
```

### Issues
1. **Inconsistent levels:** Why is `src.api` at INFO but others at DEBUG?
2. **Module names must match exactly:** Logger names in code must match config keys
3. **Third-party noise:** `langchain` and `chromadb` have separate handling

### Validation Required
Every module should have matching logger name:

```python
# In every module:
from src.logger import get_logger
logger = get_logger(__name__)  # Must be "src.module_name"
```

**Cross-check:**
```
src/agents/planner_agent.py    → get_logger(__name__)    → "src.agents.planner_agent"
                                                          but config has "src.agents" ✅ (parent matches)

src/api/main.py                → get_logger(__name__)    → "src.api.main"
                                                          config has "src.api" ✅ (parent matches)

src/ingestion/pipeline.py      → get_logger(__name__)    → "src.ingestion.pipeline"
                                                          config has "src.ingestion" ✅ (parent matches)
```

**Status:** ✅ Hierarchical logging works (parent loggers inherit child levels)

---

## Import Consistency Audit

### Pattern 1: Absolute imports with sys.path manipulation ❌
```python
# src/api/main.py
sys.path.append(str(Path(__file__).parent.parent))
from src.agents.graph_builder import build_medical_graph
```
**Problem:** Works locally but fails in Docker, CI/CD, installed packages

### Pattern 2: Relative imports (PREFERRED) ✅
```python
# Proposed fix:
from ..agents.graph_builder import build_medical_graph
from ..logger import get_logger
```

### Pattern 3: Config imports - CONSISTENT ✅
```python
# All files use:
from src.config import settings
```
This works because config.py doesn't have sys.path manipulation

---

## Data Type Consistency Issues

### Vector Search Results Structure

**Returns from VectorStoreManager.search()** - `vector_stores.py:76`
```python
{
    "text": str,
    "metadatas": Dict,  # ❌ KEY: "metadatas" (plural)
    "distance": float
}
```

**Consumed by HybridRetriever** - `hybrid_retriever.py:40`
```python
meta = chunk.get('metadata', {})  # ❌ EXPECTS: "metadata" (singular)
```

**Result:** `None` for all metadata lookups → missing source info

### Recommended Standardization

Choose one convention and use everywhere:
```
Option A: "metadata" (singular) - More Pythonic
Option B: "metadatas" (plural) - Matches Chroma API

RECOMMENDATION: Use "metadata" (singular)
- Match common Python convention
- Chroma uses "metadatas" for batch operations,
  but we can map it internally
```

---

## Dependency Version Compatibility

### From requirements.txt

| Package | Version | Known Issues |
|---------|---------|--------------|
| `neo4j` | `>=5.26.0` | ✅ Latest stable |
| `langchain-neo4j` | `>=0.13.0` | ✅ Compatible |
| `chromadb` | (no version spec) | ⚠️ No pinned version |
| `langchain` | (no version spec) | ⚠️ Breaking changes between versions |
| `sentence-transformers` | (no version spec) | ⚠️ API changes in newer versions |
| `torch` | (no version spec) | ⚠️ Size matters (2GB+) |

**Recommendation:** Pin versions in requirements.txt
```txt
neo4j==5.26.0
chromadb==0.5.0
langchain==0.1.20
langchain-neo4j==0.13.0
sentence-transformers==2.2.2
torch==2.0.1
```

---

## Initialization Order Dependencies

### Expected Startup Sequence

```
1. Load environment variables (.env)
   └─> config.py runs on import
       └─> settings = Settings()
           └─> Validates env vars
           └─> Calls ensure_directories()

2. Initialize logging
   └─> logger.py setup_logging()
       └─> Creates log files

3. Initialize agents (in graph_builder.py)
   └─> PlannerAgent()
       └─> Tries to connect to Ollama
           └─> FAILS if Ollama not running
               └─> Falls back to (commented out) OpenAI
                   └─> FAILS if no OPENAI_API_KEY
                       └─> ERROR: No LLM available

   └─> SynthesisAgent()
       └─> Same issue

   └─> ReasoningAgent()
       └─> Same issue

4. Initialize vector store
   └─> HybridRetriever()
       └─> MedicalEmbedder() - needs HuggingFace download
       └─> VectorStoreManager() - needs Chroma connection
       └─> Neo4jMedicalGraph() - FAILS if Neo4j not running

5. Build graph
   └─> workflow.compile()
       └─> All nodes must be ready
```

### Failure Points Without Services
- ❌ No Ollama (port 11434) → Agents crash
- ❌ No OpenAI token → Agents crash (synthesis)
- ❌ No Neo4j (port 7687) → Knowledge graph fails
- ❌ First request hangs if HuggingFace model not cached

### Recommended Startup Validation

**Add to main.py:**
```python
def validate_dependencies():
    """Check critical services are available."""
    import socket
    
    checks = {
        ("127.0.0.1", 11434): "Ollama",
        ("127.0.0.1", 7687): "Neo4j",
    }
    
    missing = []
    for (host, port), service in checks.items():
        try:
            socket.create_connection((host, port), timeout=2)
        except (socket.timeout, ConnectionRefusedError):
            missing.append(service)
    
    if missing:
        logger.warning(f"Missing services: {', '.join(missing)}")
        logger.warning("Using fallback LLM configuration...")
    
    return len(missing) == 0
```

---

## Environment Variable Mapping

### Required Variables
```bash
# .env file

# LLM Configuration (choose one)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral  # or llama2, neural-chat, etc

# OR for OpenAI (commented out - you don't have tokens)
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o
# SYNTHESIS_MODEL=openai

# Vector Database
CHROMA_PERSIST_DIR=./data/chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Knowledge Graph
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-secure-password>  # NOT password123!
NEO4J_DATABASE=neo4j  # Changed from 38f4f491

# Data
DATA_RAW_DIR=./data/raw
COLLECTION_GALE=gale_encyclopedia
COLLECTION_DAILYMED=daily_med
COLLECTION_PUBMED=pubmed_central
```

### Code Validation
```python
# Add to config.py __init__:
def validate_required_settings():
    """Ensure all critical settings are configured."""
    errors = []
    
    if not settings.ollama_model and not settings.openai_api_key:
        errors.append(
            "Must set OLLAMA_MODEL or OPENAI_API_KEY environment variable"
        )
    
    # Verify directories
    try:
        settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        settings.data_raw_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"Cannot create data directories: {e}")
    
    if errors:
        raise ValueError("\n".join(errors))

# Call during startup:
validate_required_settings()
```

---

## Summary of Consistency Issues

| Category | Issue | Impact | Fix |
|----------|-------|--------|-----|
| **Collection Names** | Hardcoded in agents | App breaks if collection names change | Use `settings.collection_*` |
| **Metadata Keys** | "metadata" vs "metadatas" | Missing metadata in results | Standardize to "metadata" |
| **Logger Levels** | Wrong levels used | Poor debugging visibility | Use error/debug/info correctly |
| **Neo4j Config** | Hardcoded database ID | Wrong database used | Use standard default "neo4j" |
| **Passwords** | Hardcoded in config | Security risk | Use env vars, validate required |
| **Import Paths** | sys.path manipulation | Fails in Docker/CI | Use relative imports |
| **Singleton Store** | Global state, not thread-safe | Memory leaks | Initialize at startup |
| **LLM Initialization** | Crashes if service missing | App fails to start | Add graceful fallback validation |
| **Return Statements** | Inside loops | Incomplete results | Move outside loops |
| **Type Mismatches** | Dict unpacking with extend() | Data corruption | Use append() not extend() |
