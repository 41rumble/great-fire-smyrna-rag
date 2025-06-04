#!/usr/bin/env python3
"""
Test the impact of higher limits on answer quality and performance
"""

import time
from hybrid_qa_system import HybridQASystem
import asyncio

class HighLimitQASystem(HybridQASystem):
    def __init__(self, 
                 total_entities=20,      # Was 10
                 relationships_per_char=10,  # Was 5  
                 episodes_per_word=5,    # Was 3
                 events_per_word=3,      # Was 2
                 content_length=2000):   # Was 1200
        super().__init__()
        
        # Store the new limits
        self.total_entities = total_entities
        self.relationships_per_char = relationships_per_char  
        self.episodes_per_word = episodes_per_word
        self.events_per_word = events_per_word
        self.content_length = content_length
        
        print(f"🔧 MODIFIED LIMITS:")
        print(f"   Total entities: {total_entities} (was 10)")
        print(f"   Relationships per character: {relationships_per_char} (was 5)")
        print(f"   Episodes per word: {episodes_per_word} (was 3)")
        print(f"   Events per word: {events_per_word} (was 2)")
        print(f"   Content length: {content_length} chars (was 1200)")
    
    def search_manually(self, question: str):
        """Enhanced manual search with configurable limits"""
        print("🔍 Using enhanced Neo4j search with higher limits...")
        
        start_time = time.time()
        
        with self.driver.session(database="the-great-fire-db") as session:
            # Extract key entities from question
            key_names = []
            question_lower = question.lower()
            
            # Look for specific character names
            known_characters = ["atatürk", "ataturk", "kemal", "jennings", "bristol", "horton", "powell"]
            for char in known_characters:
                if char in question_lower:
                    key_names.append(char)
            
            # Also extract other significant words
            words = [w.lower().strip('.,?!') for w in question.split() if len(w) > 3 and w.lower() not in ['with', 'that', 'this', 'were', 'have', 'from']]
            
            # PRIORITY ORDER: Character nodes first, then episodes
            context_parts = []
            
            # 1. HIGHEST PRIORITY: Search for specific characters mentioned
            character_found = False
            for name in key_names:
                # Normalize the search name (remove accents, etc.)
                normalized_name = name.replace('ü', 'u').replace('ä', 'a').replace('ö', 'o')
                
                character_query = f"""
                MATCH (c:Character)
                WHERE toLower(c.name) CONTAINS $name 
                   OR toLower(c.name) CONTAINS $normalized_name
                   OR toLower(replace(replace(c.name, 'ü', 'u'), 'ä', 'a')) CONTAINS $name
                OPTIONAL MATCH (c)-[r:RELATES_TO]-(other)
                RETURN c AS character, collect({{other: other.name, relationship: r.type, context: r.narrative_context}}) as relationships
                LIMIT 1
                """
                result = session.run(character_query, {"name": name, "normalized_name": normalized_name})
                for record in result:
                    char = record["character"]
                    relationships = record["relationships"]
                    character_found = True
                    
                    char_info = f"AUTHORITATIVE CHARACTER PROFILE: {char.get('name', 'Unknown')}\\n"
                    char_info += f"OFFICIAL ROLE: {char.get('role', 'Unknown')}\\n"
                    if char.get('nationality'): char_info += f"Nationality: {char['nationality']}\\n"
                    if char.get('significance'): char_info += f"Historical Significance: {char['significance']}\\n"
                    if char.get('motivations'): char_info += f"Motivations: {char['motivations']}\\n"
                    if char.get('development'): char_info += f"Character Development: {char['development']}\\n"
                    
                    # Add key relationships - INCREASED LIMIT
                    if relationships and any(rel['other'] for rel in relationships[:self.relationships_per_char]):
                        char_info += "KEY HISTORICAL RELATIONSHIPS:\\n"
                        for rel in relationships[:self.relationships_per_char]:
                            if rel['other']:
                                char_info += f"  → {rel['other']}: {rel.get('context', 'Connected')}\\n"
                    
                    # Put character info FIRST
                    context_parts.insert(0, char_info)
            
            # 2. Search episodes for broader context - INCREASED LIMIT
            words_to_search = words[:6]  # Increased from 4
            for word in words_to_search:
                episode_query = f"""
                MATCH (e:Episode)
                WHERE toLower(e.content) CONTAINS $word
                RETURN e.name AS name, e.content AS content
                ORDER BY e.chapter_sequence
                LIMIT {self.episodes_per_word}
                """
                result = session.run(episode_query, {"word": word})
                for record in result:
                    content = record["content"][:self.content_length]  # INCREASED LENGTH
                    context_parts.append(f"FROM {record['name']}:\\n{content}")
            
            # 3. Search events related to the question - INCREASED LIMIT
            for word in words[:4]:  # Increased from 2
                event_query = f"""
                MATCH (ev:Event)
                WHERE toLower(ev.name) CONTAINS $word
                   OR toLower(ev.narrative_function) CONTAINS $word
                RETURN ev AS event
                LIMIT {self.events_per_word}
                """
                result = session.run(event_query, {"word": word})
                for record in result:
                    event = record["event"]
                    event_info = f"EVENT: {event.get('name', 'Unknown')}\\n"
                    if event.get('narrative_function'): event_info += f"Function: {event['narrative_function']}\\n"
                    if event.get('participants'): event_info += f"Participants: {event['participants']}\\n"
                    if event.get('consequences'): event_info += f"Consequences: {event['consequences']}\\n"
                    context_parts.append(event_info)
            
            search_time = time.time() - start_time
            print(f"🔍 Found {len(context_parts)} context sources in {search_time:.2f}s")
            
            # Show context size
            total_context = "\\n\\n".join(context_parts[:self.total_entities])
            context_size = len(total_context)
            print(f"📏 Total context size: {context_size:,} characters")
            
            # DEBUG: Show what sources we're actually finding
            for i, part in enumerate(context_parts[:5]):  # Show more for debugging
                print(f"SOURCE {i+1}: {part[:150]}...")
            
            return total_context

async def test_limits():
    """Test different limit configurations"""
    
    test_question = "What was Asa Jennings' role in the evacuation?"
    
    print("🧪 TESTING DIFFERENT LIMIT CONFIGURATIONS")
    print("=" * 70)
    
    # Test configurations
    configs = [
        {"name": "CURRENT", "total_entities": 10, "relationships_per_char": 5, "episodes_per_word": 3, "events_per_word": 2, "content_length": 1200},
        {"name": "MODERATE", "total_entities": 20, "relationships_per_char": 10, "episodes_per_word": 5, "events_per_word": 3, "content_length": 2000},
        {"name": "HIGH", "total_entities": 50, "relationships_per_char": 20, "episodes_per_word": 10, "events_per_word": 5, "content_length": 3000},
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\\n{i}. TESTING {config['name']} LIMITS")
        print("-" * 50)
        
        try:
            # Create system with these limits
            qa_system = HighLimitQASystem(**{k: v for k, v in config.items() if k != 'name'})
            
            start_time = time.time()
            answer = await qa_system.answer_question(test_question)
            total_time = time.time() - start_time
            
            # Analyze results
            answer_length = len(answer.split())
            context_quality = "❌ Failed" if answer.startswith("I couldn't find") else "✅ Success"
            
            print(f"⏱️  Total time: {total_time:.2f}s")
            print(f"📊 Answer length: {answer_length} words")
            print(f"🎯 Status: {context_quality}")
            print(f"🔍 Answer preview: {answer[:200]}...")
            
            qa_system.close()
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
    
    print("\\n" + "=" * 70)
    print("🏁 LIMIT TESTING COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_limits())