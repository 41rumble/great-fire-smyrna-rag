from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def fix_graphiti_database():
    """Fix the database connection and indexes for Graphiti"""
    
    # Connect to the exact same database Graphiti uses
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    print(f"🔧 Connecting to: {uri}")
    print(f"👤 Username: {username}")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    # Try both default database and the specific one
    databases_to_fix = ["neo4j", "the-great-fire-db"]
    
    for db_name in databases_to_fix:
        print(f"\n🗄️  Fixing database: {db_name}")
        
        try:
            with driver.session(database=db_name) as session:
                # Drop and recreate the problematic index
                print("   🗑️  Dropping existing fulltext index...")
                try:
                    session.run("DROP INDEX node_name_and_summary IF EXISTS")
                except Exception as e:
                    print(f"     No existing index to drop: {e}")
                
                # Create the fulltext index using procedure call (more reliable)
                print("   🔧 Creating fulltext index with procedure call...")
                try:
                    session.run("""
                        CALL db.index.fulltext.createNodeIndex(
                            'node_name_and_summary', 
                            ['Entity', 'Episodic'], 
                            ['name', 'summary']
                        )
                    """)
                    print("   ✅ Fulltext index created successfully")
                except Exception as e:
                    print(f"   ❌ Procedure call failed: {e}")
                    
                    # Try alternative syntax
                    try:
                        session.run("""
                            CREATE FULLTEXT INDEX node_name_and_summary
                            FOR (n:Entity|Episodic) 
                            ON EACH [n.name, n.summary]
                        """)
                        print("   ✅ Fulltext index created with alternative syntax")
                    except Exception as e2:
                        print(f"   ❌ Alternative syntax failed: {e2}")
                
                # Wait for index to be online
                import time
                time.sleep(2)
                
                # Test the index
                print("   🧪 Testing fulltext index...")
                try:
                    result = session.run("""
                        CALL db.index.fulltext.queryNodes('node_name_and_summary', 'test') 
                        YIELD node, score 
                        RETURN count(*) as count
                    """)
                    count = result.single()["count"]
                    print(f"   ✅ Index test successful (found {count} results)")
                except Exception as e:
                    print(f"   ❌ Index test failed: {e}")
                
                # Show all indexes
                print("   📋 Current indexes in this database:")
                try:
                    result = session.run("SHOW INDEXES WHERE type = 'FULLTEXT'")
                    for record in result:
                        print(f"     - {record.get('name', 'unnamed')}: {record.get('state', 'unknown')}")
                except Exception as e:
                    print(f"     Could not list indexes: {e}")
                    
        except Exception as e:
            print(f"   ❌ Could not connect to database {db_name}: {e}")
    
    driver.close()
    print("\n✨ Database fix complete!")

if __name__ == "__main__":
    fix_graphiti_database()