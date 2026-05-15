from langgraph.graph import (StateGraph, 
                             END, 
                             START)
# FIX: Using relative imports
from ..agents.state import AgentState  
from ..agents.planner_agent import PlannerAgent  
from ..agents.synthesis_agent import SynthesisAgent  
from ..agents.reasoning_agent import ReasoningAgent 
from ..agents.retrieval_agent import RetrievalAgent  
from ..storage.hybrid_retriever import HybridMedicalRetriever  
from ..agents.graph_query_agent import GraphQueryAgent 
from ..logger import get_logger  

logger = get_logger(__name__)

def enhanced_retrieve_node(state:AgentState)->dict:
    retriever = HybridMedicalRetriever()
    result  = retriever.retrieve(state["user_query"], k=5, use_graph=True)
    return {
        "retrieved_chunks": result["chunks"],
        "graph_context": result["graph_context"],
        "citations":result["citations"]  
    }


def build_medical_graph():
    workflow = StateGraph(AgentState)

    #intializing agents
    planner = PlannerAgent()
    synthesizer = SynthesisAgent()
    reasoner = ReasoningAgent()


    #setup the graph nodes
    workflow.add_node("planner",planner)
    workflow.add_node("retrieve",enhanced_retrieve_node)
    workflow.add_node("reasoner",reasoner)
    workflow.add_node("synthesizer",synthesizer)

    #set entry point
    workflow.set_entry_point("planner")

    #define edges for flow
    workflow.add_edge("planner","retrieve")
    workflow.add_edge("retrieve","reasoner")
    workflow.add_edge("reasoner","synthesizer")
    workflow.add_edge("synthesizer",END)

    return workflow.compile()


#standalone testing
if __name__ == "__main__":
    graph = build_medical_graph()
    initial_state = {
        "user_query": "What are the side effects of ibuprofen and is it safe during pregnancy?",
        "session_id": "test",
        "plans": [],
        "retrieved_chunks": [],
        "reasoning_steps": [],
        "reasoned_evidence": "",
        "final_answer": None,
        "citations": [],
        "error": None,
        "next_node": None,
        "messages": []
    }
    result = graph.invoke(initial_state)
    logger.info("final answer:", result["final_answer"][:500])
    logger.info("\nCitations:", result["citations"])
