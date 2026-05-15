from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_core.messages import SystemMessage, HumanMessage
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

import os
from dotenv import load_dotenv

from ..config import settings  
from ..agents.state import AgentState  
from ..agents.system_prompt import get_sys_prompt_for_reasoning  
from ..logger import get_logger  

logger = get_logger(__name__)

class ReasoningAgent:
    """
    Uses DeepSeek (or fallback) to perform step‑by‑step reasoning over retrieved chunks.
    Outputs reasoned evidence that will be used by the synthesis agent.
    """
    def __init__(self):
        if settings.ollama_model:
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(
            model = settings.ollama_model,
            base_url = settings.ollama_base_url,
            temperature = 0
            )
        #else:
            #from langchain_openai import ChatOpenAI
            #self.llm = ChatOpenAI(model="gpt-3.5-turbo",temperature=0)

        self.sys_prompt = get_sys_prompt_for_reasoning()

    def reason(self,query:str, chunks:list)->str:
        context = "\n\n".join([f"[{i+1}] {chunk['text']}" for i, chunk in enumerate(chunks)])
        user_prompt = f"user query: {query}\n\nRetrived context:\n{context}\n\nPlease reason step by step"
        messages = [
            SystemMessage(content=self.sys_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = self.llm.invoke(messages)
        return response.content
    
    def __call__(self, state: AgentState)->dict:
        reasoning = self.reason(state['user_query'], state['retrieved_chunks'])
        steps = [line for line in reasoning.split("\n") if line.strip().startswith(("1.", "2.", "3.", "4.", "5."))]
        return {'reasoned_evidence':reasoning, 'reasoning_steps':steps}


# Standalone test (requires retrieved_chunks)
if __name__ == "__main__":
    from src.agents.state import create_initial_state
    from src.logger import get_logger

    logger = get_logger(__name__)

    test_state = create_initial_state("What is the maximum dose of paracetamol?")
    test_state["retrieved_chunks"] = [
        {"text": "Paracetamol maximum daily dose for adults is 4000 mg.", "metadata": {}},
        {"text": "Overdose can cause liver damage.", "metadata": {}}
    ]
    agent = ReasoningAgent()
    result = agent(test_state)
    logger.info("Reasoning output:\n", result["reasoned_evidence"][:500])