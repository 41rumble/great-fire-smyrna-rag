#!/usr/bin/env python3
"""
Source-aware query examples for the multi-book system
Demonstrates how to query with source provenance
"""

from neo4j import GraphDatabase
from typing import List, Dict, Any

class SourceAwareQueries:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
    
    def list_all_sources(self) -> List[Dict]:
        """List all books/sources in the database"""
        with self.driver.session(database="the-great-fire-db") as session:
            query = """
            MATCH (s:Source)
            OPTIONAL MATCH (s)-[:HAS_CHAPTER]->(c:Chapter)
            OPTIONAL MATCH (e:Episode)-[:FROM_SOURCE]->(s)
            RETURN s.title as title, s.author as author, s.year as year,
                   s.sourceId as sourceId, s.perspective as perspective,
                   count(DISTINCT c) as chapters, count(DISTINCT e) as episodes
            ORDER BY s.year, s.title
            """
            
            result = session.run(query)
            sources = []
            for record in result:
                sources.append({
                    'title': record['title'],
                    'author': record['author'],
                    'year': record['year'],
                    'sourceId': record['sourceId'],
                    'perspective': record['perspective'],
                    'chapters': record['chapters'],
                    'episodes': record['episodes']
                })
            
            return sources
    
    def compare_entity_across_sources(self, entity_name: str) -> Dict[str, List]:
        """Compare how different sources describe the same entity"""
        with self.driver.session(database="the-great-fire-db") as session:
            query = """
            MATCH (e:Entity)
            WHERE toLower(e.name) CONTAINS toLower($entity_name)
            MATCH (e)<-[:MENTIONS]-(ep:Episode)-[:FROM_SOURCE]->(s:Source)
            WITH e, s, collect(DISTINCT ep.chapter_title) as chapters
            RETURN e.name as entity_name, e.role as role, e.significance as significance,
                   s.title as source_title, s.author as source_author, s.perspective as perspective,
                   e.sourceId as sourceId, chapters
            ORDER BY s.year, s.title
            """
            
            result = session.run(query, entity_name=entity_name)
            
            by_source = {}
            for record in result:
                source = record['source_title']
                if source not in by_source:
                    by_source[source] = []
                
                by_source[source].append({
                    'entity_name': record['entity_name'],
                    'role': record['role'],
                    'significance': record['significance'],
                    'author': record['source_author'],
                    'perspective': record['perspective'],
                    'sourceId': record['sourceId'],
                    'chapters': record['chapters']
                })
            
            return by_source
    
    def find_unique_to_source(self, source_id: str) -> Dict[str, List]:
        """Find entities/events unique to a specific source"""
        with self.driver.session(database="the-great-fire-db") as session:
            query = """
            MATCH (e:Entity {sourceId: $sourceId})
            WHERE NOT EXISTS {
                MATCH (other:Entity)
                WHERE other.sourceId <> $sourceId 
                AND (toLower(other.name) = toLower(e.name) 
                     OR toLower(other.name) CONTAINS toLower(e.name)
                     OR toLower(e.name) CONTAINS toLower(other.name))
            }
            MATCH (s:Source {sourceId: $sourceId})
            RETURN e.name as name, e.entity_type as type, e.role as role,
                   s.title as source_title
            ORDER BY e.entity_type, e.name
            """
            
            result = session.run(query, sourceId=source_id)
            
            unique_entities = {}
            for record in result:
                entity_type = record['type'] or 'Unknown'
                if entity_type not in unique_entities:
                    unique_entities[entity_type] = []
                
                unique_entities[entity_type].append({
                    'name': record['name'],
                    'role': record['role'],
                    'source_title': record['source_title']
                })
            
            return unique_entities
    
    def find_conflicting_accounts(self, entity_name: str) -> List[Dict]:
        """Find conflicting accounts of the same entity across sources"""
        with self.driver.session(database="the-great-fire-db") as session:
            query = """
            MATCH (e1:Entity)-[r1:RELATES_TO]->(target:Entity)
            MATCH (e2:Entity)-[r2:RELATES_TO]->(target)
            WHERE toLower(target.name) CONTAINS toLower($entity_name)
            AND r1.sourceId <> r2.sourceId
            AND r1.type <> r2.type
            MATCH (s1:Source {sourceId: r1.sourceId})
            MATCH (s2:Source {sourceId: r2.sourceId})
            RETURN target.name as target_entity,
                   e1.name as from_entity1, r1.type as relationship1, s1.title as source1,
                   e2.name as from_entity2, r2.type as relationship2, s2.title as source2,
                   r1.evidence as evidence1, r2.evidence as evidence2
            LIMIT 10
            """
            
            result = session.run(query, entity_name=entity_name)
            
            conflicts = []
            for record in result:
                conflicts.append({
                    'target_entity': record['target_entity'],
                    'account1': {
                        'from_entity': record['from_entity1'],
                        'relationship': record['relationship1'],
                        'source': record['source1'],
                        'evidence': record['evidence1']
                    },
                    'account2': {
                        'from_entity': record['from_entity2'],
                        'relationship': record['relationship2'],
                        'source': record['source2'],
                        'evidence': record['evidence2']
                    }
                })
            
            return conflicts
    
    def timeline_across_sources(self, event_pattern: str) -> List[Dict]:
        """Create timeline of events across all sources"""
        with self.driver.session(database="the-great-fire-db") as session:
            query = """
            MATCH (event:Entity:Event)
            WHERE toLower(event.name) CONTAINS toLower($event_pattern)
            MATCH (event)<-[:MENTIONS]-(ep:Episode)-[:FROM_SOURCE]->(s:Source)
            MATCH (ep)-[:IN_CHAPTER]->(c:Chapter)
            RETURN event.name as event_name, event.importance as importance,
                   s.title as source_title, s.author as source_author, s.perspective as perspective,
                   c.number as chapter_number, c.title as chapter_title,
                   ep.content as episode_content
            ORDER BY c.number, s.year
            """
            
            result = session.run(query, event_pattern=event_pattern)
            
            timeline = []
            for record in result:
                timeline.append({
                    'event_name': record['event_name'],
                    'importance': record['importance'],
                    'source_title': record['source_title'],
                    'author': record['source_author'],
                    'perspective': record['perspective'],
                    'chapter_number': record['chapter_number'],
                    'chapter_title': record['chapter_title'],
                    'content_snippet': record['episode_content'][:300] + "..." if record['episode_content'] else ""
                })
            
            return timeline
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about all sources"""
        with self.driver.session(database="the-great-fire-db") as session:
            
            # Overall stats
            stats_query = """
            MATCH (s:Source)
            OPTIONAL MATCH (s)-[:HAS_CHAPTER]->(c:Chapter)
            OPTIONAL MATCH (e:Episode)-[:FROM_SOURCE]->(s)
            OPTIONAL MATCH (ent:Entity {sourceId: s.sourceId})
            OPTIONAL MATCH ()-[r:RELATES_TO {sourceId: s.sourceId}]->()
            RETURN s.title as title, s.sourceId as sourceId,
                   count(DISTINCT c) as chapters,
                   count(DISTINCT e) as episodes,
                   count(DISTINCT ent) as entities,
                   count(DISTINCT r) as relationships
            ORDER BY s.title
            """
            
            result = session.run(stats_query)
            
            sources = []
            total_chapters = 0
            total_episodes = 0
            total_entities = 0
            total_relationships = 0
            
            for record in result:
                source_stats = {
                    'title': record['title'],
                    'sourceId': record['sourceId'],
                    'chapters': record['chapters'],
                    'episodes': record['episodes'],
                    'entities': record['entities'],
                    'relationships': record['relationships']
                }
                sources.append(source_stats)
                
                total_chapters += record['chapters']
                total_episodes += record['episodes']
                total_entities += record['entities']
                total_relationships += record['relationships']
            
            # Entity type breakdown
            entity_types_query = """
            MATCH (e:Entity)
            WHERE e.sourceId IS NOT NULL
            RETURN e.entity_type as type, e.sourceId as sourceId, count(e) as count
            ORDER BY e.sourceId, type
            """
            
            entity_result = session.run(entity_types_query)
            entity_breakdown = {}
            for record in entity_result:
                source_id = record['sourceId']
                if source_id not in entity_breakdown:
                    entity_breakdown[source_id] = {}
                entity_breakdown[source_id][record['type']] = record['count']
            
            return {
                'summary': {
                    'total_sources': len(sources),
                    'total_chapters': total_chapters,
                    'total_episodes': total_episodes,
                    'total_entities': total_entities,
                    'total_relationships': total_relationships
                },
                'by_source': sources,
                'entity_breakdown': entity_breakdown
            }
    
    def close(self):
        self.driver.close()

# Example usage and testing
if __name__ == "__main__":
    queries = SourceAwareQueries()
    
    try:
        print("📚 MULTI-SOURCE QUERY EXAMPLES")
        print("=" * 50)
        
        # List all sources
        print("\n1. ALL SOURCES IN DATABASE:")
        sources = queries.list_all_sources()
        for source in sources:
            print(f"   📖 {source['title']} by {source['author']} ({source['year']})")
            print(f"      ID: {source['sourceId']}")
            print(f"      Perspective: {source['perspective']}")
            print(f"      Content: {source['chapters']} chapters, {source['episodes']} episodes")
        
        # Compare entity across sources
        print("\n2. ENTITY COMPARISON - 'Jennings':")
        comparisons = queries.compare_entity_across_sources("Jennings")
        for source, entities in comparisons.items():
            print(f"   📚 In '{source}':")
            for entity in entities:
                print(f"      👤 {entity['entity_name']}: {entity['role']}")
        
        # Get statistics
        print("\n3. DATABASE STATISTICS:")
        stats = queries.get_source_statistics()
        print(f"   📊 Total: {stats['summary']['total_sources']} sources, "
              f"{stats['summary']['total_entities']} entities, "
              f"{stats['summary']['total_relationships']} relationships")
        
        print("\n✅ Multi-source query system working!")
        
    finally:
        queries.close()