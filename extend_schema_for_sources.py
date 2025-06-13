#!/usr/bin/env python3
"""
Extend existing Neo4j schema to support multiple book sources
WITHOUT requiring re-ingestion of existing data
"""

from neo4j import GraphDatabase
from datetime import datetime
import re

class SourceSchemaExtender:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
    
    def extend_schema(self):
        """Extend schema to support multiple sources"""
        with self.driver.session(database="the-great-fire-db") as session:
            
            print("🏗️  EXTENDING SCHEMA FOR MULTI-BOOK SUPPORT")
            print("=" * 50)
            
            # 1. Create Source node for current data
            print("📚 Creating Source node for 'The Great Fire of Smyrna'...")
            session.run("""
            MERGE (s:Source {
                sourceId: "great-fire-smyrna-1922",
                title: "The Great Fire of Smyrna", 
                author: "Lou Ureneck",
                year: 2015,
                isbn: "9780062259103",
                publisher: "Ecco",
                perspective: "American journalist perspective",
                language: "English",
                historical_period: "1922 Greek-Turkish War",
                created_at: datetime()
            })
            """)
            
            # 2. Create Chapter nodes linked to Source
            print("📖 Creating Chapter nodes and linking to Source...")
            result = session.run("""
            MATCH (e:Episode)
            WHERE e.chapter_title IS NOT NULL AND e.chapter_number IS NOT NULL
            RETURN DISTINCT e.chapter_number as number, e.chapter_title as title, e.chapter_sequence as sequence
            ORDER BY e.chapter_number
            """)
            
            chapters = []
            for record in result:
                chapters.append({
                    'number': record['number'],
                    'title': record['title'], 
                    'sequence': record['sequence']
                })
            
            for chapter in chapters:
                session.run("""
                MATCH (s:Source {sourceId: "great-fire-smyrna-1922"})
                MERGE (c:Chapter {
                    chapterId: "great-fire-smyrna-ch" + $number,
                    number: $number,
                    title: $title,
                    sequence: $sequence,
                    sourceId: "great-fire-smyrna-1922"
                })
                MERGE (s)-[:HAS_CHAPTER]->(c)
                """, number=str(chapter['number']), title=chapter['title'], sequence=chapter['sequence'])
            
            print(f"✅ Created {len(chapters)} Chapter nodes")
            
            # 3. Link existing Episodes to Source and Chapters
            print("🔗 Linking Episodes to Source and Chapters...")
            session.run("""
            MATCH (e:Episode), (s:Source {sourceId: "great-fire-smyrna-1922"})
            MERGE (e)-[:FROM_SOURCE]->(s)
            
            WITH e, s
            MATCH (c:Chapter {sourceId: "great-fire-smyrna-1922"})
            WHERE c.number = e.chapter_number
            MERGE (e)-[:IN_CHAPTER]->(c)
            """)
            
            # 4. Add source metadata to all existing entities
            print("🏷️  Adding source metadata to existing entities...")
            session.run("""
            MATCH (entity:Entity)
            SET entity.sourceId = "great-fire-smyrna-1922",
                entity.source_added_at = datetime()
            """)
            
            # 5. Add source context to relationships
            print("🔗 Adding source context to relationships...")
            session.run("""
            MATCH ()-[r:RELATES_TO]->()
            SET r.sourceId = "great-fire-smyrna-1922",
                r.source_context = "From: The Great Fire of Smyrna by Lou Ureneck"
            """)
            
            session.run("""
            MATCH ()-[r:MENTIONS]->()
            SET r.sourceId = "great-fire-smyrna-1922"
            """)
            
            # 6. Create indexes for efficient source queries
            print("📇 Creating indexes for source queries...")
            
            # Source node index
            session.run("CREATE INDEX source_id IF NOT EXISTS FOR (s:Source) ON (s.sourceId)")
            session.run("CREATE INDEX source_title IF NOT EXISTS FOR (s:Source) ON (s.title)")
            
            # Chapter indexes  
            session.run("CREATE INDEX chapter_id IF NOT EXISTS FOR (c:Chapter) ON (c.chapterId)")
            session.run("CREATE INDEX chapter_source IF NOT EXISTS FOR (c:Chapter) ON (c.sourceId)")
            
            # Entity source indexes
            session.run("CREATE INDEX entity_source IF NOT EXISTS FOR (e:Entity) ON (e.sourceId)")
            
            # Relationship source indexes
            session.run("CREATE INDEX relates_source IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.sourceId)")
            session.run("CREATE INDEX mentions_source IF NOT EXISTS FOR ()-[r:MENTIONS]-() ON (r.sourceId)")
            
            print("✅ Schema extension complete!")
            
    def create_entity_aliases_framework(self):
        """Create framework for cross-book entity resolution"""
        with self.driver.session(database="the-great-fire-db") as session:
            
            print("\n🔄 CREATING ENTITY ALIAS FRAMEWORK")
            print("=" * 40)
            
            # Create CanonicalEntity nodes for major characters
            print("👥 Creating canonical entities for major characters...")
            
            major_characters = [
                {"name": "Asa Kent Jennings", "aliases": ["Asa Jennings", "A.K. Jennings", "Jennings"]},
                {"name": "Mustafa Kemal Atatürk", "aliases": ["Atatürk", "Kemal", "Mustafa Kemal"]},
                {"name": "Mark Lambert Bristol", "aliases": ["Admiral Bristol", "Bristol", "Mark Bristol"]},
                {"name": "George Horton", "aliases": ["Horton", "Consul Horton"]},
            ]
            
            for character in major_characters:
                # Create canonical entity
                session.run("""
                MERGE (ce:CanonicalEntity {
                    canonicalName: $name,
                    entityType: "Person",
                    created_at: datetime()
                })
                """, name=character['name'])
                
                # Link existing entities as interpretations
                for alias in character['aliases']:
                    session.run("""
                    MATCH (ce:CanonicalEntity {canonicalName: $canonical})
                    MATCH (e:Entity)
                    WHERE toLower(e.name) CONTAINS toLower($alias)
                    MERGE (e)-[:INTERPRETS_AS]->(ce)
                    SET e.canonicalName = $canonical
                    """, canonical=character['name'], alias=alias)
            
            print("✅ Canonical entity framework created")
            
    def verify_extension(self):
        """Verify the schema extension worked correctly"""
        with self.driver.session(database="the-great-fire-db") as session:
            
            print("\n✅ VERIFICATION RESULTS")
            print("=" * 30)
            
            # Check Source node
            result = session.run("MATCH (s:Source) RETURN s.title, s.author, s.sourceId")
            for record in result:
                print(f"📚 Source: {record['s.title']} by {record['s.author']} (ID: {record['s.sourceId']})")
            
            # Check Chapter counts
            result = session.run("MATCH (s:Source)-[:HAS_CHAPTER]->(c:Chapter) RETURN s.sourceId, count(c) as chapters")
            for record in result:
                print(f"📖 {record['s.sourceId']}: {record['chapters']} chapters")
            
            # Check Episode links
            result = session.run("MATCH (e:Episode)-[:FROM_SOURCE]->(s:Source) RETURN s.sourceId, count(e) as episodes")
            for record in result:
                print(f"📄 {record['s.sourceId']}: {record['episodes']} episodes linked")
            
            # Check entity source tracking
            result = session.run("MATCH (e:Entity) WHERE e.sourceId IS NOT NULL RETURN count(e) as tagged_entities")
            for record in result:
                print(f"🏷️  {record['tagged_entities']} entities tagged with source")
            
            # Check relationship source tracking
            result = session.run("MATCH ()-[r:RELATES_TO]->() WHERE r.sourceId IS NOT NULL RETURN count(r) as tagged_rels")
            for record in result:
                print(f"🔗 {record['tagged_rels']} relationships tagged with source")
                
            print("\n🎉 Schema successfully extended for multi-book support!")
            print("🔄 You can now add additional books without re-ingesting existing data")

    def close(self):
        self.driver.close()

if __name__ == "__main__":
    extender = SourceSchemaExtender()
    try:
        extender.extend_schema()
        extender.create_entity_aliases_framework()
        extender.verify_extension()
    finally:
        extender.close()