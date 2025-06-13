#!/usr/bin/env python3
"""
Enhanced ingestion system for multiple books with source tracking
Extends the existing enhanced_narrative_ingest.py for multi-book support
"""

import os
import asyncio
import glob
import json
import requests
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase
import re
from typing import List, Dict, Any

class MultiBookIngest:
    def __init__(self, text_directory="./text_files"):
        self.text_directory = text_directory
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        self.ollama_url = "http://localhost:11434/v1/chat/completions"
        self.model = "mistral-small3.1:latest"
        
    def create_source_node(self, source_info: Dict[str, Any]) -> str:
        """Create a Source node for a new book"""
        with self.driver.session(database="the-great-fire-db") as session:
            # Generate sourceId from title
            source_id = source_info['title'].lower().replace(' ', '-').replace("'", "")
            source_id = re.sub(r'[^a-z0-9\-]', '', source_id)
            
            print(f"📚 Creating source node: {source_info['title']}")
            
            # Handle null values for Neo4j
            year_value = source_info.get('year') or 0  # Use 0 instead of null
            
            session.run("""
            MERGE (s:Source {
                sourceId: $sourceId,
                title: $title,
                author: $author,
                year: $year,
                isbn: $isbn,
                publisher: $publisher,
                perspective: $perspective,
                language: $language,
                historical_period: $historical_period,
                description: $description,
                created_at: datetime()
            })
            """, 
                sourceId=source_id,
                title=source_info['title'],
                author=source_info.get('author', 'Unknown'),
                year=year_value,
                isbn=source_info.get('isbn', ''),
                publisher=source_info.get('publisher', ''),
                perspective=source_info.get('perspective', ''),
                language=source_info.get('language', 'English'),
                historical_period=source_info.get('historical_period', ''),
                description=source_info.get('description', '')
            )
            
            return source_id
    
    def ingest_book(self, source_info: Dict[str, Any], file_pattern: str = "*.txt"):
        """Ingest a complete book with source tracking"""
        
        print(f"\n🔥 INGESTING NEW BOOK: {source_info['title']}")
        print("=" * 60)
        
        # 1. Create source node
        source_id = self.create_source_node(source_info)
        
        # 2. Find and process text files
        pattern = os.path.join(self.text_directory, file_pattern)
        files = glob.glob(pattern)
        files.sort()
        
        if not files:
            print(f"❌ No files found matching: {pattern}")
            return
        
        print(f"📂 Found {len(files)} files to process")
        
        # 3. Process each file
        chapters_created = {}
        episodes_created = 0
        
        for file_path in files:
            print(f"\n📖 Processing: {os.path.basename(file_path)}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract chapter info
            chapter_info = self.extract_chapter_info(content, file_path)
            chapter_info['sourceId'] = source_id
            
            # Create chapter node if new
            chapter_id = f"{source_id}-ch{chapter_info['number']}"
            if chapter_id not in chapters_created:
                self.create_chapter_node(chapter_info, source_id)
                chapters_created[chapter_id] = chapter_info
            
            # Create episodes for this chapter
            episodes = self.chunk_content(content, chapter_info)
            
            for episode in episodes:
                # Extract entities and relationships with source context
                entities = self.extract_narrative_entities(
                    episode['content'], 
                    chapter_info, 
                    source_id
                )
                
                # Create episode with source tracking
                self.create_episode_with_source(episode, chapter_info, source_id, entities)
                episodes_created += 1
        
        print(f"\n✅ BOOK INGESTION COMPLETE")
        print(f"📚 Source: {source_info['title']}")
        print(f"📖 Chapters: {len(chapters_created)}")
        print(f"📄 Episodes: {episodes_created}")
    
    def extract_chapter_info(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract chapter information from content"""
        filename = os.path.basename(file_path)
        
        # Try to extract chapter number and title
        chapter_match = re.search(r'CHAPTER\s+(\d+)\s*\n(.+)', content, re.IGNORECASE)
        
        if chapter_match:
            chapter_number = int(chapter_match.group(1))
            chapter_title = chapter_match.group(2).strip()
        else:
            # Fallback: extract from filename
            num_match = re.search(r'chapter_?(\d+)', filename, re.IGNORECASE)
            chapter_number = int(num_match.group(1)) if num_match else 1
            chapter_title = filename.replace('.txt', '').replace('_', ' ').title()
        
        return {
            'number': chapter_number,
            'title': chapter_title,
            'filename': filename,
            'word_count': len(content.split())
        }
    
    def create_chapter_node(self, chapter_info: Dict[str, Any], source_id: str):
        """Create a Chapter node linked to Source"""
        with self.driver.session(database="the-great-fire-db") as session:
            chapter_id = f"{source_id}-ch{chapter_info['number']}"
            
            session.run("""
            MATCH (s:Source {sourceId: $sourceId})
            MERGE (c:Chapter {
                chapterId: $chapterId,
                number: $number,
                title: $title,
                filename: $filename,
                sourceId: $sourceId,
                word_count: $word_count,
                created_at: datetime()
            })
            MERGE (s)-[:HAS_CHAPTER]->(c)
            """,
                sourceId=source_id,
                chapterId=chapter_id,
                number=chapter_info['number'],
                title=chapter_info['title'],
                filename=chapter_info['filename'],
                word_count=chapter_info['word_count']
            )
    
    def chunk_content(self, content: str, chapter_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split content into manageable episodes"""
        # Simple chunking by paragraphs (can be enhanced)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        episodes = []
        current_chunk = ""
        chunk_num = 1
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > 1500:  # Target chunk size
                if current_chunk:
                    episodes.append({
                        'name': f"{chapter_info['title']} (Part {chunk_num})",
                        'content': current_chunk.strip(),
                        'chunk_number': chunk_num,
                        'word_count': len(current_chunk.split())
                    })
                    chunk_num += 1
                    current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add final chunk
        if current_chunk:
            episodes.append({
                'name': f"{chapter_info['title']} (Part {chunk_num})",
                'content': current_chunk.strip(),
                'chunk_number': chunk_num,
                'word_count': len(current_chunk.split())
            })
        
        return episodes
    
    def call_ollama(self, prompt: str, max_tokens: int = 1500) -> str:
        """Call Ollama for entity extraction"""
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert entity extractor. Extract key entities from historical text. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(self.ollama_url, json=data)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return ""
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return ""
    
    def extract_narrative_entities(self, text: str, chapter_info: dict, source_id: str) -> Dict[str, List]:
        """Extract entities with source context"""
        prompt = f"""Extract key entities from this historical text:

{text[:1500]}

Source: {source_id}
Chapter: {chapter_info['title']}

Return JSON format:
{{
    "people": [
        {{"name": "Person Name", "role": "their role", "significance": "why important"}}
    ],
    "places": [
        {{"name": "Place Name", "type": "city/country/building", "context": "relevance"}}
    ],
    "events": [
        {{"name": "Event Name", "type": "battle/meeting/crisis", "importance": "high/medium/low"}}
    ],
    "organizations": [
        {{"name": "Organization Name", "type": "military/government/religious"}}
    ]
}}

Return ONLY the JSON."""
        
        response = self.call_ollama(prompt)
        
        try:
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                entities = json.loads(json_str)
                return entities
        except:
            pass
        
        # Fallback empty structure
        return {
            "people": [],
            "places": [],
            "events": [],
            "organizations": []
        }
    
    def create_episode_with_source(self, episode: Dict, chapter_info: Dict, source_id: str, entities: Dict):
        """Create episode with full source tracking"""
        with self.driver.session(database="the-great-fire-db") as session:
            
            # Create Episode node
            episode_id = f"{source_id}-ch{chapter_info['number']}-ep{episode['chunk_number']}"
            
            session.run("""
            MATCH (c:Chapter {chapterId: $chapterId})
            MATCH (s:Source {sourceId: $sourceId})
            MERGE (e:Episode {
                episodeId: $episodeId,
                name: $name,
                content: $content,
                chapter_number: $chapter_number,
                chapter_title: $chapter_title,
                chunk_number: $chunk_number,
                word_count: $word_count,
                sourceId: $sourceId,
                filename: $filename,
                created_at: datetime()
            })
            MERGE (e)-[:IN_CHAPTER]->(c)
            MERGE (e)-[:FROM_SOURCE]->(s)
            """,
                episodeId=episode_id,
                chapterId=f"{source_id}-ch{chapter_info['number']}",
                sourceId=source_id,
                name=episode['name'],
                content=episode['content'],
                chapter_number=chapter_info['number'],
                chapter_title=chapter_info['title'],
                chunk_number=episode['chunk_number'],
                word_count=episode['word_count'],
                filename=chapter_info['filename']
            )
            
            # Create entities with source tracking
            self.create_entities_with_source(entities, episode_id, source_id, chapter_info, session)
    
    def create_entities_with_source(self, entities: Dict, episode_id: str, source_id: str, chapter_info: Dict, session):
        """Create entities with full source provenance"""
        
        # Process people
        for person in entities.get('people', []):
            entity_id = f"{source_id}-person-{person['name'].lower().replace(' ', '-')}"
            
            session.run("""
            MERGE (p:Entity:Person {
                entityId: $entityId,
                name: $name,
                role: $role,
                significance: $significance,
                sourceId: $sourceId,
                entity_type: "Person",
                created_at: datetime()
            })
            
            WITH p
            MATCH (e:Episode {episodeId: $episodeId})
            MERGE (e)-[:MENTIONS {
                sourceId: $sourceId,
                chapter: $chapter,
                context: $context,
                created_at: datetime()
            }]->(p)
            """,
                entityId=entity_id,
                name=person['name'],
                role=person.get('role', ''),
                significance=person.get('significance', ''),
                sourceId=source_id,
                episodeId=episode_id,
                chapter=chapter_info['title'],
                context=f"Mentioned in {chapter_info['title']}"
            )
        
        # Process places
        for place in entities.get('places', []):
            entity_id = f"{source_id}-place-{place['name'].lower().replace(' ', '-')}"
            
            session.run("""
            MERGE (p:Entity:Location {
                entityId: $entityId,
                name: $name,
                type: $type,
                context: $context,
                sourceId: $sourceId,
                entity_type: "Location",
                created_at: datetime()
            })
            
            WITH p
            MATCH (e:Episode {episodeId: $episodeId})
            MERGE (e)-[:MENTIONS {
                sourceId: $sourceId,
                chapter: $chapter,
                created_at: datetime()
            }]->(p)
            """,
                entityId=entity_id,
                name=place['name'],
                type=place.get('type', ''),
                context=place.get('context', ''),
                sourceId=source_id,
                episodeId=episode_id,
                chapter=chapter_info['title']
            )
        
        # Process events
        for event in entities.get('events', []):
            entity_id = f"{source_id}-event-{event['name'].lower().replace(' ', '-')}"
            
            session.run("""
            MERGE (ev:Entity:Event {
                entityId: $entityId,
                name: $name,
                type: $type,
                importance: $importance,
                sourceId: $sourceId,
                entity_type: "Event",
                created_at: datetime()
            })
            
            WITH ev
            MATCH (e:Episode {episodeId: $episodeId})
            MERGE (e)-[:MENTIONS {
                sourceId: $sourceId,
                chapter: $chapter,
                created_at: datetime()
            }]->(ev)
            """,
                entityId=entity_id,
                name=event['name'],
                type=event.get('type', ''),
                importance=event.get('importance', 'medium'),
                sourceId=source_id,
                episodeId=episode_id,
                chapter=chapter_info['title']
            )
    
    def link_to_canonical_entities(self, source_id: str):
        """Link new entities to existing canonical entities where appropriate"""
        with self.driver.session(database="the-great-fire-db") as session:
            
            print(f"🔗 Linking {source_id} entities to canonical entities...")
            
            # Find potential matches for major historical figures
            session.run("""
            MATCH (new:Entity {sourceId: $sourceId})
            MATCH (canonical:CanonicalEntity)
            WHERE toLower(new.name) CONTAINS toLower(canonical.canonicalName) 
               OR toLower(canonical.canonicalName) CONTAINS toLower(new.name)
            MERGE (new)-[:INTERPRETS_AS]->(canonical)
            SET new.canonicalName = canonical.canonicalName
            """, sourceId=source_id)
    
    def close(self):
        self.driver.close()

# Example usage
if __name__ == "__main__":
    ingester = MultiBookIngest()
    
    # Example: Add a second book about the same historical period
    second_book_info = {
        'title': 'Paradise Lost: Smyrna 1922',
        'author': 'Giles Milton',
        'year': 2008,
        'isbn': '9780465045624',
        'publisher': 'Basic Books',
        'perspective': 'British historian perspective',
        'language': 'English',
        'historical_period': '1922 Greek-Turkish War',
        'description': 'Another account of the destruction of Smyrna from British perspective'
    }
    
    # To ingest a new book:
    # ingester.ingest_book(second_book_info, "paradise_lost_*.txt")
    
    print("📚 Multi-book ingestion system ready!")
    print("💡 To ingest a new book, call:")
    print("   ingester.ingest_book(book_info, 'filename_pattern*.txt')")
    
    ingester.close()