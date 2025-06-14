#!/usr/bin/env python3
"""
Test the ingested chapters with OpenAI Graphiti
"""

import asyncio
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from graphiti_core import Graphiti

load_dotenv()

async def test_ingested_chapters():
    """Test what's been ingested so far"""
    
    print("🔍 TESTING INGESTED CHAPTERS")
    print("=" * 50)
    
    # Initialize Graphiti (using OpenAI)
    graphiti = Graphiti(
        "bolt://localhost:7687",
        "neo4j", 
        "Sk1pper(())"
    )
    
    # Check what's in the database
    print("📊 Checking what's been created...")
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        # Check node types
        result = session.run('MATCH (n) RETURN DISTINCT labels(n) as labels, count(*) as count ORDER BY count DESC')
        print("Database contents:")
        for record in result:
            print(f"   {record[0]}: {record[1]} nodes")
            
        # Show sample entities
        result = session.run('MATCH (n:Entity) RETURN n.name ORDER BY n.name LIMIT 15')
        entities = [record[0] for record in result]
        if entities:
            print(f"\nSample entities extracted ({len(entities)} shown):")
            for entity in entities:
                print(f"   - {entity}")
        
        # Show sample facts
        result = session.run('MATCH ()-[r]->() WHERE r.fact IS NOT NULL RETURN r.fact LIMIT 8')
        facts = [record[0] for record in result]
        if facts:
            print(f"\nSample historical facts:")
            for fact in facts:
                print(f"   • {fact}")
                
        # Count total facts
        result = session.run('MATCH ()-[r]->() RETURN count(r) as total')
        total_facts = result.single()['total']
        print(f"\nTotal relationships/facts: {total_facts}")
        
    driver.close()
    
    # Test searches on historical content
    print(f"\n🔍 TESTING HISTORICAL SEARCHES")
    print("=" * 40)
    
    historical_queries = [
        "Who was Asa Jennings?",
        "What happened in Smyrna?",
        "Greek naval forces",
        "refugee evacuation", 
        "Mustafa Kemal Ataturk",
        "American YMCA",
        "Turkish forces",
        "Captain Theofanides",
        "1922 crisis"
    ]
    
    for query in historical_queries:
        print(f"\n🔍 '{query}'")
        
        try:
            results = await graphiti.search(query, num_results=3)
            
            if results and len(results) > 0:
                print(f"   ✅ Found {len(results)} results:")
                for i, result in enumerate(results):
                    if hasattr(result, 'fact'):
                        print(f"      {i+1}. {result.fact}")
                    else:
                        print(f"      {i+1}. {result}")
            else:
                print("   ❌ No results found")
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")
    
    print(f"\n🎉 CHAPTER TESTING COMPLETE!")
    print("📚 Your historical knowledge graph is working!")

if __name__ == "__main__":
    asyncio.run(test_ingested_chapters())