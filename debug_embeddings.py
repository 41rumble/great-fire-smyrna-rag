#!/usr/bin/env python3
"""
Debug embedding dimensions to find the mismatch
"""

import asyncio
from graphiti_with_local_models import OllamaEmbedder
from neo4j import GraphDatabase

async def debug_embeddings():
    """Debug what embeddings are being created"""
    
    print("🔍 DEBUGGING EMBEDDING DIMENSIONS")
    print("=" * 50)
    
    # Test our embedder directly
    embedder = OllamaEmbedder()
    
    print("1. Testing direct embedder...")
    test_embedding = await embedder.create("flames water test")
    print(f"   Direct embedder dimension: {len(test_embedding)}")
    print(f"   First few values: {test_embedding[:5]}")
    
    # Check what's stored in database
    print("\n2. Checking stored embeddings...")
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "Sk1pper(())")
    )
    
    with driver.session(database="the-great-fire-db") as session:
        # Check for recent Graphiti nodes
        result = session.run("""
        MATCH (n)
        WHERE n.embedding IS NOT NULL
        RETURN labels(n), n.name, size(n.embedding) as emb_size
        ORDER BY id(n) DESC LIMIT 3
        """)
        
        for record in result:
            print(f"   {record[0]} - {record[1][:50]}... - Size: {record[2]}")
    
    driver.close()
    
    print(f"\n🎯 EMBEDDING DEBUG COMPLETE!")

if __name__ == "__main__":
    asyncio.run(debug_embeddings())