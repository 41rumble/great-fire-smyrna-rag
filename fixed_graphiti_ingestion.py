#!/usr/bin/env python3
"""
Fixed Graphiti ingestion based on the official quickstart example
"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from debug_embedder_calls import DebugOllamaLLMClient, DebugOllamaEmbedder
from graphiti_core import Graphiti

async def fixed_graphiti_ingestion():
    """Ingest using the correct Graphiti approach from quickstart"""
    
    print("🔧 FIXED GRAPHITI INGESTION (Following Official Example)")
    print("=" * 70)
    
    # Initialize with debug to see what's happening
    llm_client = DebugOllamaLLMClient()
    embedder = DebugOllamaEmbedder()
    
    # Initialize exactly like the official example
    graphiti = Graphiti(
        uri="bolt://localhost:7687/graphiti-fixed",
        user="neo4j",
        password="Sk1pper(())",
        llm_client=llm_client,
        embedder=embedder
    )
    
    print("✅ Graphiti initialized")
    
    # CRITICAL: Build indices and constraints (from official example)
    print("🔨 Building indices and constraints...")
    try:
        await graphiti.build_indices_and_constraints()
        print("✅ Indices and constraints built")
    except Exception as e:
        print(f"⚠️  Indices/constraints info: {e}")
    
    # Get a text file to test with
    text_files_dir = Path("text_files")
    text_files = list(text_files_dir.glob("*.txt"))[:1]  # Just one for testing
    
    if not text_files:
        print("❌ No text files found")
        return
    
    text_file = text_files[0]
    print(f"📄 Testing with: {text_file.name}")
    
    # Read the content
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📊 Content length: {len(content)} characters")
    
    # Add episode using official example format
    print(f"\n📝 Adding episode using official format...")
    
    try:
        await graphiti.add_episode(
            name=f'Historical Text - {text_file.stem}',
            episode_body=content,  # Raw text content
            source_description='Historical text file',  # Use official parameter name
            reference_time=datetime.now(timezone.utc)  # Use timezone-aware datetime like example
        )
        
        print(f"✅ Episode added successfully")
        print(f"📊 Embedder calls during add: {embedder.call_count}")
        
    except Exception as e:
        print(f"❌ Failed to add episode: {e}")
        return
    
    # Test search
    print(f"\n🔍 Testing search...")
    
    try:
        results = await graphiti.search(
            query="historical text",
            num_results=1
        )
        
        if results and hasattr(results, 'results') and len(results.results) > 0:
            print(f"✅ Search successful! Found {len(results.results)} results")
            for i, result in enumerate(results.results):
                if hasattr(result, 'episode') and hasattr(result.episode, 'name'):
                    print(f"   {i+1}. {result.episode.name}")
        else:
            print("❌ Search found no results")
            
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    print(f"\n📊 Final embedder call count: {embedder.call_count}")
    print(f"🔧 FIXED INGESTION TEST COMPLETE!")

if __name__ == "__main__":
    asyncio.run(fixed_graphiti_ingestion())