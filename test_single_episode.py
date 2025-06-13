#!/usr/bin/env python3
"""
Test adding a single episode to verify the database and embedding fix
"""

import asyncio
from datetime import datetime
from graphiti_with_local_models import OllamaLLMClient, OllamaEmbedder
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig

async def test_single_episode():
    """Test adding one episode to verify everything works"""
    
    print("🧪 TESTING SINGLE EPISODE INGESTION")
    print("=" * 50)
    
    # Initialize with corrected database
    llm_client = OllamaLLMClient()
    embedder = OllamaEmbedder()
    
    # Try with database in URI or see if there's another way
    graphiti = Graphiti(
        uri="bolt://localhost:7687/the-great-fire-db",
        user="neo4j",
        password="Sk1pper(())",
        llm_client=llm_client,
        embedder=embedder
    )
    
    print("✅ Graphiti initialized with the-great-fire-db")
    
    # Test adding a simple episode
    try:
        await graphiti.add_episode(
            name="TEST EPISODE - Flames on Water Test",
            episode_body="This is a test episode about flames on the water from our book. It contains some test content to verify that embeddings work properly with our local Ollama setup.",
            source_description="Test Source - Flames on Water",
            reference_time=datetime(1922, 9, 15)
        )
        
        print("✅ Test episode added successfully")
        
        # Now test search
        print("\n🔍 Testing search on new episode...")
        
        results = await graphiti.search(
            query="flames water test",
            num_results=2
        )
        
        if results and hasattr(results, 'results') and len(results.results) > 0:
            print(f"✅ Search successful! Found {len(results.results)} results")
            for i, result in enumerate(results.results):
                if hasattr(result, 'episode'):
                    print(f"   {i+1}. {result.episode.name}")
        else:
            print("❌ Search found no results")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n🎉 SINGLE EPISODE TEST COMPLETE!")

if __name__ == "__main__":
    asyncio.run(test_single_episode())