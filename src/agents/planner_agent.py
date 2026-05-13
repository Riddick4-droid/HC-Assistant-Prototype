from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import sys
from pathlib import Path
import json
import os
from dotenv import load_dotenv
sys.path.append(str(Path(__file__).parent.parent))
from src.config import settings
from src.agents.state import AgentState, Plan
from src.logger import get_logger
from src.agents.system_prompt import get_sys_prompt_for_planner

logger = get_logger(__name__)

load_dotenv()

class PlannerAgent:
    """
    Decomposes a user query into subqueries and decides which collections to search.
    Uses DeepSeek via HuggingFace (or OpenAI).
    """
    def __init__(self):
        global logger
        if os.getenv('DEEPSEEK_MODEL_ID'):
            from transformers import AutoModelForCausalLM,AutoTokenizer,pipeline
            model_id = settings.deepseek_model_id if hasattr(settings,'deepseek_model_id') else "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForCausalLM.from_pretrained(model_id,
                                                         device_map="auto",
                                                         torch_dtype="auto")
            #define the pipeline abstraction
            pipe = pipeline("text-generation",model=model,
                             tokenizer=tokenizer,
                             max_new_tokens=512)
            self.llm = ChatHuggingFace(llm=HuggingFacePipeline(pipeline=pipe))
        else:
            self.llm = ChatOpenAI(model="gpt-3.5-turbo",temperature=0)
        self.system_prompt = get_sys_prompt_for_planner()

    def plan(self,user_query:str)->list[Plan]:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_query)
        ]
        response = self.llm.invoke(messages)
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            plans = json.loads(content)
            for p in plans: #ensures each plan has a required field
                p.setdefault("priority",1)
            return plans
        except Exception as e:
            logger.info(f'Planner error: {e}\n Response: {response.content}')
            return [{'query':user_query,'collections':["gale_encyclopedia", "daily_med", "pubmed_central"], "priority": 1}]
    def __call__(self, state: AgentState)->dict:
        plans = self.plan(state['user_query'])
        return {'plans':plans}
    
#standalone test for debugging before full use
if __name__ == "__main__":
    planner = PlannerAgent()
    query = "What are the symptoms of long covid and are there any treatments?"
    plans = planner.plan(query)
    logger.info("plans: ")
    for p in plans:
        logger.info(f" -{p}")