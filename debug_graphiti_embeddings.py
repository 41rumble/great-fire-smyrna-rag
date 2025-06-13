#!/usr/bin/env python3
"""
Deep debug of Graphiti embedding storage and retrieval
"""

import asyncio
from neo4j import GraphDatabase
from graphiti_with_local_models import OllamaEmbedder

async def debug_graphiti_embeddings():
    """Debug what embeddings are actually stored vs queried"""
    
    print("🔍 DEEP DEBUGGING GRAPHITI EMBEDDINGS")
    print("=" * 60)
    
    # Test our embedder directly
    embedder = OllamaEmbedder()
    
    print("1. Testing embedder directly...")
    test_queries = ["Flames on the Water", "test", "hello"]
    
    for query in test_queries:
        embedding = await embedder.create(query)
        print(f"   '{query}' -> {len(embedding)} dimensions")
        print(f"   First 3 values: {embedding[:3]}")
    
    # Check what's actually in the clean database
    print("\n2. Checking clean database contents...")
    
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "Sk1pper(())")
    )
    
    with driver.session(database="graphiti-clean") as session:
        # Check all node types
        result = session.run("MATCH (n) RETURN DISTINCT labels(n) as labels, count(*) as count ORDER BY count DESC")
        print("   Node types in clean database:")
        for record in result:
            print(f"     {record['labels']} - {record['count']} nodes")
        
        # Check nodes with embeddings
        result = session.run("MATCH (n) WHERE n.embedding IS NOT NULL RETURN labels(n), n.name, size(n.embedding) LIMIT 5")
        print("\n   Nodes with embeddings:")
        for record in result:
            print(f"     {record[0]} - {record[1][:50]}... - Size: {record[2]}")
        
        # Check for any nodes with different embedding sizes
        result = session.run("MATCH (n) WHERE n.embedding IS NOT NULL RETURN DISTINCT size(n.embedding) as size, count(*) as count")
        print("\n   Embedding dimensions:")
        for record in result:
            print(f"     {record['size']} dimensions: {record['count']} nodes")
    
    driver.close()
    
    print(f"\n🎯 EMBEDDING DEBUG COMPLETE!")

if __name__ == "__main__":
    asyncio.run(debug_graphiti_embeddings())