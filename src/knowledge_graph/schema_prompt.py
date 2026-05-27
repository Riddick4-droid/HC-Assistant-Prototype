import os
from src.logger import get_logger

logger = get_logger(__name__)
def get_schema_prompt():
    prompt = """
Extract medical entities and relationships from the following text. Return ONLY valid JSON, no explanations, no markdown formatting.

Entity types: {', '.join([f"{k}: {v}" for k, v in ENTITY_TYPES.items()])}
Relationship types: {', '.join([f"{k}: {v}" for k, v in RELATIONSHIP_TYPES.items()])}

Output JSON format:
{{"nodes": [{{"id": "entity_name", "type": "DRUG/DISEASE/SYMPTOM/etc", "properties": {{"name": "entity_name", "source": "document source"}}}}], "relationships": [{{"source": "entity_id", "target": "entity_id", "type": "TREATS/CAUSES/etc", "properties": {{"evidence": "quote from text"}}}}]}}

Text chunk: {chunk_text}
Source: {chunk_metadata}

JSON:
"""
    return prompt

if __name__ == "__main__":
    get_schema_prompt()
    logger.info("Shema prompt created successfully!")