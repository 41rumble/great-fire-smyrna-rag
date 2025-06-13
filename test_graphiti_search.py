#!/usr/bin/env python3
"""
Test Graphiti search directly to see if it's working
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Set OpenAI key for Graphiti
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
if OPENAI_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_KEY
    from graphiti_core import Graphiti
else:
    print("❌ No OpenAI API key - Graphiti disabled")
    exit(1)

async def test_graphiti_search():
    """Test if Graphiti can find our book content"""
    
    print("🧠 TESTING GRAPHITI SEARCH")
    print("=" * 40)
    
    # Initialize Graphiti
    graphiti = Graphiti(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD")
    )
    
    # Test searches
    test_queries = [
        "Girdis family",
        "Nicholas Girdis", 
        "Con Aroney",
        "Smyrna fire",
        "American evacuation"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        
        try:
            results = await graphiti.search(
                query=query,
                num_results=3
            )
            
            if results and hasattr(results, 'results') and len(results.results) > 0:
                print(f"✅ Found {len(results.results)} results")
                
                for i, result in enumerate(results.results[:2]):
                    if hasattr(result, 'episode') and hasattr(result.episode, 'name'):
                        print(f"   {i+1}. {result.episode.name}")
                        if hasattr(result.episode, 'content'):
                            content_preview = result.episode.content[:100] + "..."
                            print(f"      Content: {content_preview}")
                    elif hasattr(result, 'content'):
                        print(f"   {i+1}. {result.content[:100]}...")
                    else:
                        print(f"   {i+1}. {result}")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    print("\n🧠 GRAPHITI SEARCH TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_graphiti_search())