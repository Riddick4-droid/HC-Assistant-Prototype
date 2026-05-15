from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama


import json
import os
from dotenv import load_dotenv

from ..config import settings  
from ..agents.state import AgentState, Plan 
from ..logger import get_logger  
from ..agents.system_prompt import get_sys_prompt_for_planner 

logger = get_logger(__name__)

load_dotenv()

class PlannerAgent:
    """
    Decomposes a user query into subqueries and decides which collections to search.
    Uses DeepSeek via HuggingFace (or OpenAI).
    """
    def __init__(self):
        global logger
        if settings.ollama_model:
            self.llm = ChatOllama(
            model = settings.ollama_model,
            base_url = settings.ollama_base_url,
            temperature = 0
            )
        #else:
            #self.llm = ChatOpenAI(model="gpt-3.5-turbo",temperature=0)
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
            logger.error(f'Planner error: {e}\n Response: {response.content}')  
            return [{"query":user_query,"collections":[settings.collection_gale, settings.collection_dailymed, settings.collection_pubmed], "priority": 1}]  
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