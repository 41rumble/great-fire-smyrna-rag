#!/usr/bin/env python3
"""
Test if we can force Graphiti to create embeddings
"""

import asyncio
from datetime import datetime
from debug_embedder_calls import DebugOllamaLLMClient, DebugOllamaEmbedder
from graphiti_core import Graphiti

async def force_embedding_test():
    """Test if we can force embeddings to be created"""
    
    print("🔧 FORCING EMBEDDING TEST")
    print("=" * 50)
    
    embedder = DebugOllamaEmbedder()
    llm_client = DebugOllamaLLMClient()
    
    # Test embedder directly first
    print("1. Testing embedder directly...")
    test_embedding = await embedder.create("test text for embedding")
    print(f"   Direct test: {len(test_embedding)} dimensions")
    
    # Test with Graphiti
    print("\n2. Testing with Graphiti...")
    
    graphiti = Graphiti(
        uri="bolt://localhost:7687/graphiti-clean",
        user="neo4j",
        password="Sk1pper(())",
        llm_client=llm_client,
        embedder=embedder,
        store_raw_episode_content=True  # Make sure content is stored
    )
    
    print("✅ Graphiti initialized with explicit settings")
    
    # Try adding episode with more explicit content
    print("\n3. Adding episode with rich content...")
    
    try:
        result = await graphiti.add_episode(
            name="RICH TEST EPISODE",
            episode_body="""
            This is a detailed test episode with substantial content that should trigger embedding generation.
            
            The episode contains multiple sentences and paragraphs to ensure that Graphiti has enough
            content to work with for entity extraction and embedding generation.
            
            Key topics: Smyrna fire, evacuation, historical events, refugees, international relations
            
            Characters: Asa Jennings, Mustafa Kemal Ataturk, American officials
            
            This content should be rich enough to trigger the full Graphiti processing pipeline
            including entity extraction, fact generation, and embedding creation.
            """,
            source_description="Rich Test Source",
            reference_time=datetime(1922, 9, 15)  # Provide valid datetime
        )
        
        print(f"✅ Episode added successfully")
        print(f"📊 Embedder calls during add: {embedder.call_count}")
        
        # Try a search to see if it triggers embeddings
        print("\n4. Testing search (should trigger query embedding)...")
        
        search_results = await graphiti.search(
            query="Smyrna fire evacuation",
            num_results=1
        )
        
        print(f"📊 Embedder calls after search: {embedder.call_count}")
        
        if search_results and hasattr(search_results, 'results'):
            print(f"🔍 Search found {len(search_results.results)} results")
        
    except Exception as e:
        print(f"❌ Error during episode/search: {e}")
        print(f"📊 Final embedder calls: {embedder.call_count}")

if __name__ == "__main__":
    asyncio.run(force_embedding_test())