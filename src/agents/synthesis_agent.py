import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import settings
from src.agents.state import AgentState
from src.logger import get_logger
from src.agents.system_prompt import get_sys_prompt_for_synthesis

from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

class SynthesisAgent:
    """
    Generates a final, user‑friendly answer with citations, using either OpenAI or DeepSeek.
    """
    def __init__(self):
        #use_openai = os.getenv('SYNTHESIS_MODEL','openai').lower() == 'openai'
        #if use_openai and os.getenv('OPENAI_API_KEY'):
            #self.llm = ChatOpenAI(model=os.getenv('OPENAI_MODEL','gpt-4o'),temperature=0.2)
        if settings.ollama_model:
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(
            model = settings.ollama_model,
            base_url = settings.ollama_base_url,
            temperature = 0.3
            )
        else:
            raise RuntimeError('No LLM available for synthesis')
    def synthesize(self,query:str, reasoned_evidence:str, chunks:list)->tuple[str,list]:
        citations = []
        for idx, chunk in enumerate(chunks[:5]):
            meta = chunk.get('metadata',{})
            citation = {
                "id":idx+1,
                "text_snippet":chunk["text"][:150] + '...',
                "source":meta.get("source","No grounding source"),
                "collection":meta.get("collection","unnkown collection"),
                "page": meta.get("page")
            }
            citations.append(citation)
        sys_prompt = get_sys_prompt_for_synthesis()
        user_prompt = f"""User query: {query}

                     Reasoned evidence:
                    {reasoned_evidence}

                     Available chunks with citations:
                    {chr(10).join([f"[{c['id']}] {c['text_snippet']}" for c in citations])}

            Now produce the final answer with appropriate citations."""
        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = self.llm.invoke(messages)
        return response.content, citations
    def __call__(self, state: AgentState)->dict:
        answer, citations = self.synthesize(
            state["user_query"],
            state["reasoned_evidence"],
            state["retrieved_chunks"]
        )
        return {"final_answer": answer, "citations":citations}
    

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

        
