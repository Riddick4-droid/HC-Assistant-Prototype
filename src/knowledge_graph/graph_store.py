from neo4j import GraphDatabase
from typing import List, Dict, Any
from ..config import settings  
from ..logger import get_logger  
from ..knowledge_graph.schema import CONSTRAINT_QUERIES  

logger = get_logger(__name__)

class Neo4jMedicalGraph:
    """Handles storage and retrieval of medical knowledge graph."""
    def __init__(self):

        global logger

        #initializing graph database
        self.driver = GraphDatabase.driver(
            uri =  settings.neo4j_uri,
            auth = (settings.neo4j_user,settings.neo4j_password)
        )
        self.__init__constraints()
    
    def __init__constraints(self):
        """Create uniqueness contraints if not exists"""
        with self.driver.session() as session:
            for query in CONSTRAINT_QUERIES:
                try:
                    session.run(query)
                except Exception as e:
                    logger.info(f"constaints already exists or error: {e}")
    def close(self):
        self.driver.close()
    def add_node(self,node_id:str,node_type:str, properties:Dict):
        """Add or merge a node into the graph"""
        with self.driver.session() as session:
            session.run(
                f"Merge (n:`{node_type}` {{id:$id}})"
                "SET n += $props",
                id = node_id,props=properties
            )
    def add_relationship(self,source_id:str, target_id:str,rel_type:str,properties:Dict=None):
        """Create a relationship between two nodes"""
        with self.driver.session() as session:
            session.run(
                f"MATCH (a {{id: $source}}), (b {{id: $target}}) "
                f"MERGE (a)-[r:`{rel_type}`]->(b) "
                "SET r += $props",
                source=source_id, target=target_id, props=properties or {}
            )
    def ingest_entities(self,extraction:Dict):
        """Bulk insert nodes and relationships from extraction output"""
        for node in extraction.get("nodes",[]):
            self.add_node(node["id"],node["node_type"],node.get("properties",{}))
        for rel in extraction.get("relationships",[]):
    
            self.add_relationship(rel["source"],rel["target"],rel["type"],rel.get("properties"))  

    def search_entities(self,query_text:str, limit:int=10)->List[Dict]:
        """Search for entities by name or properties (full-text index)"""
        with self.driver.session() as session:
            result = session.run(
                "CALL db.index.fulltext.queryNodes('entity_search', $query) "
                "YIELD node, score "
                "RETURN node.id AS id, labels(node)[0] AS type, properties(node) AS props, score "
                "ORDER BY score DESC LIMIT $limit",
                query=query_text,limit=limit
            )
            return [dict(record) for record in result]
    def query_relationship(self, entity_id:str,relationship_type:str=None, depth:int=1)->List[Dict]:
        """Traverse graph to find connected entities"""
        with self.driver.session() as session:
            rel_filter = f":{relationship_type}" if relationship_type else ""
            query =  f"""
                MATCH path = (a {{id: $entity_id}})-[r{rel_filter}*1..{depth}]-(b)
                RETURN a.id AS source, type(r[0]) AS rel_type, b.id AS target, r[0].evidence AS evidence
                LIMIT 50
            """
            result = session.run(query=query, entity_id=entity_id, depth=depth)  
            return [dict(record) for record in result]
