from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from src.agents.graph_builder import build_medical_graph
from src.agents.state import create_initial_state

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

#post request
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

if __name__ == "__main__":
    uvicorn.run('src.api.main:app', host="0.0.0.0", port=8000, reload=True)