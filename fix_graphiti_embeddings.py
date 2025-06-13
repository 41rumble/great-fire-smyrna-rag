#!/usr/bin/env python3
"""
Fix Graphiti embeddings by directly ingesting episodes with proper format
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Set OpenAI key for Graphiti
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
if OPENAI_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_KEY
    from graphiti_core import Graphiti
else:
    print("❌ OpenAI API key required for Graphiti ingestion")
    exit(1)

async def fix_graphiti_embeddings():
    """Create proper Graphiti embeddings for your book content"""
    
    print("🔧 FIXING GRAPHITI EMBEDDINGS")
    print("=" * 50)
    
    # Connect to Neo4j to get episodes
    neo4j_driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD"))
    )
    
    # Initialize Graphiti
    graphiti = Graphiti(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD")
    )
    
    # Get episodes from all sources
    with neo4j_driver.session(database="the-great-fire-db") as session:
        query = """
        MATCH (e:Episode)-[:FROM_SOURCE]->(s:Source)
        WHERE e.content IS NOT NULL AND length(e.content) > 100
        RETURN e.name as name, e.content as content, 
               s.title as source_title, s.author as source_author, s.sourceId as sourceId
        ORDER BY s.sourceId
        LIMIT 50
        """
        
        result = session.run(query)
        episodes = []
        
        for record in result:
            episodes.append({
                "name": record["name"],
                "content": record["content"],
                "source_title": record["source_title"],
                "source_author": record["source_author"],
                "sourceId": record["sourceId"]
            })
    
    neo4j_driver.close()
    
    if not episodes:
        print("❌ No episodes found")
        return
    
    print(f"📖 Found {len(episodes)} episodes to process")
    
    # Group by source
    sources = {}
    for episode in episodes:
        source_id = episode['sourceId']
        if source_id not in sources:
            sources[source_id] = []
        sources[source_id].append(episode)
    
    # Process each source
    for source_id, source_episodes in sources.items():
        print(f"\n📚 Processing {len(source_episodes)} episodes from {source_episodes[0]['source_title']}")
        
        # Process episodes in smaller batches to avoid timeouts
        batch_size = 5
        for i in range(0, len(source_episodes), batch_size):
            batch = source_episodes[i:i+batch_size]
            
            print(f"  🔄 Processing batch {i//batch_size + 1}/{(len(source_episodes)-1)//batch_size + 1}")
            
            for episode in batch:
                try:
                    # Create clean episode body
                    episode_body = f"Source: {episode['source_title']} by {episode['source_author']}\n\n{episode['content']}"
                    
                    # Add to Graphiti with proper parameters
                    await graphiti.add_episode(
                        name=f"[{episode['sourceId']}] {episode['name']}",
                        episode_body=episode_body,
                        source_description=f"{episode['source_title']} by {episode['source_author']}",
                        reference_time=datetime(1922, 9, 15)  # Default reference time
                    )
                    
                    print(f"    ✅ Added: {episode['name'][:50]}...")
                    
                except Exception as e:
                    print(f"    ❌ Failed: {episode['name'][:50]}... - {e}")
                    
            # Small delay between batches
            await asyncio.sleep(1)
    
    print(f"\n🎉 GRAPHITI EMBEDDINGS CREATION COMPLETE!")
    print("🧠 Your semantic search should now work properly")

if __name__ == "__main__":
    asyncio.run(fix_graphiti_embeddings())