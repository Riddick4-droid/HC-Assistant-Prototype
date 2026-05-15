
import os
from pathlib import Path
from typing import List,Dict, Any

from ..tools.vector_search_tool import search_collection  
from ..agents.state import AgentState  
from ..logger import get_logger  

logger = get_logger(__name__)

class RetrievalAgent:
    """
    Executes the plan: for each subquery and each collection, run a vector search.
    Aggregates results, removes duplicates (by text), and scores.
    """
    def __init__(self,k_per_search:int=5):
        global logger
        self.k = k_per_search

    def retrieve(self,plan:Dict, state:AgentState)->List[Dict[str,Any]]:
        all_chunks = []
        query = plan['query']
        for coll in plan['collections']:
            try:
                chunks = search_collection.invoke({"query": query, "collection_name": coll, "k": self.k})
                all_chunks.extend(chunks)
            except Exception as e:
                logger.info(f"retrieval error for {coll}: {e}")
        seen_docs = set()
        unique = []
        for chunk in all_chunks:
            text = chunk["text"]
            if text not in seen_docs:
                seen_docs.add(text)
                unique.append(chunk)
        unique.sort(key=lambda x: x['distance'],reverse=False)
        return unique[:self.k*2] #keep top 2xk after deduplication
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
                unique.append(chunk) 
        unique.sort(key=lambda x : x['distance'],reverse=False)
        unique = unique[:10]
        return {'retrieved_chunks':unique}
    
if __name__ == "__main__":
    from src.agents.state import create_initial_state
    from src.logger import get_logger
    logger = get_logger(__name__)
    state = create_initial_state("headache treatment")
    state["plans"] = [{'"query": "headache treatment", "collections": ["gale_encyclopedia", "daily_med"], "priority": 1'}]
    agent = RetrievalAgent()
    new_state = agent(state)
    logger.info(f"retrieved {len(new_state['retrieved_chunks'])} chunks")
    for i, chunk in enumerate(new_state['retrieved_chunks'][:2]):
        logger.info(f"Chunk {i}: {chunk['text'][:100]}...")



