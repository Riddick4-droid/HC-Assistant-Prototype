from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_openai import ChatOpenAI
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
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.2
        )
        self.system_prompt = """You are a medical reasoning engine. You are given a user query and a set of retrieved text chunks from medical knowledge bases. Your task is to reason step by step, citing evidence from the chunks, and produce a final reasoned analysis that answers the query.

Guidelines:
- Only use information present in the provided chunks.
- If information is missing, state that explicitly.
- Be cautious and avoid over‑confidence.
- Number your reasoning steps.
- At the end, provide a concise conclusion.

Output format:
Steps:
1. ...
2. ...
Conclusion: ..."""
    
    def reason(self, query: str, chunks: list) -> str:
        context = "\n\n".join([f"[{i+1}] {chunk['text']}" for i, chunk in enumerate(chunks)])
        user_prompt = f"User query: {query}\n\nRetrieved context:\n{context}\n\nPlease reason step by step."
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = self.llm.invoke(messages)
        return response.content
    
    def __call__(self, state: AgentState) -> dict:
        reasoning = self.reason(state["user_query"], state["retrieved_chunks"])
        steps = [line for line in reasoning.split("\n") if line.strip().startswith(("1.", "2.", "3.", "4.", "5."))]
        return {"reasoned_evidence": reasoning, "reasoning_steps": steps}


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