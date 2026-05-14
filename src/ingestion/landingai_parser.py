from pathlib import Path
from typing import List, Dict, Any
from landingai_ade import LandingAIADE
from src.config import settings
from src.logger import get_logger
import os
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)

class ADEParser:
    def __init__(self):
        self.client = LandingAIADE(apikey=settings.vision_agent_api_key)

    def parse_document(self,file_path:Path)->List[Dict[str,Any]]:
        """
        Parse a document using ADE, return list of chunks with metadata.
        Each chunk includes:
        - text (markdown content)
        - type ('text', 'table', 'figure')
        - page number (if available)
        - bounding_box (if available)
        """
        global logger
        logger.info(f"Parsing: {file_path.name}")
        response = self.client.parse(
            document = file_path,
            model = "dpt-2-latest",
            split="page"
        )

        chunks = []

        for chunk in response.chunks:
            bbox = None

            if chunk.grounding:
                if hasattr(chunk.grounding,'bbox'):
                    bbox = str(chunk.grounding.bbox)
                elif hasattr(chunk.grounding,'box'):
                    bbox = str(chunk.grounding.box)
            chunks.append({
                "text":chunk.markdown,
                "type":chunk.type,
                "page":chunk.grounding.page if chunk.grounding else None,
                "bbox": bbox,
            })
        logger.info(f"Extracted {len(chunks)} chunks")
        return chunks
