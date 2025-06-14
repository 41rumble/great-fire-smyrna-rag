#!/usr/bin/env python3
"""
Test searching for the entities Graphiti actually extracted
"""

import asyncio
from graphiti_core import Graphiti

async def test_actual_entities():
    """Search for entities that Graphiti actually created"""
    
    print("🔍 TESTING SEARCH FOR ACTUAL ENTITIES")
    print("=" * 50)
    
    graphiti = Graphiti(
        uri="bolt://localhost:7687",
        user="neo4j", 
        password="Sk1pper(())"
    )
    
    # Search for entities we know exist
    test_queries = [
        "Greek naval officer",
        "Greek forces", 
        "American forces",
        "naval officer",
        "officer",
        "Greek",
        "forces"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")
        
        try:
            results = await graphiti.search(query, num_results=3)
            
            if results and hasattr(results, 'results') and len(results.results) > 0:
                print(f"✅ Found {len(results.results)} results:")
                for i, result in enumerate(results.results):
                    print(f"   {i+1}. {result}")
            else:
                print("❌ No results")
                
        except Exception as e:
            print(f"❌ Search error: {e}")
    
    print(f"\n🔍 ENTITY SEARCH TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_actual_entities())