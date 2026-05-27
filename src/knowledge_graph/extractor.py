# src/knowledge_graph/extractor.py
import json
import re
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import settings
from src.knowledge_graph.schema import ENTITY_TYPES, RELATIONSHIP_TYPES

import sys

class MedicalEntityExtractor:
    """
    Extracts medical entities and relationships from text chunks using OpenAI.
    Returns: {"nodes": [...], "relationships": [...]}
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0
        )
    
    def extract_from_chunk(self, chunk_text: str, chunk_metadata: Dict) -> Dict:
        import re
        cleaned_text = re.sub(r'<a[^>]+>', '', chunk_text)  # remove <a id=...>
        cleaned_text = re.sub(r'[①-⑩]', '', cleaned_text)   # remove circled numbers
        cleaned_text = re.sub(r'[🔹🔸▪️]', '', cleaned_text) # remove bullets
        schema_prompt = f"""
Extract medical entities and relationships from the following text.

Entity types: {', '.join([f"{k}: {v}" for k, v in ENTITY_TYPES.items()])}
Relationship types: {', '.join([f"{k}: {v}" for k, v in RELATIONSHIP_TYPES.items()])}

Output JSON format:
{{
    "nodes": [
        {{"id": "entity_name", "type": "DRUG/DISEASE/SYMPTOM/etc", "properties": {{"name": "entity_name", "source": "document source"}}}}
    ],
    "relationships": [
        {{"source": "entity_id", "target": "entity_id", "type": "TREATS/CAUSES/etc", "properties": {{"evidence": "quote from text"}}}}
    ]
}}

Text chunk: {chunk_text}
Source: {chunk_metadata}

Return ONLY valid JSON. Do NOT include any extra text before or after the JSON.
"""
        response = self.llm.invoke([
            SystemMessage(content="You are a medical information extraction system. Output only JSON."),
            HumanMessage(content=schema_prompt)
        ])
        
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        # Find the first valid JSON object or array using regex
        match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
        if match:
            content = match.group(1)
        
        # Try to parse JSON
        try:
            data = json.loads(content)
            # Ensure required keys exist
            if "nodes" not in data:
                data["nodes"] = []
            if "relationships" not in data:
                data["relationships"] = []
            return data
        except json.JSONDecodeError as e:
            print(f"Extraction error: {e}\nContent: {content[:200]}...")
            return {"nodes": [], "relationships": []}