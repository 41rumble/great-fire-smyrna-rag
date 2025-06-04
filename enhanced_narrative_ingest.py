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

class EnhancedNarrativeIngest:
    def __init__(self, text_directory="./text_files"):
        self.text_directory = text_directory
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        self.ollama_url = "http://localhost:11434/v1/chat/completions"
        self.model = "mistral-small3.1:latest"  # Back to Mistral - more aggressive at entity extraction
        
        # Track story progression
        self.story_timeline = []
        self.character_arcs = {}
        
    def call_ollama(self, prompt: str, max_tokens: int = 1500) -> str:
        """Call Ollama with enhanced parameters for narrative analysis"""
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an aggressive entity extractor. You MUST find and extract entities from ANY text given to you. Never return empty arrays. Always find at least some entities. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,  # Very low for consistent JSON
            "top_p": 0.9,
            "repeat_penalty": 1.0
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
    
    def extract_first_complete_json(self, response: str) -> str:
        """Extract the first complete JSON object from response"""
        start = response.find('{')
        if start == -1:
            return ""
        
        brace_count = 0
        i = start
        while i < len(response):
            if response[i] == '{':
                brace_count += 1
            elif response[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return response[start:i+1]
            i += 1
        
        # If we get here, JSON was incomplete
        return response[start:]
    
    def extract_narrative_entities(self, text: str, chapter_info: dict, chapter_sequence: int) -> Dict[str, List[Dict]]:
        """Extract entities with deep narrative and temporal context"""
        
        prompt = f"""Extract key entities from this text about The Great Fire of Smyrna:

{text[:1500]}

{{
    "characters": [
        {{"name": "Character Name", "role": "brief role"}}
    ],
    "locations": [
        {{"name": "Location Name", "type": "city/country/building"}}
    ],
    "events": [
        {{"name": "Event Name", "type": "important/minor"}}
    ]
}}

Find 3-5 entities per category. Keep it simple. Return ONLY the JSON."""
        
        response = self.call_ollama(prompt, 5000)  # Increased for complex JSON
        
        # DEBUG: Show what we actually got back
        print(f"      🔍 Response length: {len(response)} chars")
        print(f"      🔍 Response starts with: {response[:100]}...")
        print(f"      🔍 Response ends with: ...{response[-100:]}")
        
        try:
            # More aggressive JSON extraction and cleaning for entities
            if '{' in response and '}' in response:
                # Try to find JSON - NO CLEANING AT ALL
                if '```json' in response:
                    start = response.find('```json') + 7
                    end = response.find('```', start)
                    if end != -1:
                        json_str = response[start:end].strip()
                    else:
                        json_str = self.extract_first_complete_json(response)
                else:
                    json_str = self.extract_first_complete_json(response)
                
                # DEBUG: Check if JSON looks complete
                print(f"      🔍 Cleaned JSON length: {len(json_str)}")
                print(f"      🔍 JSON starts: {json_str[:50]}")
                print(f"      🔍 JSON ends: {json_str[-50:]}")
                
                # Check for incomplete JSON (common signs)
                if not json_str.rstrip().endswith('}'):
                    print(f"      ⚠️ JSON doesn't end with }} - likely truncated!")
                
                brace_count = json_str.count('{') - json_str.count('}')
                if brace_count != 0:
                    print(f"      ⚠️ Unbalanced braces: {brace_count} extra opening braces")
                
                parsed = json.loads(json_str)
                
                # Validate and structure  
                result = {
                    "characters": [], "locations": [], "events": []
                }
                
                entity_count = 0
                for key in result.keys():
                    if key in parsed and isinstance(parsed[key], list):
                        for item in parsed[key]:
                            if isinstance(item, dict) and 'name' in item:
                                result[key].append(item)
                                entity_count += 1
                
                print(f"      ✅ Extracted {entity_count} entities from JSON")
                return result
                
        except json.JSONDecodeError as e:
            print(f"      JSON decode error in entities: {e}")
            print(f"      Problematic JSON around error: {json_str[max(0, e.pos-50):e.pos+50]}")
            print(f"      Full JSON length: {len(json_str)}")
            # Write the problematic JSON to file for debugging
            with open("/tmp/debug_entities.json", "w") as f:
                f.write(json_str)
            print(f"      Saved problematic JSON to /tmp/debug_entities.json")
            return {
                "characters": [], "locations": [], "events": [], 
                "organizations": [], "temporal_markers": [], "themes": []
            }
        except Exception as e:
            print(f"      Error parsing narrative entities: {e}")
            print(f"      Raw response: {response[:500]}...")
            return {
                "characters": [], "locations": [], "events": [], 
                "organizations": [], "temporal_markers": [], "themes": []
            }
    
    def extract_entities_by_pattern(self, response: str, original_text: str) -> Dict[str, List[Dict]]:
        """Fallback: extract entities using simple patterns"""
        result = {
            "characters": [], "locations": [], "events": [], 
            "organizations": [], "temporal_markers": [], "themes": []
        }
        
        # Simple character extraction - look for proper names
        name_pattern = r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b'
        potential_names = re.findall(name_pattern, original_text)
        
        # Filter for likely character names (common historical names)
        likely_characters = []
        unique_names = list(set(potential_names))  # Convert to list
        for name in unique_names:
            if len(name.split()) <= 3 and len(name) > 3:
                if any(word in name for word in ['Jennings', 'Atatürk', 'Kemal', 'Horton', 'Bristol']):
                    likely_characters.append({
                        "name": name,
                        "role": "Historical figure",
                        "significance": "Key person in the Great Fire events"
                    })
        
        result["characters"] = likely_characters[:5]
        
        # Simple location extraction - look for place names
        location_indicators = ['Smyrna', 'Constantinople', 'Turkey', 'Greece', 'America', 'Izmir']
        for location in location_indicators:
            if location.lower() in original_text.lower():
                result["locations"].append({
                    "name": location,
                    "type": "city" if location in ['Smyrna', 'Constantinople', 'Izmir'] else "country",
                    "significance": "Important location in the historical narrative"
                })
        
        # Simple date extraction
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        dates = re.findall(date_pattern, original_text)
        unique_dates = list(set(dates))[:3]  # Convert to list before slicing
        for date in unique_dates:
            result["temporal_markers"].append({
                "time_reference": date,
                "narrative_moment": "Historical date mentioned in text"
            })
        
        total_entities = sum(len(ents) for ents in result.values())
        print(f"      🔄 Fallback: extracted {total_entities} entities by pattern matching")
        
        return result
    
    def extract_deep_relationships(self, text: str, entities: Dict, chapter_info: dict) -> List[Dict]:
        """Extract deep narrative and causal relationships"""
        
        all_entities = []
        for category, ent_list in entities.items():
            for ent in ent_list:
                if isinstance(ent, dict):
                    if 'name' in ent:
                        all_entities.append(f"{ent['name']} ({category[:-1]})")
                    elif category == 'temporal_markers' and 'time_reference' in ent:
                        all_entities.append(f"{ent['time_reference']} (time)")
                    elif category == 'themes' and 'theme' in ent:
                        all_entities.append(f"{ent['theme']} (theme)")
        
        if len(all_entities) < 2:
            return []
        
        entities_str = "\n".join(all_entities[:20])
        
        prompt = f"""Analyze the deep relationships and connections in this chapter from "The Great Fire of Smyrna".

Chapter: {chapter_info['title']}
Text: {text[:1800]}

Entities found:
{entities_str}

Extract DEEP NARRATIVE RELATIONSHIPS in this JSON format:

{{
    "relationships": [
        {{
            "from": "Entity Name",
            "to": "Entity Name", 
            "relationship_type": "RELATIONSHIP_TYPE",
            "narrative_context": "how this relationship drives the story",
            "emotional_dimension": "emotional aspect of this relationship",
            "power_dynamic": "who has power/influence over whom",
            "temporal_nature": "past/present/future - when does this relationship matter",
            "story_importance": "high/medium/low - importance to overall narrative",
            "conflict_or_harmony": "conflict/harmony/neutral",
            "evidence": "specific evidence from the text"
        }}
    ]
}}

RELATIONSHIP TYPES (choose most specific):

PERSONAL: LOVES, TRUSTS, BETRAYS, MENTORS, FAMILY_OF, FRIENDS_WITH, RIVALS_WITH, DEPENDS_ON
POWER: COMMANDS, REPORTS_TO, INFLUENCES, CONTROLS, SERVES, REPRESENTS
SPATIAL: LIVES_IN, TRAVELS_TO, ESCAPES_FROM, DEFENDS, ATTACKS, OCCUPIES
TEMPORAL: PRECEDES, FOLLOWS, COINCIDES_WITH, TRIGGERS, RESULTS_FROM, INTERRUPTS
NARRATIVE: SYMBOLIZES, REPRESENTS, FORESHADOWS, PARALLELS, CONTRASTS_WITH, EXEMPLIFIES
CAUSAL: CAUSES, PREVENTS, ENABLES, MOTIVATES, INSPIRES, DESTROYS

Focus on relationships that show character development, plot progression, and thematic connections. Maximum 12 relationships.

CRITICAL JSON REQUIREMENTS:
- Return ONLY the JSON object, nothing else
- Use double quotes for all strings
- No trailing commas in objects or arrays
- Properly escape quotes within strings
- All objects must end with }}
- All arrays must end with ]
- No comments or explanations

Example valid format:
{{"characters": [{{"name": "John Doe", "role": "soldier"}}], "locations": []}}"""
        
        response = self.call_ollama(prompt, 4000)  # Increased for relationship JSON
        
        try:
            # More aggressive JSON extraction and cleaning
            if '{' in response and '}' in response:
                # Try to find JSON - NO CLEANING AT ALL
                if '```json' in response:
                    start = response.find('```json') + 7
                    end = response.find('```', start)
                    if end != -1:
                        json_str = response[start:end].strip()
                    else:
                        json_str = self.extract_first_complete_json(response)
                else:
                    json_str = self.extract_first_complete_json(response)
                
                data = json.loads(json_str)
                relationships = data.get('relationships', [])
                
                # Validate relationships
                valid_relationships = []
                for rel in relationships:
                    if isinstance(rel, dict) and all(key in rel for key in ['from', 'to', 'relationship_type']):
                        valid_relationships.append(rel)
                
                print(f"      ✅ Extracted {len(valid_relationships)} valid relationships from JSON")
                return valid_relationships
                
        except json.JSONDecodeError as e:
            print(f"      JSON decode error in relationships: {e}")
            print(f"      Problematic JSON around error: {json_str[max(0, e.pos-50):e.pos+50]}")
            # Write the problematic JSON to file for debugging
            with open("/tmp/debug_relationships.json", "w") as f:
                f.write(json_str)
            print(f"      Saved problematic JSON to /tmp/debug_relationships.json")
            return []
        except Exception as e:
            print(f"      Error parsing relationships: {e}")
            return []
    
    def extract_relationships_by_pattern(self, response: str, entities: list) -> List[Dict]:
        """Fallback: extract relationships using text patterns"""
        relationships = []
        
        # Common relationship patterns in text
        patterns = [
            (r'(\w+(?:\s+\w+)*)\s+(COMMANDS|commands)\s+(\w+(?:\s+\w+)*)', 'COMMANDS'),
            (r'(\w+(?:\s+\w+)*)\s+(TRUSTS|trusts)\s+(\w+(?:\s+\w+)*)', 'TRUSTS'),
            (r'(\w+(?:\s+\w+)*)\s+(INFLUENCES|influences)\s+(\w+(?:\s+\w+)*)', 'INFLUENCES'),
            (r'(\w+(?:\s+\w+)*)\s+(lives in|LIVES_IN)\s+(\w+(?:\s+\w+)*)', 'LIVES_IN'),
            (r'(\w+(?:\s+\w+)*)\s+(escapes from|ESCAPES_FROM)\s+(\w+(?:\s+\w+)*)', 'ESCAPES_FROM'),
            (r'(\w+(?:\s+\w+)*)\s+(causes|CAUSES)\s+(\w+(?:\s+\w+)*)', 'CAUSES'),
            (r'(\w+(?:\s+\w+)*)\s+(serves|SERVES)\s+(\w+(?:\s+\w+)*)', 'SERVES')
        ]
        
        for pattern, rel_type in patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                from_entity = match.group(1).strip()
                to_entity = match.group(3).strip()
                
                # Check if entities match our extracted entities
                from_match = self.find_entity_match(from_entity, entities)
                to_match = self.find_entity_match(to_entity, entities)
                
                if from_match and to_match and len(relationships) < 5:
                    relationships.append({
                        "from": from_match,
                        "to": to_match,
                        "relationship_type": rel_type,
                        "narrative_context": "Pattern-based extraction",
                        "story_importance": "medium",
                        "evidence": f"Text pattern: {match.group(0)}"
                    })
        
        print(f"      🔄 Fallback: extracted {len(relationships)} relationships by pattern matching")
        return relationships
    
    def find_entity_match(self, text: str, entities: list) -> str:
        """Find matching entity name from extracted entities"""
        text_lower = text.lower()
        for entity in entities:
            entity_name = entity.split(" (")[0].lower()
            if text_lower in entity_name or entity_name in text_lower:
                return entity.split(" (")[0]
        return ""
    
    def store_narrative_data(self, episode_data: Dict, entities: Dict, relationships: List[Dict], chapter_info: dict):
        """Store narrative data with deep connections"""
        
        with self.driver.session(database="the-great-fire-db") as session:
            # Create episode with narrative metadata
            episode_query = """
            CREATE (ep:Episode:Chapter {
                name: $name,
                content: $content,
                filename: $filename,
                chapter_number: $chapter_number,
                chapter_title: $chapter_title,
                chapter_sequence: $chapter_sequence,
                word_count: $word_count,
                narrative_importance: $narrative_importance,
                created_at: datetime(),
                story_arc_position: $story_arc_position
            })
            RETURN ep
            """
            
            session.run(episode_query, {
                **episode_data,
                "chapter_number": chapter_info["chapter_number"],
                "chapter_title": chapter_info["title"],
                "chapter_sequence": chapter_info.get("sequence", 0),
                "narrative_importance": self.assess_chapter_importance(entities),
                "story_arc_position": self.determine_story_position(chapter_info.get("sequence", 0))
            })
            
            # Create detailed entity nodes
            for category, ent_list in entities.items():
                for entity in ent_list:
                    if isinstance(entity, dict) and self.get_entity_key(entity, category):
                        entity_name = self.get_entity_key(entity, category)
                        
                        # Create entity with rich narrative data
                        entity_query = f"""
                        MERGE (ent:Entity:{category.title()[:-1]} {{name: $name}})
                        SET ent += $properties,
                            ent.category = $category,
                            ent.last_updated = datetime(),
                            ent.narrative_depth = $narrative_depth
                        WITH ent
                        MATCH (ep:Episode {{name: $episode_name}})
                        MERGE (ep)-[r:MENTIONS]->(ent)
                        SET r.context_in_chapter = $context,
                            r.importance = $importance
                        """
                        
                        # Prepare properties
                        properties = {k: v for k, v in entity.items() if k != 'name'}
                        
                        session.run(entity_query, {
                            "name": entity_name,
                            "properties": properties,
                            "category": category[:-1],
                            "narrative_depth": self.calculate_narrative_depth(entity),
                            "episode_name": episode_data["name"],
                            "context": entity.get("significance", ""),
                            "importance": self.assess_entity_importance(entity, category)
                        })
            
            # Create deep relationships
            for rel in relationships:
                if self.validate_relationship(rel):
                    rel_query = """
                    MATCH (a:Entity {name: $from_name})
                    MATCH (b:Entity {name: $to_name})
                    MERGE (a)-[r:RELATES_TO {
                        type: $rel_type,
                        narrative_context: $narrative_context,
                        emotional_dimension: $emotional_dimension,
                        power_dynamic: $power_dynamic,
                        temporal_nature: $temporal_nature,
                        story_importance: $story_importance,
                        conflict_or_harmony: $conflict_or_harmony,
                        evidence: $evidence,
                        chapter: $chapter_title,
                        created_at: datetime()
                    }]->(b)
                    """
                    
                    session.run(rel_query, {
                        "from_name": rel["from"],
                        "to_name": rel["to"],
                        "rel_type": rel["relationship_type"],
                        "narrative_context": rel.get("narrative_context", ""),
                        "emotional_dimension": rel.get("emotional_dimension", ""),
                        "power_dynamic": rel.get("power_dynamic", ""),
                        "temporal_nature": rel.get("temporal_nature", ""),
                        "story_importance": rel.get("story_importance", "medium"),
                        "conflict_or_harmony": rel.get("conflict_or_harmony", "neutral"),
                        "evidence": rel.get("evidence", ""),
                        "chapter_title": chapter_info["title"]
                    })
    
    def get_entity_key(self, entity: dict, category: str) -> str:
        """Get the key name for an entity based on category"""
        if 'name' in entity:
            return entity['name']
        elif category == 'temporal_markers' and 'time_reference' in entity:
            return entity['time_reference']
        elif category == 'themes' and 'theme' in entity:
            return entity['theme']
        return ""
    
    def assess_chapter_importance(self, entities: Dict) -> str:
        """Assess the narrative importance of a chapter"""
        events = entities.get('events', [])
        characters = entities.get('characters', [])
        
        # Count major plot points
        major_events = sum(1 for event in events if event.get('story_turning_point') == 'true')
        character_developments = sum(1 for char in characters if 'development' in char and char['development'])
        
        if major_events >= 2 or character_developments >= 3:
            return "high"
        elif major_events >= 1 or character_developments >= 2:
            return "medium"
        else:
            return "low"
    
    def determine_story_position(self, sequence: int) -> str:
        """Determine position in story arc"""
        if sequence <= 9:
            return "setup"
        elif sequence <= 18:
            return "rising_action"
        elif sequence <= 27:
            return "climax"
        else:
            return "resolution"
    
    def calculate_narrative_depth(self, entity: dict) -> int:
        """Calculate how narratively rich an entity is"""
        depth = 0
        depth_indicators = [
            'character_arc_stage', 'emotional_state', 'motivations', 'development',
            'narrative_importance', 'story_events', 'symbolic_meaning',
            'narrative_function', 'consequences', 'emotional_impact'
        ]
        
        for indicator in depth_indicators:
            if indicator in entity and entity[indicator]:
                depth += 1
        
        return depth
    
    def assess_entity_importance(self, entity: dict, category: str) -> str:
        """Assess entity importance to the story"""
        if category == 'characters':
            if entity.get('significance', '').lower().find('main') != -1:
                return "high"
            elif entity.get('role', '').lower() in ['commander', 'minister', 'leader']:
                return "high"
            elif entity.get('development', ''):
                return "medium"
            else:
                return "low"
        elif category == 'events':
            if entity.get('story_turning_point') == 'true':
                return "high"
            elif entity.get('narrative_function', ''):
                return "medium"
            else:
                return "low"
        else:
            return "medium"
    
    def validate_relationship(self, rel: dict) -> bool:
        """Validate relationship has required fields"""
        required = ['from', 'to', 'relationship_type']
        return all(key in rel and rel[key] for key in required)
    
    def extract_chapter_metadata(self, filename: str, content: str, sequence: int) -> dict:
        """Extract enhanced chapter metadata"""
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
            "word_count": len(content.split()),
            "filename": filename,
            "sequence": sequence
        }
    
    def split_for_narrative_analysis(self, content: str, metadata: dict) -> List[str]:
        """Split content optimally for narrative analysis"""
        # For narrative analysis, we want larger chunks to capture story flow
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        target_words = 1500  # Larger chunks for better narrative context
        
        for para in paragraphs:
            para_words = len(para.split())
            
            if current_word_count + para_words > target_words and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_word_count = para_words
            else:
                current_chunk.append(para)
                current_word_count += para_words
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    async def process_file_with_narrative_depth(self, file_path: str, sequence: int):
        """Process file with deep narrative analysis"""
        filename = Path(file_path).name
        print(f"\n📚 Processing: {filename} (Story sequence: {sequence}/36)")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            if len(content.strip()) < 100:
                print(f"   ⏭️  Skipping - too short")
                return 0
            
            # Extract chapter metadata
            metadata = self.extract_chapter_metadata(filename, content, sequence)
            print(f"   📖 Chapter {metadata['chapter_number']}: {metadata['title']}")
            print(f"   📍 Story position: {self.determine_story_position(sequence)}")
            
            # Split for narrative analysis
            chunks = self.split_for_narrative_analysis(content, metadata)
            print(f"   📑 Split into {chunks} narrative chunks")
            
            success_count = 0
            for i, chunk in enumerate(chunks):
                print(f"   🔄 Analyzing chunk {i+1}/{len(chunks)}...")
                
                # Extract narrative entities
                entities = self.extract_narrative_entities(chunk, metadata, sequence)
                total_entities = sum(len(ents) for ents in entities.values())
                print(f"      🎭 Found {total_entities} narrative entities")
                
                # Extract deep relationships
                relationships = self.extract_deep_relationships(chunk, entities, metadata)
                print(f"      🔗 Found {len(relationships)} deep relationships")
                
                # Store with narrative data
                episode_data = {
                    "name": f"Great Fire - {metadata['title']} (Narrative Chunk {i+1})",
                    "content": chunk,
                    "filename": filename,
                    "word_count": len(chunk.split())
                }
                
                self.store_narrative_data(episode_data, entities, relationships, metadata)
                success_count += 1
                print(f"      ✅ Chunk {i+1} stored with narrative depth")
                
                # Brief pause
                await asyncio.sleep(1)
            
            print(f"   📊 Successfully processed {success_count}/{len(chunks)} chunks")
            return success_count
            
        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    async def process_all_files_narrative(self):
        """Process all files with narrative depth"""
        txt_files = glob.glob(os.path.join(self.text_directory, "*.txt"))
        
        if not txt_files:
            print(f"No .txt files found in {self.text_directory}")
            return
        
        print(f"🔥 ENHANCED NARRATIVE ANALYSIS - GREAT FIRE OF SMYRNA")
        print(f"📚 Found {len(txt_files)} files to process with deep narrative analysis")
        print(f"🎭 Focus: Character arcs, story progression, thematic connections")
        print("=" * 80)
        
        total_chunks = 0
        total_files = 0
        
        # Sort files to maintain story sequence
        sorted_files = sorted(txt_files)
        
        for sequence, file_path in enumerate(sorted_files, 1):
            chunk_count = await self.process_file_with_narrative_depth(file_path, sequence)
            total_chunks += chunk_count
            if chunk_count > 0:
                total_files += 1
        
        print(f"\n" + "=" * 80)
        print(f"🎉 ENHANCED NARRATIVE INGESTION COMPLETE!")
        print(f"📊 Statistics:")
        print(f"   📁 Files processed: {total_files}/{len(txt_files)}")
        print(f"   📄 Narrative chunks created: {total_chunks}")
        print(f"   🎭 Deep character and story analysis complete")
        print(f"   🔍 Ready for advanced narrative querying!")
        print("=" * 80)
        
        return total_chunks
    
    def close(self):
        self.driver.close()

async def main():
    text_dir = input("Enter path to text files (or press Enter for '~/Downloads/chapters'): ").strip()
    if not text_dir:
        text_dir = "~/Downloads/chapters"
    
    text_dir = os.path.expanduser(text_dir)
    
    print("🚀 ENHANCED NARRATIVE ANALYSIS SYSTEM")
    print("🎭 Deep character arcs, story progression, and thematic analysis")
    print("=" * 60)
    
    processor = EnhancedNarrativeIngest(text_dir)
    await processor.process_all_files_narrative()
    processor.close()

if __name__ == "__main__":
    asyncio.run(main())