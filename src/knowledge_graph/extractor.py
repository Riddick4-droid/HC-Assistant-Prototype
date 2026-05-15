import json
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage,HumanMessage
from ..config import settings  
from ..logger import get_logger  
from ..knowledge_graph.schema import ENTITY_TYPES,RELATIONSHIP_TYPES  
from ..knowledge_graph.schema_prompt import get_schema_prompt  

logger = get_logger(__name__)

class MedicalEntityExtractor:
    """Extracts medical entities and relationships from text chunks
    using OpenAI GPT-4o. Outputs triples ready for Neo4j ingestion.
    """
    def __init__(self):
        global logger
        
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0 #this is intentionally set to deterministic for high-level extraction
        )
    
    def extract_from_chunk(self,chunk_text:str,chunk_metadata:Dict)->Dict:
        """Extract nodes and relationships from a text chunk.
        Returns: {"nodes": [...], "relationships": [...]}
        """
        schema_prompt = get_schema_prompt()
        response = self.llm.invoke(
            [SystemMessage(content="You are a medical information extraction system"),
             HumanMessage(content=schema_prompt)]
        )
        try:
            content = response.content.strip() 
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                return json.loads(content)
        except Exception as e:
            logger.error(f"Extraction error: {e}")  
            return {"nodes": [], "relationships": []}
    