from langgraph.graph import (StateGraph, 
                             END, 
                             START)
from src.agents.state import AgentState
from src.agents.planner_agent import PlannerAgent
from src.agents.synthesis_agent import SynthesisAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.logger import get_logger

logger = get_logger(__name__)

def build_medical_graph():
    workflow = StateGraph(AgentState)

    #intializing agents
    planner = PlannerAgent()
    synthesizer = SynthesisAgent()
    reasoner = ReasoningAgent()
    retriever = RetrievalAgent()

    #setup the graph nodes
    workflow.add_node("planner",planner)
    workflow.add_node("retriever",retriever)
    workflow.add_node("reasoner",reasoner)
    workflow.add_node("synthesizer",synthesizer)

    #set entry point
    workflow.set_entry_point("planner")

    #define edges for flow
    workflow.add_edge("planner","retriever")
    workflow.add_edge("retriever","reasoner")
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
