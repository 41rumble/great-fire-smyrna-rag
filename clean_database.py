#!/usr/bin/env python3
"""
Simple database cleaner for Graphiti knowledge graph
"""

from neo4j import GraphDatabase

def clean_database():
    """Clean the Neo4j database completely"""
    
    print("🧹 CLEANING GRAPHITI DATABASE")
    print("=" * 40)
    
    # Connect and clean
    print("🗑️  Connecting to Neo4j...")
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    
    try:
        with driver.session() as session:
            # Check what exists first
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = result.single()['total_nodes']
            
            if total_nodes == 0:
                print("✅ Database is already empty")
                return
            
            print(f"📊 Found {total_nodes} nodes to delete")
            
            # Confirm deletion
            response = input(f"⚠️  Are you sure you want to delete ALL {total_nodes} nodes? (y/N): ")
            
            if response.lower() != 'y':
                print("❌ Deletion cancelled")
                return
            
            # Delete everything
            print("🗑️  Deleting all nodes and relationships...")
            session.run("MATCH (n) DETACH DELETE n")
            
            # Verify deletion
            result = session.run("MATCH (n) RETURN count(n) as remaining")
            remaining = result.single()['remaining']
            
            if remaining == 0:
                print("✅ Database cleaned successfully")
                print("🎯 Ready for fresh ingestion")
            else:
                print(f"⚠️  Warning: {remaining} nodes still remain")
                
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")
        
    finally:
        driver.close()

if __name__ == "__main__":
    clean_database()