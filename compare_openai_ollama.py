#!/usr/bin/env python3
"""
Compare OpenAI vs Ollama results to see why entity extraction isn't working
"""

import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from neo4j import GraphDatabase

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

load_dotenv()

async def compare_openai_ollama():
    """Compare what OpenAI vs Ollama actually produces"""
    
    print("🔍 COMPARING OPENAI VS OLLAMA RESULTS")
    print("=" * 60)
    
    # Test with OpenAI first
    print("🤖 Testing with OpenAI...")
    
    # Clean database
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()
    
    # OpenAI test
    graphiti_openai = Graphiti(
        "bolt://localhost:7687",
        "neo4j", 
        "Sk1pper(())"
    )
    
    await graphiti_openai.build_indices_and_constraints()
    
    test_content = """
    Captain Ioannis Theofanides was a Greek naval officer during the 1922 Smyrna crisis. 
    He worked with Asa Jennings to evacuate refugees. Jennings was an American YMCA worker.
    They coordinated with Turkish forces led by Mustafa Kemal Ataturk.
    """
    
    await graphiti_openai.add_episode(
        name="OpenAI Test Episode",
        episode_body=test_content,
        source=EpisodeType.text,
        source_description="Test with OpenAI",
        reference_time=datetime(1922, 9, 15, tzinfo=timezone.utc)
    )
    
    print("✅ OpenAI episode added")
    await asyncio.sleep(2)
    
    # Check what OpenAI created
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        result = session.run('MATCH (n) RETURN DISTINCT labels(n) as labels, count(*) as count ORDER BY count DESC')
        print("OpenAI created:")
        for record in result:
            print(f"   {record[0]}: {record[1]} nodes")
            
        result = session.run('MATCH (n:Entity) RETURN n.name LIMIT 5')
        print("OpenAI entities:")
        for record in result:
            print(f"   - {record[0]}")
            
        result = session.run('MATCH ()-[r]->() WHERE r.fact IS NOT NULL RETURN r.fact LIMIT 3')
        print("OpenAI facts:")
        for record in result:
            print(f"   • {record[0]}")
    driver.close()
    
    # Test search with OpenAI
    try:
        results = await graphiti_openai.search("Asa Jennings", num_results=2)
        print(f"OpenAI search results: {len(results) if results else 0}")
    except Exception as e:
        print(f"OpenAI search error: {e}")
    
    print(f"\n" + "="*60)
    print("Now we know what working Graphiti should produce!")
    print("The issue is likely that Ollama LLM responses aren't in the format Graphiti expects.")

if __name__ == "__main__":
    asyncio.run(compare_openai_ollama())