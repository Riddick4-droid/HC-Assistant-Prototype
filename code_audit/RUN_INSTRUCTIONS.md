# How to Run After Fixes

All critical and high-priority bugs have been fixed. Here's how to run your app:

---

## Prerequisites

You need these services running before starting the app:

### 1. **Ollama** (for LLM inference)
```bash
# Install Ollama from https://ollama.ai
# Pull a model
ollama pull mistral

# In a separate terminal, run Ollama server
ollama serve
# Should output: Listening on 127.0.0.1:11434
```

**OR if you have OpenAI tokens:**
```bash
# Set in .env:
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
SYNTHESIS_MODEL=openai
```

### 2. **Neo4j** (for knowledge graph)
```bash
# Using Docker (recommended)
docker run --name neo4j \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_secure_password \
  neo4j:latest

# OR run Neo4j locally if already installed
# Make sure it's running on bolt://localhost:7687
```

### 3. **Create .env file**
```bash
# Create file: .env in project root
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# OR use OpenAI (if you have tokens):
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o
# SYNTHESIS_MODEL=openai

# Vector Database
CHROMA_PERSIST_DIR=./data/chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Neo4j - UPDATE WITH YOUR ACTUAL PASSWORD
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password  # Changed from hardcoded "password123"
NEO4J_DATABASE=neo4j  # Changed from hardcoded UUID

# Collections
COLLECTION_GALE=gale_encyclopedia
COLLECTION_DAILYMED=daily_med
COLLECTION_PUBMED=pubmed_central

# Data
DATA_RAW_DIR=./data/raw
```

---

## Installation

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Download embedding model
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
# This will download and cache the model (~100MB)
```

---

## Running the App

### Option 1: Run as Python module (RECOMMENDED - works with new import fixes)
```bash
cd HC-Assistant-Prototype
python -m src.api.main
```

This is the best way because:
- ✅ Works with relative imports (new fixes)
- ✅ Works in Docker
- ✅ Works in CI/CD pipelines
- ✅ Works with installed packages

### Option 2: Run with Uvicorn
```bash
cd HC-Assistant-Prototype
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Run directly (requires PYTHONPATH)
```bash
cd HC-Assistant-Prototype
export PYTHONPATH=$PYTHONPATH:$(pwd)
python src/api/main.py
```

---

## Testing the API

Once running, test the chat endpoint:

### Using curl
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the side effects of ibuprofen?",
    "session_id": "test-session-1"
  }'
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "query": "What are the side effects of ibuprofen?",
        "session_id": "test-session-1"
    }
)

print(response.json())
```

### Check health endpoint
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", "graph_ready": true}
```

---

## First Time Ingestion

If you need to ingest medical documents:

```python
from src.ingestion.pipeline import IngestionPipeline
from pathlib import Path

pipeline = IngestionPipeline()

# Ingest from a directory
docs_dir = Path("./data/raw")
pipeline.ingest_directory(docs_dir, source="gale")  # gale|dailymed|pubmed
```

---

## Startup Sequence

When you start the app, it will:

1. ✅ Load configuration from `.env`
2. ✅ Set up logging to `logs/app.log`
3. ✅ Initialize embedder (downloads model if needed)
4. ✅ Connect to Chroma vector database
5. ✅ Connect to Neo4j knowledge graph
6. ✅ Initialize all agents (Planner, Reasoner, Synthesis)
7. ✅ Build the LangGraph workflow
8. ✅ Start FastAPI server on port 8000

**If any of these fail:**
- Check `.env` file has required variables
- Verify Ollama is running on port 11434
- Verify Neo4j is running on port 7687
- Check `logs/app.log` for detailed errors

---

## Troubleshooting

### ImportError: No module named 'src'
**Solution:** Run with module flag:
```bash
python -m src.api.main  # ✅ This will work
# NOT: python src/api/main.py
```

### ConnectionRefusedError: Neo4j connection failed
**Solution:** Start Neo4j:
```bash
docker run --name neo4j -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
```

### ConnectionRefusedError: Ollama connection failed
**Solution:** Start Ollama:
```bash
ollama serve
```

### Extraction error: Extraction error: [Errno 2] No such file or directory
**Solution:** Create data directory:
```bash
mkdir -p data/raw data/chroma_db
```

### Neo4j auth error
**Solution:** Update Neo4j password in .env to match Docker startup:
```bash
# If you started with:
docker run -e NEO4J_AUTH=neo4j/my_password neo4j:latest

# Then in .env:
NEO4J_PASSWORD=my_password
```

---

## What's Different After Fixes

### Before (Broken):
```python
# ❌ Imports would fail in Docker/CI/CD
sys.path.append(...)
from src.module import ...

# ❌ Only 1 citation returned
return citations  # inside loop

# ❌ Data corruption
unique.extend(chunk)

# ❌ Password in code
NEO4J_PASSWORD=password123
```

### After (Fixed):
```python
# ✅ Works everywhere (Docker, CI/CD, production)
from ..module import ...

# ✅ All citations returned
for chunk in chunks:
    ...
return citations  # outside loop

# ✅ Proper data handling
unique.append(chunk)

# ✅ Security: password from env
NEO4J_PASSWORD=your_env_var
```

---

## Performance Notes

### First run:
- **Slow:** Embedding model downloads (~100MB)
- **Slow:** LLM models download (Ollama ~5-10GB depending on model)
- **Time:** ~5-10 minutes total for first setup

### Subsequent runs:
- **Fast:** Models are cached locally
- **Time:** Server starts in ~5 seconds

### Chroma database:
- Persists to `data/chroma_db/`
- Survives app restarts
- Data accumulates (good for production)

---

## Logging

App logs go to:
- **Console:** INFO level (see real-time events)
- **File:** `logs/app.log` (DEBUG level, detailed)
- **Errors:** `logs/error.log` (ERROR level only)

View logs:
```bash
# Watch real-time
tail -f logs/app.log

# See errors only
grep ERROR logs/app.log

# Full debug output
grep "src.agents" logs/app.log
```

---

## Docker Support

Now that imports are fixed, you can easily containerize:

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# ✅ This now works with the fixed relative imports
CMD ["python", "-m", "src.api.main"]
```

Build and run:
```bash
docker build -t hc-assistant .
docker run -p 8000:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  hc-assistant
```

---

## Next Steps After Getting Running

1. **Test with curl/Postman** - Verify chat endpoint works
2. **Ingest sample documents** - Load medical data into Chroma
3. **Check logs** - Ensure no warnings/errors
4. **Monitor performance** - Time to first response
5. **Add to production** - Now safe to deploy with fixed imports

---

## Success Checklist

- [ ] `.env` file created with your values
- [ ] Ollama running (`ollama serve`)
- [ ] Neo4j running (Docker or local)
- [ ] `pip install -r requirements.txt` completed
- [ ] `python -m src.api.main` starts without errors
- [ ] `/health` endpoint returns `{"status": "healthy"}`
- [ ] `/chat` endpoint accepts POST requests
- [ ] Responses include citations
- [ ] No ImportError messages
- [ ] Logs show normal startup sequence

**✅ All checks passing = Ready to use!**
