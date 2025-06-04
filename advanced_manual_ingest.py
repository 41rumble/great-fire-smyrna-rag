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

class AdvancedManualIngest:
    def __init__(self, text_directory="./text_files"):
        self.text_directory = text_directory
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        self.ollama_url = "http://localhost:11434/v1/chat/completions"
        self.model = "mistral-small3.1:latest"
        
    def call_ollama(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call Ollama with a prompt"""
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(self.ollama_url, json=data)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"Ollama error: {response.status_code}")
                return ""
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return ""
    
    def extract_comprehensive_entities(self, text: str, context: str) -> Dict[str, List[Dict]]:
        """Extract comprehensive entities using Ollama"""
        prompt = f"""Analyze this historical text about the Great Fire of Smyrna (1922) and extract detailed entities.

Context: {context}

Text: {text[:2000]}

Extract entities in this exact JSON format:
{{
    "people": [
        {{"name": "Full Name", "role": "their role/title", "nationality": "nationality", "significance": "why they're important"}}
    ],
    "places": [
        {{"name": "Place Name", "type": "city/district/building/ship", "location": "broader location", "significance": "historical importance"}}
    ],
    "events": [
        {{"name": "Event Name", "date": "when it happened", "type": "fire/evacuation/military/diplomatic", "significance": "why it mattered"}}
    ],
    "organizations": [
        {{"name": "Organization Name", "type": "military/relief/government/religious", "role": "what they did"}}
    ],
    "dates": [
        {{"name": "specific date or period", "event": "what happened", "significance": "importance"}}
    ]
}}

Focus on historical accuracy and specific details. Only include entities explicitly mentioned in the text."""
        
        response = self.call_ollama(prompt, 1500)
        
        try:
            # Extract JSON from response
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                parsed = json.loads(json_str)
                
                # Validate structure
                result = {"people": [], "places": [], "events": [], "organizations": [], "dates": []}
                for key in result.keys():
                    if key in parsed and isinstance(parsed[key], list):
                        # Filter valid entities
                        valid_entities = []
                        for item in parsed[key]:
                            if isinstance(item, dict):
                                # Handle different naming conventions
                                if 'name' in item:
                                    valid_entities.append(item)
                                elif key == 'dates' and 'date' in item:
                                    # Convert date format to standard
                                    item['name'] = item['date']
                                    valid_entities.append(item)
                                else:
                                    print(f"Skipping invalid {key} entity (missing name/date): {item}")
                            else:
                                print(f"Skipping invalid {key} entity: {item}")
                        result[key] = valid_entities
                
                return result
        except Exception as e:
            print(f"Error parsing entities JSON: {e}")
            print(f"Response was: {response[:200]}...")
        
        return {"people": [], "places": [], "events": [], "organizations": [], "dates": []}
    
    def extract_relationships(self, text: str, entities: Dict[str, List[Dict]]) -> List[Dict]:
        """Extract relationships between entities"""
        all_entities = []
        for category, ent_list in entities.items():
            for ent in ent_list:
                if isinstance(ent, dict) and 'name' in ent:
                    all_entities.append(f"{ent['name']} ({category[:-1]})")
                else:
                    print(f"Warning: Invalid entity format in {category}: {ent}")
        
        if len(all_entities) < 2:
            return []
            
        entities_str = "\n".join(all_entities[:20])  # Limit to avoid token overflow
        
        prompt = f"""Based on this historical text, find relationships between these entities. Return ONLY valid JSON.

Text: {text[:1200]}

Entities: {entities_str[:800]}

Return exactly this JSON format (no extra text):
{{
    "relationships": [
        {{"from": "EntityName1", "to": "EntityName2", "relationship": "RELATIONSHIP_TYPE", "context": "brief context"}}
    ]
}}

Valid relationships: LOCATED_IN, COMMANDED, RESCUED, WITNESSED, ALLIED_WITH, OPPOSED, EVACUATED_FROM, CAUSED, RESULTED_FROM.

Include maximum 5 relationships. Use exact entity names. Keep context under 50 words."""
        
        response = self.call_ollama(prompt, 800)
        
        try:
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                
                # Clean up common JSON issues
                json_str = json_str.replace('\n', ' ')
                json_str = json_str.replace('\t', ' ')
                json_str = json_str.replace('\\', '')
                
                # Fix common quote issues
                json_str = json_str.replace('"', '"').replace('"', '"')
                json_str = json_str.replace(''', "'").replace(''', "'")
                
                # Try to parse
                data = json.loads(json_str)
                relationships = data.get('relationships', [])
                
                # Validate relationship structure
                valid_relationships = []
                for rel in relationships:
                    if isinstance(rel, dict) and all(key in rel for key in ['from', 'to', 'relationship']):
                        valid_relationships.append(rel)
                    else:
                        print(f"Skipping invalid relationship: {rel}")
                
                return valid_relationships
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Problematic JSON: {json_str[:200]}...")
            
            # Fallback: try to extract simple relationships from text
            return self.extract_simple_relationships(text, all_entities)
            
        except Exception as e:
            print(f"Error parsing relationships: {e}")
        
        return []
    
    def extract_simple_relationships(self, text: str, entities: list) -> List[Dict]:
        """Simple fallback relationship extraction without JSON"""
        relationships = []
        
        # Look for common relationship patterns
        patterns = [
            (r'(\w+(?:\s+\w+)*)\s+commanded\s+(\w+(?:\s+\w+)*)', 'COMMANDED'),
            (r'(\w+(?:\s+\w+)*)\s+rescued\s+(\w+(?:\s+\w+)*)', 'RESCUED'),
            (r'(\w+(?:\s+\w+)*)\s+in\s+(\w+(?:\s+\w+)*)', 'LOCATED_IN'),
            (r'(\w+(?:\s+\w+)*)\s+witnessed\s+(\w+(?:\s+\w+)*)', 'WITNESSED')
        ]
        
        for pattern, rel_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                from_entity = match.group(1).strip()
                to_entity = match.group(2).strip()
                
                # Check if entities are in our extracted list
                from_match = next((e for e in entities if from_entity.lower() in e.lower()), None)
                to_match = next((e for e in entities if to_entity.lower() in e.lower()), None)
                
                if from_match and to_match and len(relationships) < 3:
                    relationships.append({
                        "from": from_match.split(" (")[0],
                        "to": to_match.split(" (")[0], 
                        "relationship": rel_type,
                        "context": f"Pattern match in text"
                    })
        
        return relationships
    
    def store_comprehensive_episode(self, episode_data: Dict, entities: Dict, relationships: List[Dict]):
        """Store episode, entities, and relationships in Neo4j"""
        with self.driver.session(database="the-great-fire-db") as session:
            # Create episode node
            episode_query = """
            CREATE (ep:Episode {
                name: $name,
                content: $content,
                filename: $filename,
                chapter_title: $chapter_title,
                word_count: $word_count,
                created_at: datetime(),
                reference_date: $reference_date
            })
            RETURN ep
            """
            
            session.run(episode_query, {
                "name": episode_data["name"],
                "content": episode_data["content"],
                "filename": episode_data["filename"],
                "chapter_title": episode_data.get("chapter_title", ""),
                "word_count": episode_data.get("word_count", 0),
                "reference_date": episode_data.get("reference_date", "1922-09-13")
            })
            
            # Create entity nodes
            for category, ent_list in entities.items():
                for entity in ent_list:
                    if isinstance(entity, dict) and 'name' in entity:
                        entity_query = f"""
                        MERGE (ent:Entity:{category.title()[:-1]} {{name: $name}})
                        SET ent.type = $type,
                            ent.category = $category,
                            ent.significance = $significance,
                            ent.updated_at = datetime()
                        WITH ent
                        MATCH (ep:Episode {{name: $episode_name}})
                        MERGE (ep)-[:MENTIONS]->(ent)
                        """
                        
                        session.run(entity_query, {
                            "name": entity["name"],
                            "type": entity.get("type", entity.get("role", "unknown")),
                            "category": category[:-1],  # Remove 's' from plural
                            "significance": entity.get("significance", ""),
                            "episode_name": episode_data["name"]
                        })
                    else:
                        print(f"Skipping invalid entity in {category}: {entity}")
            
            # Create relationships between entities
            for rel in relationships:
                rel_query = """
                MATCH (a:Entity {name: $from_name})
                MATCH (b:Entity {name: $to_name})
                MERGE (a)-[r:RELATES_TO {type: $rel_type}]->(b)
                SET r.context = $context,
                    r.episode = $episode_name,
                    r.created_at = datetime()
                """
                
                # Extract entity names (remove category info)
                from_name = rel["from"].split(" (")[0]
                to_name = rel["to"].split(" (")[0]
                
                session.run(rel_query, {
                    "from_name": from_name,
                    "to_name": to_name,
                    "rel_type": rel["relationship"],
                    "context": rel.get("context", ""),
                    "episode_name": episode_data["name"]
                })
    
    def extract_chapter_info(self, filename: str, content: str) -> Dict:
        """Extract chapter metadata"""
        chapter_match = re.search(r'CHAPTER\s+(\d+)\s*\n(.+)', content)
        if chapter_match:
            chapter_num = int(chapter_match.group(1))
            title = chapter_match.group(2).strip()
        else:
            chapter_num = 0
            title = filename.replace('.txt', '').replace('TheGreatFire_', '')
        
        # Extract dates
        dates = re.findall(r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', content)
        
        return {
            "chapter_number": chapter_num,
            "title": title,
            "dates": dates[:3],
            "word_count": len(content.split())
        }
    
    def split_content(self, content: str, target_size: int = 1000) -> List[str]:
        """Split content into manageable chunks"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para.split())
            
            if current_size + para_size > target_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    async def process_file_comprehensive(self, file_path: str):
        """Process a single file comprehensively"""
        filename = Path(file_path).name
        print(f"\n📚 Processing: {filename}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if len(content.strip()) < 100:
            print(f"   ⏭️  Skipping - too short")
            return
        
        # Extract chapter info
        chapter_info = self.extract_chapter_info(filename, content)
        print(f"   📖 Chapter {chapter_info['chapter_number']}: {chapter_info['title']}")
        
        # Split into chunks
        chunks = self.split_content(content, 1200)
        print(f"   📑 Split into {len(chunks)} episodes")
        
        for i, chunk in enumerate(chunks):
            episode_name = f"Great Fire - {chapter_info['title']} (Episode {i+1})"
            context = f"Chapter {chapter_info['chapter_number']}: {chapter_info['title']}. Historical period: September 1922, Great Fire of Smyrna."
            
            print(f"      🔍 Extracting entities from episode {i+1}...")
            entities = self.extract_comprehensive_entities(chunk, context)
            
            total_entities = sum(len(ents) for ents in entities.values())
            print(f"         Found {total_entities} entities")
            
            print(f"      🔗 Extracting relationships...")
            relationships = self.extract_relationships(chunk, entities)
            print(f"         Found {len(relationships)} relationships")
            
            episode_data = {
                "name": episode_name,
                "content": chunk,
                "filename": filename,
                "chapter_title": chapter_info['title'],
                "word_count": len(chunk.split()),
                "reference_date": "1922-09-13"
            }
            
            print(f"      💾 Storing in knowledge graph...")
            self.store_comprehensive_episode(episode_data, entities, relationships)
            print(f"      ✅ Episode {i+1} complete")
            
            # Brief pause to avoid overwhelming the system
            await asyncio.sleep(2)
    
    async def process_all_files(self):
        """Process all files comprehensively"""
        txt_files = glob.glob(os.path.join(self.text_directory, "*.txt"))
        
        if not txt_files:
            print(f"No .txt files found in {self.text_directory}")
            return
        
        print(f"🔥 ADVANCED MANUAL INGESTION - GREAT FIRE OF SMYRNA")
        print(f"Found {len(txt_files)} files to process")
        print("=" * 70)
        
        total_episodes = 0
        for file_path in sorted(txt_files):
            await self.process_file_comprehensive(file_path)
            total_episodes += 1
        
        print(f"\n" + "=" * 70)
        print(f"🎉 COMPREHENSIVE INGESTION COMPLETE!")
        print(f"📊 Files processed: {total_episodes}")
        print("🔍 Ready for advanced querying!")
        print("=" * 70)
    
    def close(self):
        self.driver.close()

async def main():
    text_dir = input("Enter path to text files (or press Enter for '~/Downloads/chapters'): ").strip()
    if not text_dir:
        text_dir = "~/Downloads/chapters"
    
    text_dir = os.path.expanduser(text_dir)
    
    processor = AdvancedManualIngest(text_dir)
    await processor.process_all_files()
    processor.close()

if __name__ == "__main__":
    asyncio.run(main())