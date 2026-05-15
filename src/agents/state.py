from typing import (TypedDict, 
                    List, 
                    Dict, Any, 
                    Optional, 
                    Annotated)
from langgraph.graph.message import add_messages
from ..logger import get_logger  # ✅ FIXED: Using relative imports

logger = get_logger(__name__)

class Plan(TypedDict):
    """a single sub-query plan"""
    query: str
    collections: List[str]
    priority: int

class AgentState(TypedDict):
    user_query:str
    session_id: Optional[str]
    plans: List[Plan]
    retrieved_chunks: List[Dict[str,Any]]
    reasoning_steps: List[str]
    reasoned_evidence: str #final reasoning output
    final_answer: Optional[str]
    citations: List[Dict[str, Any]]
    error: Optional[str]
    next_node: Optional[str]
    messages: Annotated[List[Dict[str,str]],add_messages]
    graph_context: str

def create_initial_state(user_query:str, session_id: Optional[str]=None)->AgentState:
    global logger
    logger.info('Agent state created successfully. Running...')
    return AgentState(
        user_query=user_query,
        session_id=session_id,
        plans=[],
        retrieved_chunks=[],
        reasoning_steps=[],
        reasoned_evidence="",
        final_answer=None,
        citations=[],
        error=None,
        next_node=None,
        messages=[{"role": "user", "content": user_query}],
        graph_context=""
    )