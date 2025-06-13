#!/usr/bin/env python3
"""
Test the current Graphiti setup with local Ollama models
"""

import asyncio
from datetime import datetime
from graphiti_with_local_models import OllamaLLMClient, OllamaEmbedder
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig

async def test_graphiti_functionality():
    """Test the Graphiti semantic search with what's already ingested"""
    
    print("🧪 TESTING CURRENT GRAPHITI FUNCTIONALITY")
    print("=" * 60)
    
    # Initialize the same way as the working script
    llm_client = OllamaLLMClient()
    embedder = OllamaEmbedder()
    
    # Initialize Graphiti
    graphiti = Graphiti(
        uri="bolt://localhost:7687/the-great-fire-db",
        user="neo4j", 
        password="Sk1pper(())",
        llm_client=llm_client,
        embedder=embedder
    )
    
    print("🔍 Testing search capabilities...")
    
    # Test queries that should work with even 1-2 episodes
    test_queries = [
        "Flames on the Water",
        "Section 001", 
        "Copyright",
        "water",
        "flames"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        
        try:
            results = await graphiti.search(
                query=query,
                num_results=2
            )
            
            if results and hasattr(results, 'results') and len(results.results) > 0:
                print(f"✅ Found {len(results.results)} results")
                
                for i, result in enumerate(results.results):
                    if hasattr(result, 'episode') and hasattr(result.episode, 'name'):
                        print(f"   {i+1}. {result.episode.name}")
                        if hasattr(result.episode, 'content'):
                            print(f"      Content preview: {result.episode.content[:100]}...")
                    else:
                        print(f"   {i+1}. Result: {str(result)[:100]}...")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    print(f"\n🧠 GRAPHITI FUNCTIONALITY TEST COMPLETE!")
    print("🦙 All using local Ollama models - no API costs!")

if __name__ == "__main__":
    asyncio.run(test_graphiti_functionality())