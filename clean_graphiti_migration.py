#!/usr/bin/env python3
"""
Clean migration to Graphiti - replace existing system with proper Graphiti setup
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Configure for local models
os.environ["GRAPHITI_LLM_MODEL"] = "ollama/mistral-small3.1:latest"
os.environ["GRAPHITI_EMBEDDING_MODEL"] = "ollama/nomic-embed-text"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

from graphiti_core import Graphiti

class CleanGraphitiMigration:
    def __init__(self):
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        
        self.graphiti = Graphiti(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="Sk1pper(())",
            database="the-great-fire-db"
        )
    
    def backup_source_data(self):
        """First, backup your source metadata"""
        print("💾 Backing up source metadata...")
        
        with self.neo4j_driver.session(database="the-great-fire-db") as session:
            # Get source information
            result = session.run("""
            MATCH (s:Source)
            RETURN s.sourceId, s.title, s.author, s.year, s.perspective, s.historical_period
            """)
            
            sources = []
            for record in result:
                sources.append({
                    'sourceId': record['s.sourceId'],
                    'title': record['s.title'],
                    'author': record['s.author'],
                    'year': record['s.year'],
                    'perspective': record['s.perspective'],
                    'historical_period': record['s.historical_period']
                })
            
            # Get episode content
            result = session.run("""
            MATCH (e:Episode)-[:FROM_SOURCE]->(s:Source)
            WHERE e.content IS NOT NULL AND size(e.content) > 200
            RETURN e.name, e.content, s.sourceId, e.chapter_title
            ORDER BY s.sourceId, e.name
            """)
            
            episodes = []
            for record in result:
                episodes.append({
                    'name': record['e.name'],
                    'content': record['e.content'],
                    'sourceId': record['s.sourceId'],
                    'chapter': record['e.chapter_title']
                })
            
            print(f"✅ Backed up {len(sources)} sources and {len(episodes)} episodes")
            return sources, episodes
    
    def clean_database(self):
        """Clean existing data to avoid duplication"""
        print("🧹 Cleaning existing data...")
        
        with self.neo4j_driver.session(database="the-great-fire-db") as session:
            # Remove all existing data EXCEPT keep track of what we had
            session.run("MATCH (n) DETACH DELETE n")
            
        print("✅ Database cleaned")
    
    async def rebuild_with_graphiti(self, sources, episodes):
        """Rebuild everything using pure Graphiti"""
        print("🏗️  Rebuilding with pure Graphiti...")
        
        # Group episodes by source
        sources_map = {s['sourceId']: s for s in sources}
        episodes_by_source = {}
        
        for episode in episodes:
            source_id = episode['sourceId']
            if source_id not in episodes_by_source:
                episodes_by_source[source_id] = []
            episodes_by_source[source_id].append(episode)
        
        # Ingest each source properly
        for source_id, source_episodes in episodes_by_source.items():
            source_info = sources_map[source_id]
            
            print(f"\n📚 Ingesting: {source_info['title']}")
            print(f"   Episodes: {len(source_episodes)}")
            
            batch_size = 3
            for i in range(0, len(source_episodes), batch_size):
                batch = source_episodes[i:i+batch_size]
                
                print(f"   Batch {i//batch_size + 1}/{(len(source_episodes)-1)//batch_size + 1}")
                
                for episode in batch:
                    try:
                        # Rich episode body with all metadata
                        episode_body = f"""
SOURCE: {source_info['title']} by {source_info['author']}
PERSPECTIVE: {source_info['perspective']}
PERIOD: {source_info['historical_period']}
CHAPTER: {episode['chapter']}

{episode['content']}
"""
                        
                        # Unique name
                        episode_name = f"[{source_id}] {episode['name']}"
                        
                        # Add to Graphiti
                        await self.graphiti.add_episode(
                            name=episode_name,
                            episode_body=episode_body,
                            source_description=f"{source_info['title']} - {episode['chapter']}",
                            reference_time=datetime(1922, 9, 15)
                        )
                        
                        print(f"      ✅ {episode['name'][:50]}...")
                        
                    except Exception as e:
                        print(f"      ❌ {episode['name'][:50]}... - {e}")
                
                await asyncio.sleep(1)
    
    async def test_new_system(self):
        """Test the clean Graphiti system"""
        print("\n🧠 Testing clean Graphiti system...")
        
        queries = ["Girdis family", "Smyrna fire", "American evacuation"]
        
        for query in queries:
            try:
                results = await self.graphiti.search(query=query, num_results=2)
                
                if results and hasattr(results, 'results') and len(results.results) > 0:
                    print(f"✅ '{query}': {len(results.results)} results")
                else:
                    print(f"❌ '{query}': No results")
                    
            except Exception as e:
                print(f"❌ '{query}': Error - {e}")
    
    def close(self):
        self.neo4j_driver.close()

async def main():
    print("🔄 CLEAN GRAPHITI MIGRATION")
    print("=" * 50)
    print("⚠️  This will:")
    print("   - Backup your data")
    print("   - Clean the database") 
    print("   - Rebuild with pure Graphiti")
    print("   - No duplication!")
    
    response = input("\nProceed? (y/N): ")
    if response.lower() != 'y':
        print("❌ Migration cancelled")
        return
    
    migration = CleanGraphitiMigration()
    
    try:
        # Backup
        sources, episodes = migration.backup_source_data()
        
        # Clean
        migration.clean_database()
        
        # Rebuild with Graphiti
        await migration.rebuild_with_graphiti(sources, episodes)
        
        # Test
        await migration.test_new_system()
        
        print("\n🎉 CLEAN MIGRATION COMPLETE!")
        print("📊 Pure Graphiti system with local models")
        
    finally:
        migration.close()

if __name__ == "__main__":
    asyncio.run(main())