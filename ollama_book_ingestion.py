#!/usr/bin/env python3
"""
Book ingestion using Ollama with the correct Graphiti pattern
"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_with_local_models import OllamaLLMClient, OllamaEmbedder

load_dotenv()

async def ollama_book_ingestion():
    """Ingest books using Ollama with proper Graphiti workflow"""
    
    print("🦙 OLLAMA BOOK INGESTION (CORRECT PATTERN)")
    print("=" * 60)
    
    # Initialize Ollama clients
    llm_client = OllamaLLMClient()
    embedder = OllamaEmbedder()
    
    print("✅ Ollama clients initialized")
    
    # Clean database for fresh start
    print("🧹 Cleaning database...")
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()
    print("✅ Database cleaned")
    
    # Initialize Graphiti with Ollama (using correct pattern)
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'Sk1pper(())')
    
    graphiti = Graphiti(
        neo4j_uri, 
        neo4j_user, 
        neo4j_password,
        llm_client=llm_client,
        embedder=embedder
    )
    
    print("✅ Graphiti initialized with Ollama")
    
    # Build indices and constraints
    await graphiti.build_indices_and_constraints()
    print("✅ Indices built")
    
    # Get text files
    text_files_dir = Path("text_files")
    if not text_files_dir.exists():
        print("❌ text_files directory not found")
        return
    
    text_files = list(text_files_dir.glob("*.txt"))[:5]  # Start with just 5 files
    if not text_files:
        print("❌ No text files found")
        return
    
    print(f"📁 Processing {len(text_files)} text files with Ollama")
    
    # Ingest each file using the CORRECT pattern
    for i, text_file in enumerate(text_files):
        print(f"\n📄 Processing {i+1}/{len(text_files)}: {text_file.name}")
        
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if len(content) < 100:
                print(f"   ⚠️  Skipping short file")
                continue
                
            print(f"   📊 Content: {len(content)} characters")
            
            episode_name = text_file.stem.replace('_', ' ').title()
            
            # Use the EXACT working pattern with Ollama
            await graphiti.add_episode(
                name=episode_name,
                episode_body=content,
                source=EpisodeType.text,  # THE KEY PARAMETER!
                source_description=f"Historical text: {text_file.name}",
                reference_time=datetime(1922, 9, 15, tzinfo=timezone.utc)
            )
            
            print(f"   ✅ Ingested with Ollama")
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n⏳ Processing complete, testing search...")
    await asyncio.sleep(3)
    
    # Test search with Ollama
    print(f"\n🔍 TESTING OLLAMA-POWERED SEARCH")
    print("=" * 40)
    
    test_queries = [
        "Who was Asa Jennings?",
        "What happened in Smyrna?", 
        "Greek forces",
        "American evacuation"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Ollama search: '{query}'")
        
        try:
            results = await graphiti.search(query, num_results=2)
            
            if results and len(results) > 0:
                print(f"✅ Ollama found {len(results)} results:")
                for j, result in enumerate(results):
                    if hasattr(result, 'fact'):
                        print(f"   {j+1}. {result.name}: {result.fact}")
                    else:
                        print(f"   {j+1}. {result}")
            else:
                print("❌ No results")
                
        except Exception as e:
            print(f"❌ Search error: {e}")
    
    print(f"\n🦙 OLLAMA INGESTION COMPLETE!")
    print("💰 Cost: $0 (100% local with Ollama)")

if __name__ == "__main__":
    asyncio.run(ollama_book_ingestion())