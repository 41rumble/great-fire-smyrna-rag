#!/usr/bin/env python3
"""
Fresh Graphiti ingestion from raw text files - let Graphiti handle everything naturally
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from debug_embedder_calls import DebugOllamaLLMClient, DebugOllamaEmbedder
from graphiti_core import Graphiti

async def fresh_graphiti_ingestion():
    """Ingest raw text files directly into Graphiti the natural way"""
    
    print("🌱 FRESH GRAPHITI INGESTION FROM RAW TEXT")
    print("=" * 60)
    
    # Initialize with debug to see what's happening
    llm_client = DebugOllamaLLMClient()
    embedder = DebugOllamaEmbedder()
    
    graphiti = Graphiti(
        uri="bolt://localhost:7687/graphiti-fresh",
        user="neo4j",
        password="Sk1pper(())",
        llm_client=llm_client,
        embedder=embedder
    )
    
    print("✅ Fresh Graphiti initialized")
    
    # Get some raw text files to ingest
    text_files_dir = Path("text_files")
    
    if not text_files_dir.exists():
        print("❌ text_files directory not found")
        return
    
    # Find some text files to ingest
    text_files = list(text_files_dir.glob("*.txt"))[:3]  # Just first 3 for testing
    
    if not text_files:
        print("❌ No text files found")
        return
    
    print(f"📁 Found {len(text_files)} text files to ingest")
    
    # Ingest each file as a separate episode
    for i, text_file in enumerate(text_files):
        print(f"\n📄 Ingesting file {i+1}/{len(text_files)}: {text_file.name}")
        
        try:
            # Read the raw content
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"   📊 Content length: {len(content)} characters")
            
            # Let Graphiti handle this naturally
            await graphiti.add_episode(
                name=f"Episode: {text_file.stem}",
                episode_body=content,  # Raw content - let Graphiti process it
                source_description=f"Text file: {text_file.name}",
                reference_time=datetime(1922, 9, 15)
            )
            
            print(f"   ✅ Episode added successfully")
            print(f"   📊 Embedder calls so far: {embedder.call_count}")
            
        except Exception as e:
            print(f"   ❌ Failed to ingest {text_file.name}: {e}")
    
    print(f"\n🔍 Testing search after natural ingestion...")
    print(f"📊 Total embedder calls during ingestion: {embedder.call_count}")
    
    # Test search
    test_queries = ["Smyrna", "evacuation", "fire"]
    
    for query in test_queries:
        try:
            print(f"\n🔍 Searching for: '{query}'")
            
            results = await graphiti.search(
                query=query,
                num_results=2
            )
            
            if results and hasattr(results, 'results') and len(results.results) > 0:
                print(f"✅ Found {len(results.results)} results")
                for j, result in enumerate(results.results):
                    if hasattr(result, 'episode') and hasattr(result.episode, 'name'):
                        print(f"   {j+1}. {result.episode.name}")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Search error: {e}")
    
    print(f"\n📊 Final embedder call count: {embedder.call_count}")
    print(f"🌱 FRESH INGESTION COMPLETE!")

if __name__ == "__main__":
    asyncio.run(fresh_graphiti_ingestion())