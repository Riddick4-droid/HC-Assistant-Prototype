from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_core.messages import SystemMessage, HumanMessage
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import sys
import os
from dotenv import load_dotenv
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from src.config import settings
from src.agents.state import AgentState
from src.agents.system_prompt import get_sys_prompt_for_reasoning
from src.logger import get_logger

logger = get_logger()

class ReasoningAgent:
    """
    Uses DeepSeek (or fallback) to perform step‑by‑step reasoning over retrieved chunks.
    Outputs reasoned evidence that will be used by the synthesis agent.
    """
    def __init__(self):
        if os.getenv('DEEPSEEK_MODEL_ID'):
            model_id = settings.deepseek_model_id if hasattr(settings,'deepseek_model_id') else "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForCausalLM.from_pretrained(model_id,
                                                         device_map="auto",
                                                         torch_dtype="auto")
            pipe = pipeline("text-generation",
                            model=model, 
                            tokenizer=tokenizer, 
                            max_new_tokens=102)
            self.llm = ChatHuggingFace(llm=HuggingFacePipeline(pipeline=pipe))
        else:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(model='gpt-4o',temperature=0.2)
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