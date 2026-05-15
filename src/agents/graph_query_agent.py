from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_openai import ChatOpenAI
from ..config import settings  
from ..logger import get_logger 
import os

logger = get_logger(__name__)

class GraphQueryAgent:
    """
    Uses LangChain's GraphCypherQAChain to convert natural language
    to Cypher queries and retrieve structured graph answers.
    """
    def __init__(self):
        self.graph = Neo4jGraph(
            url = settings.neo4j_uri,
            username = settings.neo4j_user,
            password = settings.neo4j_password,
            database = settings.neo4j_database
        )
        self.llm = ChatOpenAI(model=settings.openai_model,temperature=0)
        self.chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph = self.graph,
            verbose = True,
            validate_cypher = True,
            top_k = 10
        )

    def query(self, natural_language_query: str)->str:
        """Ask a question about relationships in the knowledge graph"""
        result = self.chain.invoke({"query": natural_language_query})
        return result.get("result","No information found in knowledge graph")