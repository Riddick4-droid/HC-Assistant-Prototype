# src/knowledge_graph/schema.py
"""
Medical knowledge graph schema - defines entities and relationships
for consistent extraction and querying.
"""

# Node types (entity labels)
ENTITY_TYPES = {
    "DRUG": "Medication or pharmaceutical compound",
    "DISEASE": "Medical condition or disorder", 
    "SYMPTOM": "Subjective experience reported by patient",
    "TREATMENT": "Therapeutic intervention",
    "SIDE_EFFECT": "Adverse reaction to treatment",
    "GENE": "Genetic entity",
    "PROCEDURE": "Medical procedure or test",
}

# Relationship types
RELATIONSHIP_TYPES = {
    "TREATS": "Drug/treatment treats disease/symptom",
    "CAUSES": "Agent causes disease/symptom/side effect",
    "INTERACTS_WITH": "Drug interacts with another drug",
    "CONTRAINDICATED_FOR": "Drug contraindicated for condition",
    "DOSAGE_RECOMMENDED": "Recommended dosage for condition",
    "SIDE_EFFECT_OF": "Side effect caused by drug/treatment",
    "HAS_SYMPTOM": "Disease has symptom",
}

# Cypher constraint creation (run once)
CONSTRAINT_QUERIES = [
    "CREATE CONSTRAINT drug_id IF NOT EXISTS FOR (n:DRUG) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (n:DISEASE) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT symptom_id IF NOT EXISTS FOR (n:SYMPTOM) REQUIRE n.id IS UNIQUE",
]