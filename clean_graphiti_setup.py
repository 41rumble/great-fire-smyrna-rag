#!/usr/bin/env python3
"""
Set up Graphiti in a separate clean database for pure local operation
"""

import asyncio
from datetime import datetime
from neo4j import GraphDatabase
from graphiti_with_local_models import OllamaLLMClient, OllamaEmbedder
from graphiti_core import Graphiti

async def setup_clean_graphiti():
    """Set up Graphiti in a clean separate database"""
    
    print("🧹 SETTING UP CLEAN GRAPHITI DATABASE")
    print("=" * 60)
    
    # First, create the new database
    print("1. Creating new database 'graphiti-clean'...")
    
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "Sk1pper(())")
    )
    
    try:
        with driver.session() as session:
            # Create new database
            session.run("CREATE DATABASE `graphiti-clean` IF NOT EXISTS")
            print("✅ Database 'graphiti-clean' created")
    except Exception as e:
        print(f"⚠️  Database creation info: {e}")
    
    driver.close()
    
    # Initialize Graphiti with clean database
    print("\n2. Initializing Graphiti with local models in clean DB...")
    
    llm_client = OllamaLLMClient()
    embedder = OllamaEmbedder()
    
    graphiti = Graphiti(
        uri="bolt://localhost:7687/graphiti-clean",
        user="neo4j",
        password="Sk1pper(())",
        llm_client=llm_client,
        embedder=embedder
    )
    
    print("✅ Clean Graphiti initialized")
    
    # Get some sample episodes from original database to test with
    print("\n3. Getting sample episodes from original database...")
    
    orig_driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "Sk1pper(())")
    )
    
    with orig_driver.session(database="the-great-fire-db") as session:
        query = """
        MATCH (e:Episode)-[:FROM_SOURCE]->(s:Source)
        WHERE e.content IS NOT NULL AND size(e.content) > 200
        RETURN e.name as name, e.content as content, 
               s.title as source_title, s.author as source_author, 
               s.sourceId as sourceId, s.perspective as perspective,
               e.chapter_title as chapter
        ORDER BY s.sourceId, e.name
        LIMIT 5
        """
        
        result = session.run(query)
        episodes = []
        
        for record in result:
            episodes.append({
                "name": record["name"],
                "content": record["content"],
                "source_title": record["source_title"],
                "source_author": record["source_author"],
                "sourceId": record["sourceId"],
                "perspective": record["perspective"],
                "chapter": record["chapter"]
            })
    
    orig_driver.close()
    
    if not episodes:
        print("❌ No episodes found in original database")
        return
    
    print(f"✅ Found {len(episodes)} sample episodes")
    
    # Ingest episodes to clean Graphiti
    print("\n4. Ingesting episodes to clean Graphiti...")
    
    for i, episode in enumerate(episodes):
        try:
            episode_body = f"""
SOURCE: {episode['source_title']} by {episode['source_author']}
PERSPECTIVE: {episode['perspective']}
CHAPTER: {episode['chapter']}

{episode['content']}
"""
            
            await graphiti.add_episode(
                name=f"[{episode['sourceId']}] {episode['name']}",
                episode_body=episode_body,
                source_description=f"{episode['source_title']} - {episode['chapter']}",
                reference_time=datetime(1922, 9, 15)
            )
            
            print(f"  ✅ Episode {i+1}/{len(episodes)}: {episode['name'][:50]}...")
            
        except Exception as e:
            print(f"  ❌ Failed episode {i+1}: {e}")
    
    # Test search in clean environment
    print("\n5. Testing search in clean Graphiti...")
    
    test_queries = [
        "Flames on the Water",
        "Smyrna fire", 
        "evacuation",
        "American"
    ]
    
    for query in test_queries:
        try:
            results = await graphiti.search(
                query=query,
                num_results=2
            )
            
            if results and hasattr(results, 'results') and len(results.results) > 0:
                print(f"✅ '{query}': Found {len(results.results)} results")
                for i, result in enumerate(results.results):
                    if hasattr(result, 'episode') and hasattr(result.episode, 'name'):
                        print(f"   {i+1}. {result.episode.name}")
            else:
                print(f"❌ '{query}': No results found")
                
        except Exception as e:
            print(f"❌ '{query}': Search error - {e}")
    
    print(f"\n🎉 CLEAN GRAPHITI SETUP COMPLETE!")
    print("🦙 100% local operation with clean database!")
    print("💾 Original data preserved in 'the-great-fire-db'")
    print("🧠 Graphiti data in 'graphiti-clean' database")

if __name__ == "__main__":
    asyncio.run(setup_clean_graphiti())