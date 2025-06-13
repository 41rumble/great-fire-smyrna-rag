#!/usr/bin/env python3
"""
Enhanced Graphiti ingestion for multi-source data
Works with the new source-aware schema
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

class MultiSourceGraphitiIngester:
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
        
    async def ingest_episodes_by_source(self, source_id: str = None):
        """Ingest episodes into Graphiti with source tracking"""
        print("📚 Reading episodes from Neo4j with source information...")
        
        with self.neo4j_driver.session(database="the-great-fire-db") as session:
            # Get episodes with source context
            if source_id:
                query = """
                MATCH (e:Episode)-[:FROM_SOURCE]->(s:Source {sourceId: $sourceId})
                MATCH (e)-[:IN_CHAPTER]->(c:Chapter)
                RETURN e.name as name, e.content as content, 
                       e.chapter_sequence as sequence, e.chapter_title as chapter,
                       e.story_arc_position as position, e.narrative_importance as importance,
                       s.title as source_title, s.author as source_author, s.sourceId as sourceId,
                       c.title as chapter_title, c.number as chapter_number
                ORDER BY c.number, e.chunk_number
                """
                result = session.run(query, sourceId=source_id)
            else:
                # Get all episodes with source info
                query = """
                MATCH (e:Episode)-[:FROM_SOURCE]->(s:Source)
                OPTIONAL MATCH (e)-[:IN_CHAPTER]->(c:Chapter)
                RETURN e.name as name, e.content as content, 
                       e.chapter_sequence as sequence, e.chapter_title as chapter,
                       e.story_arc_position as position, e.narrative_importance as importance,
                       s.title as source_title, s.author as source_author, s.sourceId as sourceId,
                       c.title as chapter_title, c.number as chapter_number
                ORDER BY s.sourceId, coalesce(c.number, e.chapter_sequence)
                """
                result = session.run(query)
            
            episodes = []
            for record in result:
                episodes.append({
                    "name": record["name"],
                    "content": record["content"],
                    "sequence": record["sequence"],
                    "chapter": record["chapter"] or record["chapter_title"],
                    "position": record["position"],
                    "importance": record["importance"],
                    "source_title": record["source_title"],
                    "source_author": record["source_author"],
                    "sourceId": record["sourceId"],
                    "chapter_number": record["chapter_number"]
                })
        
        if not episodes:
            print("❌ No episodes found to ingest")
            return
            
        print(f"📖 Found {len(episodes)} episodes to ingest")
        
        # Group episodes by source for better organization
        sources = {}
        for episode in episodes:
            source_id = episode['sourceId']
            if source_id not in sources:
                sources[source_id] = []
            sources[source_id].append(episode)
        
        print(f"📚 Processing {len(sources)} sources")
        
        # Ingest episodes by source
        for source_id, source_episodes in sources.items():
            print(f"\n🔄 Processing source: {source_episodes[0]['source_title']}")
            
            for i, episode in enumerate(source_episodes, 1):
                print(f"  📄 Ingesting episode {i}/{len(source_episodes)}: {episode['name']}")
                
                try:
                    # Create reference time based on sequence 
                    ref_time = datetime(1922, 9, 1)  # Default to Great Fire period
                    if episode['chapter_number']:
                        # Add days based on chapter sequence
                        ref_time = datetime(1922, 9, min(30, int(episode['chapter_number'])))
                    
                    # Build rich episode body with source metadata
                    episode_body = f"""Source: {episode['source_title']} by {episode['source_author']}
Chapter: {episode['chapter']}
Story Position: {episode['position'] or 'N/A'}
Narrative Importance: {episode['importance'] or 'medium'}

Content: {episode['content']}"""
                    
                    # Enhanced source description with provenance
                    source_description = f"{episode['source_title']} by {episode['source_author']} - {episode['chapter']}"
                    
                    # Ingest into Graphiti with source tracking
                    await self.graphiti.add_episode(
                        name=f"[{episode['sourceId']}] {episode['name']}",
                        episode_body=episode_body,
                        source_description=source_description,
                        reference_time=ref_time
                    )
                    
                    print(f"    ✅ Success: {episode['name']}")
                    
                except Exception as e:
                    print(f"    ❌ Failed: {episode['name']} - {e}")
        
        print("🎉 Multi-source episode ingestion complete!")
    
    async def ingest_entities_by_source(self, source_id: str = None):
        """Ingest entities with source context"""
        print(f"👥 Reading entities from Neo4j (source: {source_id or 'all'})...")
        
        with self.neo4j_driver.session(database="the-great-fire-db") as session:
            if source_id:
                query = """
                MATCH (entity:Entity {sourceId: $sourceId})
                MATCH (entity)<-[:MENTIONS]-(e:Episode)-[:FROM_SOURCE]->(s:Source)
                RETURN entity.name as name, entity.entity_type as type,
                       entity.role as role, entity.significance as significance,
                       s.title as source_title, s.author as source_author,
                       entity.sourceId as sourceId,
                       collect(DISTINCT e.chapter_title) as chapters
                """
                result = session.run(query, sourceId=source_id)
            else:
                query = """
                MATCH (entity:Entity)
                WHERE entity.sourceId IS NOT NULL
                MATCH (entity)<-[:MENTIONS]-(e:Episode)-[:FROM_SOURCE]->(s:Source)
                RETURN entity.name as name, entity.entity_type as type,
                       entity.role as role, entity.significance as significance,
                       s.title as source_title, s.author as source_author,
                       entity.sourceId as sourceId,
                       collect(DISTINCT e.chapter_title) as chapters
                """
                result = session.run(query)
            
            entities = []
            for record in result:
                entities.append({
                    "name": record["name"],
                    "type": record["type"],
                    "role": record["role"],
                    "significance": record["significance"],
                    "source_title": record["source_title"],
                    "source_author": record["source_author"],
                    "sourceId": record["sourceId"],
                    "chapters": record["chapters"]
                })
        
        print(f"👥 Found {len(entities)} entities with source information")
        
        # Ingest entities with source context
        for i, entity in enumerate(entities, 1):
            print(f"🔄 Processing entity {i}/{len(entities)}: {entity['name']}")
            
            try:
                # Build entity description with source context
                entity_description = f"""Entity: {entity['name']}
Type: {entity['type']}
Role: {entity['role'] or 'N/A'}
Significance: {entity['significance'] or 'N/A'}
Source: {entity['source_title']} by {entity['source_author']}
Appears in chapters: {', '.join(entity['chapters'][:5])}"""
                
                # Add to Graphiti as a fact
                await self.graphiti.add_episode(
                    name=f"[Entity] {entity['name']} in {entity['sourceId']}",
                    episode_body=entity_description,
                    source_description=f"{entity['source_title']} - Entity Profile",
                    reference_time=datetime(1922, 9, 15)  # Default reference time
                )
                
                print(f"  ✅ Added: {entity['name']}")
                
            except Exception as e:
                print(f"  ❌ Failed: {entity['name']} - {e}")
        
        print("🎉 Entity ingestion complete!")
    
    async def ingest_relationships_by_source(self, source_id: str = None):
        """Ingest relationships with source provenance"""
        print(f"🔗 Reading relationships from Neo4j (source: {source_id or 'all'})...")
        
        with self.neo4j_driver.session(database="the-great-fire-db") as session:
            if source_id:
                query = """
                MATCH (a:Entity)-[r:RELATES_TO]->(b:Entity)
                WHERE r.sourceId = $sourceId
                MATCH (a)<-[:MENTIONS]-(e:Episode)-[:FROM_SOURCE]->(s:Source {sourceId: $sourceId})
                RETURN a.name as from_entity, b.name as to_entity,
                       r.type as rel_type, r.narrative_context as context,
                       r.evidence as evidence, r.chapter as chapter,
                       s.title as source_title, s.author as source_author,
                       r.sourceId as sourceId
                LIMIT 100
                """
                result = session.run(query, sourceId=source_id)
            else:
                query = """
                MATCH (a:Entity)-[r:RELATES_TO]->(b:Entity)
                WHERE r.sourceId IS NOT NULL
                MATCH (a)<-[:MENTIONS]-(e:Episode)-[:FROM_SOURCE]->(s:Source)
                WHERE s.sourceId = r.sourceId
                RETURN a.name as from_entity, b.name as to_entity,
                       r.type as rel_type, r.narrative_context as context,
                       r.evidence as evidence, r.chapter as chapter,
                       s.title as source_title, s.author as source_author,
                       r.sourceId as sourceId
                LIMIT 200
                """
                result = session.run(query)
            
            relationships = []
            for record in result:
                relationships.append({
                    "from_entity": record["from_entity"],
                    "to_entity": record["to_entity"],
                    "rel_type": record["rel_type"],
                    "context": record["context"],
                    "evidence": record["evidence"],
                    "chapter": record["chapter"],
                    "source_title": record["source_title"],
                    "source_author": record["source_author"],
                    "sourceId": record["sourceId"]
                })
        
        print(f"🔗 Found {len(relationships)} relationships with source information")
        
        # Ingest relationships as episodes
        for i, rel in enumerate(relationships, 1):
            print(f"🔄 Processing relationship {i}/{len(relationships)}: {rel['from_entity']} -> {rel['to_entity']}")
            
            try:
                # Build relationship description
                rel_description = f"""Relationship: {rel['from_entity']} {rel['rel_type']} {rel['to_entity']}
Context: {rel['context'] or 'N/A'}
Evidence: {rel['evidence'][:200] if rel['evidence'] else 'N/A'}...
Chapter: {rel['chapter']}
Source: {rel['source_title']} by {rel['source_author']}"""
                
                await self.graphiti.add_episode(
                    name=f"[Relationship] {rel['from_entity']} -> {rel['to_entity']} ({rel['sourceId']})",
                    episode_body=rel_description,
                    source_description=f"{rel['source_title']} - {rel['chapter']} - Relationship",
                    reference_time=datetime(1922, 9, 10)
                )
                
                print(f"  ✅ Added relationship")
                
            except Exception as e:
                print(f"  ❌ Failed relationship - {e}")
        
        print("🎉 Relationship ingestion complete!")
    
    async def full_multi_source_ingest(self, source_id: str = None):
        """Complete ingestion of episodes, entities, and relationships"""
        print("🚀 STARTING FULL MULTI-SOURCE GRAPHITI INGESTION")
        print("=" * 60)
        
        try:
            # Ingest episodes with source tracking
            await self.ingest_episodes_by_source(source_id)
            
            # Ingest entities with source context
            await self.ingest_entities_by_source(source_id)
            
            # Ingest relationships with provenance
            await self.ingest_relationships_by_source(source_id)
            
            print("\n🎉 MULTI-SOURCE GRAPHITI INGESTION COMPLETE!")
            print("🔍 Your semantic search now includes source provenance")
            
        except Exception as e:
            print(f"❌ Ingestion failed: {e}")
    
    def close(self):
        self.neo4j_driver.close()

async def main():
    """Main ingestion function"""
    ingester = MultiSourceGraphitiIngester()
    
    try:
        # Option 1: Ingest all sources
        await ingester.full_multi_source_ingest()
        
        # Option 2: Ingest specific source only
        # await ingester.full_multi_source_ingest("great-fire-smyrna-1922")
        
    finally:
        ingester.close()

if __name__ == "__main__":
    asyncio.run(main())