#!/usr/bin/env python3
"""
Migrate existing Neo4j Great Fire of Smyrna data into Graphiti format
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

class GraphitiIngester:
    def __init__(self):
        # Neo4j connection for reading existing data
        self.neo4j_driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD"))
        )
        
        # Graphiti connection for writing semantic data
        self.graphiti = Graphiti(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD")
        )
        
    async def ingest_episodes(self):
        """Ingest Neo4j episodes into Graphiti format"""
        print("📚 Reading episodes from Neo4j...")
        
        with self.neo4j_driver.session(database="the-great-fire-db") as session:
            # Get all episodes with their metadata
            query = """
            MATCH (e:Episode)
            RETURN e.name as name, e.content as content, 
                   e.chapter_sequence as sequence, e.chapter_title as chapter,
                   e.story_arc_position as position, e.narrative_importance as importance
            ORDER BY e.chapter_sequence
            """
            
            result = session.run(query)
            episodes = []
            
            for record in result:
                episodes.append({
                    "name": record["name"],
                    "content": record["content"],
                    "sequence": record["sequence"],
                    "chapter": record["chapter"],
                    "position": record["position"],
                    "importance": record["importance"]
                })
        
        print(f"📖 Found {len(episodes)} episodes to ingest")
        
        # Ingest episodes into Graphiti
        for i, episode in enumerate(episodes, 1):
            print(f"🔄 Ingesting episode {i}/{len(episodes)}: {episode['name']}")
            
            try:
                # Create reference time based on sequence 
                ref_time = datetime(1922, 9, 1)  # Great Fire was September 1922
                if episode['sequence']:
                    # Add days based on chapter sequence
                    ref_time = datetime(1922, 9, int(episode['sequence']))
                
                # Build rich episode body with metadata
                episode_body = f"""Chapter: {episode['chapter']}
Story Position: {episode['position']}
Narrative Importance: {episode['importance']}

Content: {episode['content']}"""
                
                # Ingest into Graphiti
                await self.graphiti.add_episode(
                    name=episode['name'],
                    episode_body=episode_body,
                    source_description=f"The Great Fire of Smyrna - {episode['chapter']}",
                    reference_time=ref_time
                )
                
                print(f"✅ Ingested: {episode['name']}")
                
            except Exception as e:
                print(f"❌ Failed to ingest {episode['name']}: {e}")
        
        print("🎉 Episode ingestion complete!")
    
    async def ingest_characters(self):
        """Ingest character profiles as episodes"""
        print("👥 Reading character profiles from Neo4j...")
        
        with self.neo4j_driver.session(database="the-great-fire-db") as session:
            query = """
            MATCH (c:Character)
            OPTIONAL MATCH (c)-[r:RELATES_TO]-(other)
            RETURN c, collect({other: other.name, relationship: r.type, context: r.narrative_context}) as relationships
            """
            
            result = session.run(query)
            characters = []
            
            for record in result:
                char = dict(record["c"])
                relationships = record["relationships"]
                characters.append({"character": char, "relationships": relationships})
        
        print(f"👤 Found {len(characters)} characters to ingest")
        
        for i, char_data in enumerate(characters, 1):
            char = char_data["character"]
            relationships = char_data["relationships"]
            
            print(f"🔄 Ingesting character {i}/{len(characters)}: {char.get('name', 'Unknown')}")
            
            try:
                # Build character profile with relationships
                char_body = f"""Character Profile: {char.get('name', 'Unknown')}
Role: {char.get('role', 'Unknown')}
Nationality: {char.get('nationality', 'Unknown')}
Historical Significance: {char.get('significance', 'N/A')}
Motivations: {char.get('motivations', 'N/A')}
Character Development: {char.get('development', 'N/A')}

Key Relationships:"""
                
                for rel in relationships[:5]:  # Top 5 relationships
                    if rel['other']:
                        char_body += f"\n- {rel['other']}: {rel.get('context', 'Connected')}"
                
                await self.graphiti.add_episode(
                    name=f"Character Profile: {char.get('name', 'Unknown')}",
                    episode_body=char_body,
                    source_description="Character profiles from The Great Fire of Smyrna",
                    reference_time=datetime(1922, 9, 15)  # Mid-crisis date
                )
                
                print(f"✅ Ingested character: {char.get('name', 'Unknown')}")
                
            except Exception as e:
                print(f"❌ Failed to ingest character {char.get('name', 'Unknown')}: {e}")
        
        print("🎉 Character ingestion complete!")
    
    async def ingest_events(self):
        """Ingest major events as episodes"""
        print("📅 Reading events from Neo4j...")
        
        with self.neo4j_driver.session(database="the-great-fire-db") as session:
            query = """
            MATCH (e:Event)
            RETURN e
            ORDER BY e.name
            """
            
            result = session.run(query)
            events = [dict(record["e"]) for record in result]
        
        print(f"📅 Found {len(events)} events to ingest")
        
        for i, event in enumerate(events, 1):
            print(f"🔄 Ingesting event {i}/{len(events)}: {event.get('name', 'Unknown')}")
            
            try:
                event_body = f"""Historical Event: {event.get('name', 'Unknown')}
Narrative Function: {event.get('narrative_function', 'N/A')}
Participants: {event.get('participants', 'N/A')}
Consequences: {event.get('consequences', 'N/A')}
Story Turning Point: {event.get('story_turning_point', 'No')}
Date: {event.get('date_mentioned', 'Unknown')}"""
                
                await self.graphiti.add_episode(
                    name=f"Event: {event.get('name', 'Unknown')}",
                    episode_body=event_body,
                    source_description="Historical events from The Great Fire of Smyrna",
                    reference_time=datetime(1922, 9, 13)  # Fire peak date
                )
                
                print(f"✅ Ingested event: {event.get('name', 'Unknown')}")
                
            except Exception as e:
                print(f"❌ Failed to ingest event {event.get('name', 'Unknown')}: {e}")
        
        print("🎉 Event ingestion complete!")
    
    def close(self):
        self.neo4j_driver.close()

async def main():
    print("🚀 Starting Graphiti ingestion for Great Fire of Smyrna data")
    print("=" * 60)
    
    ingester = GraphitiIngester()
    
    try:
        # Ingest all data types
        await ingester.ingest_episodes()
        await ingester.ingest_characters() 
        await ingester.ingest_events()
        
        print("\n🎉 ALL INGESTION COMPLETE!")
        print("📊 Graphiti now has semantic embeddings for:")
        print("   • Episode content with narrative context")
        print("   • Character profiles with relationships")
        print("   • Historical events with consequences")
        print("\n✨ Your hybrid system can now use semantic search!")
        
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ingester.close()

if __name__ == "__main__":
    asyncio.run(main())