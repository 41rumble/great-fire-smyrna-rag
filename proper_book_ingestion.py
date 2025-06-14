#!/usr/bin/env python3
"""
Proper book ingestion using the working Graphiti approach
"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

load_dotenv()

async def proper_book_ingestion():
    """Ingest book content using the proper Graphiti approach"""
    
    print("📚 PROPER BOOK INGESTION WITH GRAPHITI")
    print("=" * 60)
    
    # Clean database for fresh start
    print("🧹 Cleaning database for fresh ingestion...")
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()
    print("✅ Database cleaned")
    
    # Initialize Graphiti properly
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'Sk1pper(())')
    
    graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
    
    print("✅ Graphiti initialized properly")
    
    # Build indices and constraints
    await graphiti.build_indices_and_constraints()
    print("✅ Indices built")
    
    # Get text files to ingest
    text_files_dir = Path("text_files")
    if not text_files_dir.exists():
        print("❌ text_files directory not found")
        return
    
    text_files = list(text_files_dir.glob("*.txt"))
    if not text_files:
        print("❌ No text files found")
        return
    
    print(f"📁 Found {len(text_files)} text files to ingest")
    
    # Ingest each file as an episode
    for i, text_file in enumerate(text_files):
        print(f"\n📄 Ingesting {i+1}/{len(text_files)}: {text_file.name}")
        
        try:
            # Read the content
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if len(content) < 100:  # Skip very short files
                print(f"   ⚠️  Skipping short file ({len(content)} chars)")
                continue
                
            print(f"   📊 Content length: {len(content)} characters")
            
            # Create episode name from filename
            episode_name = text_file.stem.replace('_', ' ').title()
            
            # Add to Graphiti using proper format
            await graphiti.add_episode(
                name=episode_name,
                episode_body=content,
                source=EpisodeType.text,  # This was the key missing piece!
                source_description=f"Historical text from {text_file.name}",
                reference_time=datetime(1922, 9, 15, tzinfo=timezone.utc)  # Smyrna crisis date
            )
            
            print(f"   ✅ Episode ingested successfully")
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Failed to ingest {text_file.name}: {e}")
    
    print(f"\n⏳ Waiting for processing to complete...")
    await asyncio.sleep(5)
    
    # Test the ingested content with searches
    print(f"\n🔍 TESTING SEARCHES ON INGESTED CONTENT")
    print("=" * 50)
    
    test_queries = [
        "Who was Asa Jennings?",
        "What happened in Smyrna?",
        "Greek forces",
        "American evacuation", 
        "Mustafa Kemal Ataturk",
        "refugees",
        "fire in Smyrna"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching: '{query}'")
        
        try:
            results = await graphiti.search(query, num_results=3)
            
            if results and len(results) > 0:
                print(f"✅ Found {len(results)} results:")
                for j, result in enumerate(results):
                    if hasattr(result, 'fact'):
                        print(f"   {j+1}. {result.name}: {result.fact}")
                    else:
                        print(f"   {j+1}. {result}")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Search error: {e}")
    
    # Show what was created in the database
    print(f"\n📊 DATABASE SUMMARY")
    print("=" * 30)
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        # Count different types of nodes
        result = session.run("MATCH (n) RETURN DISTINCT labels(n) as labels, count(*) as count ORDER BY count DESC")
        print("Node types created:")
        for record in result:
            print(f"   {record['labels']}: {record['count']} nodes")
        
        # Show some entities extracted
        result = session.run("MATCH (n:Entity) RETURN n.name ORDER BY n.name LIMIT 10")
        print(f"\nSample entities extracted:")
        for record in result:
            print(f"   - {record['n.name']}")
            
        # Count relationships/facts
        result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
        rel_count = result.single()['rel_count']
        print(f"\nRelationships/Facts: {rel_count}")
        
    driver.close()
    
    print(f"\n📚 BOOK INGESTION COMPLETE!")
    print("🎉 Graphiti has extracted entities, relationships, and facts from your historical books!")
    print("🔍 You can now search for people, events, places, and relationships")

if __name__ == "__main__":
    asyncio.run(proper_book_ingestion())