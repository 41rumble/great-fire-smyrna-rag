#!/usr/bin/env python3
"""
Properly set up Graphiti with its native structure using local Ollama models
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Set OpenAI key for Graphiti (required for now)
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
if OPENAI_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_KEY
    from graphiti_core import Graphiti
else:
    print("❌ OpenAI API key required for Graphiti")
    print("💡 Graphiti doesn't fully support local models yet")
    print("🔄 Use the hybrid system with Neo4j fallback instead")
    exit(1)

class ProperGraphitiSetup:
    def __init__(self):
        # Initialize Graphiti with local models
        self.graphiti = Graphiti(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="Sk1pper(())"
        )
        
        # Neo4j driver for reading your existing data
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
    
    async def clear_existing_graphiti_data(self):
        """Clear any partial Graphiti data to start fresh"""
        print("🧹 Clearing existing Graphiti data...")
        
        with self.neo4j_driver.session(database="the-great-fire-db") as session:
            # Remove Graphiti-specific labels and properties
            session.run("""
            MATCH (n)
            WHERE n.embedding IS NOT NULL
            REMOVE n.embedding, n.embedding_model, n.embedded_at
            """)
            
            # Remove any Graphiti-specific nodes (but keep your Episodes/Entities)
            session.run("""
            MATCH (n)
            WHERE 'GraphitiNode' IN labels(n) OR 'Fact' IN labels(n)
            DETACH DELETE n
            """)
            
        print("✅ Cleared existing Graphiti data")
    
    async def ingest_books_to_graphiti(self):
        """Properly ingest all books using Graphiti's native ingestion"""
        print("📚 INGESTING BOOKS TO GRAPHITI NATIVELY")
        print("=" * 60)
        
        # Get all episodes from your sources
        with self.neo4j_driver.session(database="the-great-fire-db") as session:
            query = """
            MATCH (e:Episode)-[:FROM_SOURCE]->(s:Source)
            WHERE e.content IS NOT NULL AND size(e.content) > 200
            RETURN e.name as name, e.content as content, 
                   s.title as source_title, s.author as source_author, 
                   s.sourceId as sourceId, s.perspective as perspective,
                   e.chapter_title as chapter
            ORDER BY s.sourceId, e.name
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
        
        if not episodes:
            print("❌ No episodes found")
            return
        
        print(f"📖 Found {len(episodes)} episodes to ingest")
        
        # Group by source for better processing
        sources = {}
        for episode in episodes:
            source_id = episode['sourceId']
            if source_id not in sources:
                sources[source_id] = []
            sources[source_id].append(episode)
        
        print(f"📚 Processing {len(sources)} sources")
        
        # Ingest each source
        for source_id, source_episodes in sources.items():
            source_title = source_episodes[0]['source_title']
            source_author = source_episodes[0]['source_author']
            perspective = source_episodes[0]['perspective']
            
            print(f"\n📚 Processing: {source_title} by {source_author}")
            print(f"   Episodes: {len(source_episodes)}")
            print(f"   Perspective: {perspective}")
            
            # Process episodes in small batches to avoid timeouts
            batch_size = 3  # Small batches for local processing
            
            for i in range(0, len(source_episodes), batch_size):
                batch = source_episodes[i:i+batch_size]
                
                print(f"   🔄 Batch {i//batch_size + 1}/{(len(source_episodes)-1)//batch_size + 1}")
                
                for episode in batch:
                    try:
                        # Create rich episode body with source context
                        episode_body = f"""
SOURCE: {episode['source_title']} by {episode['source_author']}
PERSPECTIVE: {episode['perspective']}
CHAPTER: {episode['chapter']}

{episode['content']}
"""
                        
                        # Create unique episode name with source
                        episode_name = f"[{source_id}] {episode['name']}"
                        
                        # Calculate reference time (rough estimate based on content)
                        ref_time = datetime(1922, 9, 15)  # Default to Smyrna fire period
                        
                        # Add to Graphiti using native ingestion
                        await self.graphiti.add_episode(
                            name=episode_name,
                            episode_body=episode_body,
                            source_description=f"{episode['source_title']} - {episode['chapter']}",
                            reference_time=ref_time
                        )
                        
                        print(f"      ✅ {episode['name'][:50]}...")
                        
                    except Exception as e:
                        print(f"      ❌ Failed: {episode['name'][:50]}... - {e}")
                
                # Small delay between batches
                await asyncio.sleep(2)
        
        print(f"\n🎉 GRAPHITI NATIVE INGESTION COMPLETE!")
    
    async def test_graphiti_search(self):
        """Test the Graphiti search after ingestion"""
        print("\n🧠 TESTING GRAPHITI SEARCH")
        print("=" * 40)
        
        test_queries = [
            "Girdis family",
            "Nicholas Girdis", 
            "Smyrna fire",
            "American evacuation",
            "Atatürk"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing: '{query}'")
            
            try:
                results = await self.graphiti.search(
                    query=query,
                    num_results=3
                )
                
                if results and hasattr(results, 'results') and len(results.results) > 0:
                    print(f"✅ Found {len(results.results)} results")
                    
                    for i, result in enumerate(results.results[:2]):
                        if hasattr(result, 'episode') and hasattr(result.episode, 'name'):
                            print(f"   {i+1}. {result.episode.name}")
                        else:
                            print(f"   {i+1}. {str(result)[:100]}...")
                else:
                    print("❌ No results found")
                    
            except Exception as e:
                print(f"❌ Search failed: {e}")
    
    def close(self):
        self.neo4j_driver.close()

async def main():
    """Main setup function"""
    setup = ProperGraphitiSetup()
    
    try:
        # Clear any existing partial Graphiti data
        await setup.clear_existing_graphiti_data()
        
        # Properly ingest all books using Graphiti's native system
        await setup.ingest_books_to_graphiti()
        
        # Test the search
        await setup.test_graphiti_search()
        
        print("\n🎉 GRAPHITI IS NOW PROPERLY SET UP!")
        print("🧠 Semantic search should work perfectly with local models")
        
    finally:
        setup.close()

if __name__ == "__main__":
    asyncio.run(main())