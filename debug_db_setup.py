from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def debug_database_setup():
    """Debug and fix database setup issues"""
    
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    
    with driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:
        print("🔍 Checking current database state...")
        
        # Check Neo4j version
        try:
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            for record in result:
                print(f"📊 Neo4j {record['name']}: {record['versions'][0]} ({record['edition']})")
        except Exception as e:
            print(f"⚠️  Could not get Neo4j version: {e}")
        
        # Check existing indexes
        print("\n📋 Current indexes:")
        try:
            result = session.run("SHOW INDEXES")
            indexes = []
            for record in result:
                indexes.append(record)
                print(f"  - {record.get('name', 'unnamed')}: {record.get('type', 'unknown')} on {record.get('labelsOrTypes', 'unknown')}")
            
            if not indexes:
                print("  (No indexes found)")
        except Exception as e:
            print(f"⚠️  Could not list indexes: {e}")
        
        # Check existing constraints
        print("\n🔒 Current constraints:")
        try:
            result = session.run("SHOW CONSTRAINTS")
            constraints = []
            for record in result:
                constraints.append(record)
                print(f"  - {record.get('name', 'unnamed')}: {record.get('type', 'unknown')}")
            
            if not constraints:
                print("  (No constraints found)")
        except Exception as e:
            print(f"⚠️  Could not list constraints: {e}")
        
        # Try to create the required fulltext index step by step
        print("\n🔧 Creating required fulltext index...")
        
        # Drop existing if it exists
        try:
            session.run("DROP INDEX node_name_and_summary IF EXISTS")
            print("  Dropped existing node_name_and_summary index")
        except Exception as e:
            print(f"  No existing index to drop: {e}")
        
        # Create new fulltext index
        try:
            session.run("""
                CREATE FULLTEXT INDEX node_name_and_summary
                FOR (n:Entity|Episodic) 
                ON EACH [n.name, n.summary]
            """)
            print("✅ Successfully created node_name_and_summary fulltext index")
        except Exception as e:
            print(f"❌ Failed to create fulltext index: {e}")
            
            # Try alternative syntax
            try:
                session.run("""
                    CALL db.index.fulltext.createNodeIndex('node_name_and_summary', ['Entity', 'Episodic'], ['name', 'summary'])
                """)
                print("✅ Successfully created fulltext index using alternative syntax")
            except Exception as e2:
                print(f"❌ Alternative syntax also failed: {e2}")
        
        # Verify the index was created
        print("\n🔍 Verifying fulltext index creation...")
        try:
            result = session.run("SHOW INDEXES WHERE type = 'FULLTEXT'")
            fulltext_indexes = list(result)
            if fulltext_indexes:
                for record in fulltext_indexes:
                    print(f"✅ Found fulltext index: {record.get('name', 'unnamed')}")
            else:
                print("❌ No fulltext indexes found")
        except Exception as e:
            print(f"⚠️  Could not verify fulltext indexes: {e}")
        
        # Test the fulltext index
        if fulltext_indexes:
            print("\n🧪 Testing fulltext index...")
            try:
                result = session.run("CALL db.index.fulltext.queryNodes('node_name_and_summary', 'test') YIELD node, score RETURN count(*)")
                count = result.single()[0]
                print(f"✅ Fulltext index is working (found {count} results for 'test')")
            except Exception as e:
                print(f"❌ Fulltext index test failed: {e}")
    
    driver.close()

if __name__ == "__main__":
    debug_database_setup()