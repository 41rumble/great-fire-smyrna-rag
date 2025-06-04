import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def setup_neo4j_constraints():
    """Set up Neo4j database constraints and indexes for Graphiti"""
    
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME") 
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    with driver.session(database=database) as session:
        # Create constraints for unique entities
        constraints = [
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT episode_id IF NOT EXISTS FOR (ep:Episode) REQUIRE ep.id IS UNIQUE",
        ]
        
        for constraint in constraints:
            try:
                session.run(constraint)
                print(f"Created constraint: {constraint}")
            except Exception as e:
                print(f"Constraint may already exist: {e}")
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX episode_timestamp IF NOT EXISTS FOR (ep:Episode) ON (ep.timestamp)",
        ]
        
        for index in indexes:
            try:
                session.run(index)
                print(f"Created index: {index}")
            except Exception as e:
                print(f"Index may already exist: {e}")
    
    driver.close()
    print("Neo4j setup complete!")

if __name__ == "__main__":
    setup_neo4j_constraints()