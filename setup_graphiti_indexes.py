#!/usr/bin/env python3
"""
Set up required Neo4j indexes for Graphiti
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def setup_graphiti_indexes():
    """Create the required fulltext indexes for Graphiti"""
    
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD"))
    )
    
    print("🔧 Setting up Graphiti indexes in Neo4j...")
    
    # Required indexes for Graphiti
    indexes = [
        {
            "name": "edge_name_and_fact",
            "type": "relationship",
            "query": "CREATE FULLTEXT INDEX edge_name_and_fact IF NOT EXISTS FOR ()-[r:RELATES_TO|MENTIONS|PART_OF]-() ON EACH [r.name, r.fact]"
        },
        {
            "name": "node_name_and_fact", 
            "type": "node",
            "query": "CREATE FULLTEXT INDEX node_name_and_fact IF NOT EXISTS FOR (n:Entity|Episode|Character|Event) ON EACH [n.name, n.fact, n.content]"
        },
        {
            "name": "episode_content",
            "type": "node", 
            "query": "CREATE FULLTEXT INDEX episode_content IF NOT EXISTS FOR (n:Episode) ON EACH [n.content, n.name]"
        }
    ]
    
    with driver.session() as session:
        for index in indexes:
            try:
                print(f"📊 Creating {index['type']} index: {index['name']}")
                session.run(index["query"])
                print(f"✅ Index {index['name']} created successfully")
            except Exception as e:
                if "already exists" in str(e) or "An equivalent" in str(e):
                    print(f"ℹ️  Index {index['name']} already exists")
                else:
                    print(f"❌ Failed to create index {index['name']}: {e}")
        
        # Wait for indexes to come online
        print("\n⏳ Waiting for indexes to come online...")
        try:
            session.run("CALL db.awaitIndexes(30)")
            print("✅ All indexes are online")
        except Exception as e:
            print(f"⚠️  Index status check failed: {e}")
            print("💡 Indexes may still be building - try again in a minute")
    
    driver.close()
    print("\n🎉 Graphiti index setup complete!")
    print("💡 You can now use semantic search with Graphiti")

if __name__ == "__main__":
    setup_graphiti_indexes()