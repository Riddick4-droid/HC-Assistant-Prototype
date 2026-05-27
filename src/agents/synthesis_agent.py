import os


from langchain_openai import ChatOpenAI
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_core.messages import SystemMessage, HumanMessage
from ..config import settings 
from ..agents.state import AgentState  
from ..logger import get_logger  
from ..agents.system_prompt import get_sys_prompt_for_synthesis  

from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

class SynthesisAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3
        )
    
    def synthesize(self, query: str, reasoned_evidence: str, chunks: list) -> tuple[str, list]:
        citations = []
        for idx, chunk in enumerate(chunks[:5]):
            meta = chunk.get("metadata", {})
            citation = {
                "id": idx + 1,
                "text_snippet": chunk["text"][:150] + "...",
                "source": meta.get("source", "Unknown"),
                "collection": meta.get("collection", "Unknown"),
                "page": meta.get("page")
            }
            citations.append(citation)
        
        system_prompt = """You are a medical AI assistant. Based on the reasoned evidence and the retrieved chunks, provide a clear, accurate, and safe answer to the user's query. Include citations in the format [1], [2] etc. If the information is insufficient, say so. Never invent information. End with a disclaimer: 'Always consult a healthcare professional for medical advice.'"""
        
        user_prompt = f"""User query: {query}

Reasoned evidence:
{reasoned_evidence}

Available chunks with citations:
{chr(10).join([f"[{c['id']}] {c['text_snippet']}" for c in citations])}

Now produce the final answer with appropriate citations."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = self.llm.invoke(messages)
        return response.content, citations
    
    def __call__(self, state: AgentState) -> dict:
        answer, citations = self.synthesize(
            state["user_query"],
            state["reasoned_evidence"],
            state["retrieved_chunks"]
        )
        return {"final_answer": answer, "citations": citations}
    

#standalone testing
if __name__ == "__main__":
    test_state = {
        "user_query": "Is ibuprofen safe for children?",
        "reasoned_evidence": "The retrieved chunks indicate that ibuprofen can be used in children over 6 months for fever and pain, but dosage depends on weight.",
        "retrieved_chunks": [
            {"text": "Ibuprofen dosing for children: 5-10 mg/kg every 6-8 hours.", "metadata": {"source": "DailyMed"}},
            {"text": "Avoid in children with dehydration or asthma.", "metadata": {"source": "Gale Encyclopedia"}}
        ]
    }
    agent = SynthesisAgent()
    result = agent(test_state)
    logger.info("Final answer:\n", result["final_answer"])
    logger.info("\nCitations:\n", result["citations"])

        
