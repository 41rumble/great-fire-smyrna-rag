from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def setup_graphiti_database():
    """Set up Neo4j database with required Graphiti indexes and constraints"""
    
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    
    with driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:
        print("🔧 Setting up Graphiti database schema...")
        
        # Create constraints
        constraints = [
            "CREATE CONSTRAINT entity_uuid IF NOT EXISTS FOR (e:Entity) REQUIRE e.uuid IS UNIQUE",
            "CREATE CONSTRAINT episodic_uuid IF NOT EXISTS FOR (e:Episodic) REQUIRE e.uuid IS UNIQUE",
            "CREATE CONSTRAINT community_uuid IF NOT EXISTS FOR (c:Community) REQUIRE c.uuid IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                session.run(constraint)
                print(f"✅ Created constraint: {constraint.split('CREATE CONSTRAINT ')[1].split(' IF')[0]}")
            except Exception as e:
                print(f"⚠️  Constraint may already exist: {constraint.split('CREATE CONSTRAINT ')[1].split(' IF')[0]}")
        
        # Create indexes
        indexes = [
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_group_id IF NOT EXISTS FOR (e:Entity) ON (e.group_id)",
            "CREATE INDEX episodic_valid_at IF NOT EXISTS FOR (e:Episodic) ON (e.valid_at)",
            "CREATE INDEX episodic_group_id IF NOT EXISTS FOR (e:Episodic) ON (e.group_id)",
            "CREATE INDEX episodic_source IF NOT EXISTS FOR (e:Episodic) ON (e.source)"
        ]
        
        for index in indexes:
            try:
                session.run(index)
                print(f"✅ Created index: {index.split('CREATE INDEX ')[1].split(' IF')[0]}")
            except Exception as e:
                print(f"⚠️  Index may already exist: {index.split('CREATE INDEX ')[1].split(' IF')[0]}")
        
        # Create fulltext indexes that Graphiti needs
        fulltext_indexes = [
            """
            CREATE FULLTEXT INDEX node_name_and_summary IF NOT EXISTS
            FOR (n:Entity|Episodic) 
            ON EACH [n.name, n.summary]
            """,
            """
            CREATE FULLTEXT INDEX entity_name_fulltext IF NOT EXISTS
            FOR (n:Entity) 
            ON EACH [n.name]
            """
        ]
        
        for fulltext_index in fulltext_indexes:
            try:
                session.run(fulltext_index)
                index_name = fulltext_index.split('INDEX ')[1].split(' IF')[0]
                print(f"✅ Created fulltext index: {index_name}")
            except Exception as e:
                index_name = fulltext_index.split('INDEX ')[1].split(' IF')[0]
                print(f"⚠️  Fulltext index may already exist: {index_name}")
        
        # Create vector indexes for embeddings (if supported)
        try:
            session.run("""
                CREATE VECTOR INDEX entity_name_embedding IF NOT EXISTS
                FOR (e:Entity) ON (e.name_embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
            """)
            print("✅ Created vector index: entity_name_embedding")
        except Exception as e:
            print(f"⚠️  Vector index creation failed (may not be supported): {e}")
        
        try:
            session.run("""
                CREATE VECTOR INDEX episodic_summary_embedding IF NOT EXISTS
                FOR (e:Episodic) ON (e.summary_embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
            """)
            print("✅ Created vector index: episodic_summary_embedding")
        except Exception as e:
            print(f"⚠️  Vector index creation failed (may not be supported): {e}")
        
        print("\n🎯 Graphiti database setup complete!")
        print("✨ Neo4j is now ready for Graphiti ingestion")
    
    driver.close()

if __name__ == "__main__":
    setup_graphiti_database()