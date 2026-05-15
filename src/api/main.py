from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import Optional, List, Dict, Any
import uvicorn

# FIX: Removed sys.path manipulation and using relative imports
# import sys
# from pathlib import Path
# sys.path.append(str(Path(__file__).parent.parent))  # ❌ OLD: Fragile import path manipulation
from ..agents.graph_builder import build_medical_graph  # ✅ FIXED: Using relative imports
from ..agents.state import create_initial_state  # ✅ FIXED: Using relative imports

app = FastAPI(title='Heathcare Assistant API', version="1.0.0")




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

graph = build_medical_graph()

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class CitationResponse(BaseModel):
    id:int
    text_snippet:str
    source:str
    collection:str
    page: Optional[int]=None

class ChatResponse(BaseModel):
    answer:str
    citations: List[CitationResponse]
    safety_alert: bool =True
    safety_message: Optional[str]=None
    session_id: Optional[str]=None

#post request or endpint
@app.post('/chat', response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        state = create_initial_state(request.query, request.session_id)
        result= graph.invoke(state)

        citations = [
            CitationResponse(
                id = c["id"],
                text_snippet=c["text_snippet"],
                source=c["source"],
                collection=c["collection"],
                page = c.get("page")
            )
            for c in result.get("citations",[])
        ]
        return ChatResponse(
            answer=result["final_answer"],
            citations=citations,
            safety_alert=result.get("safety_alert",False),
            safety_message=result.get("safety_message"),
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get('/health')
async def health():
    return {'status':'healthy', 'graph_ready':graph is not None}

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Frontend not found. Please add static/index.html</h1>")

if __name__ == "__main__":
    uvicorn.run('src.api.main:app', host="0.0.0.0", port=8000, reload=True)