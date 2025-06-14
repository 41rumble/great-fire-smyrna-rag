#!/usr/bin/env python3
"""
Clean start test - wipe database and test basic functionality
"""

import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from neo4j import GraphDatabase
from graphiti_core import Graphiti

load_dotenv()

async def clean_start_test():
    """Clean database and test basic Graphiti functionality"""
    
    print("🧹 CLEAN START GRAPHITI TEST")
    print("=" * 50)
    
    # Clean the database first
    print("🗑️  Cleaning database...")
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()
    print("✅ Database cleaned")
    
    # Initialize fresh Graphiti
    graphiti = Graphiti(
        uri="bolt://localhost:7687",
        user="neo4j", 
        password="Sk1pper(())"
    )
    
    print("✅ Fresh Graphiti initialized")
    
    # Build indices
    await graphiti.build_indices_and_constraints()
    print("✅ Indices built")
    
    # Add a very simple, clear episode
    simple_episode = """
    John Smith met Mary Johnson at the library yesterday. 
    They discussed the upcoming conference in Boston.
    John works at Google and Mary works at Microsoft.
    """
    
    print("📝 Adding simple episode...")
    
    await graphiti.add_episode(
        name="Library Meeting",
        episode_body=simple_episode,
        source_description="Test episode",
        reference_time=datetime.now(timezone.utc)
    )
    
    print("✅ Episode added")
    
    # Check what was created
    print("\n🔍 Checking what was created...")
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN labels(n), n.name ORDER BY n.name")
        for record in result:
            print(f"   {record[0]} - {record[1]}")
    driver.close()
    
    # Wait a moment for processing
    print("\n⏳ Waiting for processing...")
    await asyncio.sleep(2)
    
    # Try searching for things that definitely exist
    test_searches = ["John", "Mary", "library", "Google", "Microsoft", "Boston"]
    
    for search_term in test_searches:
        print(f"\n🔍 Searching for: '{search_term}'")
        
        try:
            results = await graphiti.search(search_term, num_results=5)
            
            if results and hasattr(results, 'results') and len(results.results) > 0:
                print(f"✅ Found {len(results.results)} results")
                for i, result in enumerate(results.results):
                    print(f"   {i+1}. {result}")
            else:
                print("❌ No results")
                
        except Exception as e:
            print(f"❌ Search error: {e}")
    
    print(f"\n🧹 CLEAN START TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(clean_start_test())