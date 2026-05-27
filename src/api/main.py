# src/api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from datetime import datetime
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..agents.graph_builder import build_medical_graph
from ..agents.state import create_initial_state
from ..memory.session_memory import memory

app = FastAPI(title="Healthcare Assistant Prototype API", version="1.0.0")

# CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load graph once
graph = build_medical_graph()

# Request/Response models
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class CitationResponse(BaseModel):
    id: int
    text_snippet: str
    source: str
    collection: str
    page: Optional[int] = None

class ChatResponse(BaseModel):
    answer: str
    citations: List[CitationResponse]
    safety_alert: bool = False
    safety_message: Optional[str] = None
    session_id: str

class HistoryResponse(BaseModel):
    session_id: str
    history: List[dict]

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or f"session_{int(datetime.now().timestamp())}"
    history = memory.get_history(session_id)
    state = create_initial_state(request.query, session_id, history)
    try:
        result = graph.invoke(state)
        memory.add_message(session_id, "user", request.query)
        memory.add_message(session_id, "assistant", result["final_answer"])
        citations = [
            CitationResponse(
                id=c["id"],
                text_snippet=c["text_snippet"],
                source=c["source"],
                collection=c.get("collection", "Unknown"),
                page=c.get("page")
            )
            for c in result.get("citations", [])
        ]
        return ChatResponse(
            answer=result["final_answer"],
            citations=citations,
            safety_alert=result.get("safety_alert", False),
            safety_message=result.get("safety_message"),
            session_id=session_id
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    """Retrieve conversation history for a session."""
    return HistoryResponse(
        session_id=session_id,
        history=memory.get_history(session_id)
    )

@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear conversation history for a session."""
    memory.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}

@app.get("/health")
async def health():
    return {"status": "healthy", "graph_ready": graph is not None}

# this is where I static frontend
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Frontend not found. Please add src/api/static/index.html</h1>")

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)