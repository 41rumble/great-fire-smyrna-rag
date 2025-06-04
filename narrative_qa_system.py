import os
import requests
from neo4j import GraphDatabase

class NarrativeQASystem:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        self.ollama_url = "http://localhost:11434/v1/chat/completions"
        self.model = "mistral-small3.1:latest"
    
    def call_ollama(self, prompt: str, max_tokens: int = 1500) -> str:
        """Call Ollama for narrative analysis"""
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a literary analyst and historian specializing in narrative structure, character development, and thematic analysis. You provide deep insights into story arcs, character motivations, and historical context."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.6,
            "top_p": 0.95,
            "frequency_penalty": 0.8,
            "presence_penalty": 0.4
        }
        
        try:
            response = requests.post(self.ollama_url, json=data)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    def analyze_character_arc(self, character_name: str):
        """Analyze a character's development throughout the story"""
        with self.driver.session(database="the-great-fire-db") as session:
            # Get character's appearances across chapters
            character_query = """
            MATCH (c:Character {name: $name})<-[:MENTIONS]-(ep:Episode)
            RETURN c, ep.chapter_sequence as sequence, ep.chapter_title as chapter, 
                   ep.story_arc_position as position, ep.content as content
            ORDER BY ep.chapter_sequence
            """
            
            result = session.run(character_query, {"name": character_name})
            appearances = []
            
            for record in result:
                character_data = dict(record["c"])
                appearances.append({
                    "sequence": record["sequence"],
                    "chapter": record["chapter"],
                    "position": record["position"],
                    "content": record["content"][:800],
                    "character_data": character_data
                })
            
            if not appearances:
                return f"Character '{character_name}' not found in the story."
            
            # Get character relationships
            relationships_query = """
            MATCH (c:Character {name: $name})-[r:RELATES_TO]->(other)
            RETURN other.name as other_name, r.type as relationship, 
                   r.emotional_dimension as emotion, r.story_importance as importance,
                   r.chapter as chapter
            ORDER BY r.story_importance DESC
            """
            
            result = session.run(relationships_query, {"name": character_name})
            relationships = [dict(record) for record in result]
            
            return self.generate_character_analysis(character_name, appearances, relationships)
    
    def analyze_story_progression(self, focus_theme: str = ""):
        """Analyze how the story progresses through different acts"""
        with self.driver.session(database="the-great-fire-db") as session:
            progression_query = """
            MATCH (ep:Episode)
            RETURN ep.story_arc_position as position, ep.chapter_sequence as sequence,
                   ep.chapter_title as title, ep.narrative_importance as importance,
                   count(*) as episode_count
            ORDER BY ep.chapter_sequence
            """
            
            result = session.run(progression_query)
            story_structure = [dict(record) for record in result]
            
            # Get major events by story position
            events_query = """
            MATCH (e:Event)<-[:MENTIONS]-(ep:Episode)
            WHERE e.story_turning_point = 'true'
            RETURN e.name as event, e.narrative_function as function,
                   ep.story_arc_position as position, ep.chapter_sequence as sequence,
                   e.consequences as consequences
            ORDER BY ep.chapter_sequence
            """
            
            result = session.run(events_query)
            major_events = [dict(record) for record in result]
            
            return self.generate_story_analysis(story_structure, major_events, focus_theme)
    
    def explore_relationships(self, entity1: str, entity2: str = ""):
        """Explore relationships between entities or all relationships for one entity"""
        with self.driver.session(database="the-great-fire-db") as session:
            if entity2:
                # Specific relationship between two entities
                relationship_query = """
                MATCH (a:Entity {name: $entity1})-[r:RELATES_TO]-(b:Entity {name: $entity2})
                RETURN a.name as entity1, b.name as entity2, r.type as relationship,
                       r.narrative_context as context, r.emotional_dimension as emotion,
                       r.power_dynamic as power, r.story_importance as importance,
                       r.evidence as evidence, r.chapter as chapter
                """
                
                result = session.run(relationship_query, {"entity1": entity1, "entity2": entity2})
                relationships = [dict(record) for record in result]
                
                if not relationships:
                    return f"No direct relationship found between '{entity1}' and '{entity2}'."
                
                return self.generate_relationship_analysis(relationships, entity1, entity2)
            else:
                # All relationships for one entity
                all_relationships_query = """
                MATCH (a:Entity {name: $entity1})-[r:RELATES_TO]-(b:Entity)
                RETURN a.name as entity1, b.name as entity2, r.type as relationship,
                       r.narrative_context as context, r.emotional_dimension as emotion,
                       r.story_importance as importance, b.category as other_category
                ORDER BY r.story_importance DESC, r.chapter
                LIMIT 15
                """
                
                result = session.run(all_relationships_query, {"entity1": entity1})
                relationships = [dict(record) for record in result]
                
                if not relationships:
                    return f"No relationships found for '{entity1}'."
                
                return self.generate_entity_network_analysis(entity1, relationships)
    
    def analyze_themes(self, theme_focus: str = ""):
        """Analyze how themes develop throughout the story"""
        with self.driver.session(database="the-great-fire-db") as session:
            themes_query = """
            MATCH (t:Theme)<-[:MENTIONS]-(ep:Episode)
            RETURN t.theme as theme, t.how_expressed as expression,
                   t.character_connection as characters,
                   ep.story_arc_position as position, ep.chapter_sequence as sequence,
                   ep.chapter_title as chapter
            ORDER BY ep.chapter_sequence
            """
            
            result = session.run(themes_query)
            theme_development = [dict(record) for record in result]
            
            if not theme_development:
                return "No thematic analysis found in the database."
            
            return self.generate_thematic_analysis(theme_development, theme_focus)
    
    def trace_temporal_flow(self, start_event: str = "", time_period: str = ""):
        """Trace how events unfold over time"""
        with self.driver.session(database="the-great-fire-db") as session:
            temporal_query = """
            MATCH (tm:Temporal_marker)<-[:MENTIONS]-(ep:Episode)
            RETURN tm.time_reference as time, tm.narrative_moment as moment,
                   tm.story_pacing as pacing, tm.temporal_relationship as relationship,
                   ep.chapter_sequence as sequence, ep.chapter_title as chapter
            ORDER BY ep.chapter_sequence
            """
            
            result = session.run(temporal_query)
            temporal_flow = [dict(record) for record in result]
            
            # Get events with temporal context
            events_temporal_query = """
            MATCH (e:Event)<-[:MENTIONS]-(ep:Episode)
            WHERE e.date_mentioned IS NOT NULL
            RETURN e.name as event, e.date_mentioned as date,
                   e.narrative_function as function, e.consequences as consequences,
                   ep.chapter_sequence as sequence
            ORDER BY ep.chapter_sequence
            """
            
            result = session.run(events_temporal_query)
            events_timeline = [dict(record) for record in result]
            
            return self.generate_temporal_analysis(temporal_flow, events_timeline, start_event, time_period)
    
    def generate_character_analysis(self, character_name: str, appearances: list, relationships: list) -> str:
        """Generate deep character analysis"""
        context = f"CHARACTER ANALYSIS FOR: {character_name}\n\n"
        
        # Character development across chapters
        context += "CHARACTER APPEARANCES:\n"
        for app in appearances:
            context += f"Chapter {app['sequence']}: {app['chapter']} ({app['position']})\n"
            if app['character_data']:
                for key, value in app['character_data'].items():
                    if key not in ['name', 'category'] and value:
                        context += f"  {key}: {value}\n"
            context += f"  Content excerpt: {app['content'][:300]}...\n\n"
        
        # Key relationships
        context += "KEY RELATIONSHIPS:\n"
        for rel in relationships[:8]:
            context += f"With {rel['other_name']}: {rel['relationship']} ({rel['importance']} importance)\n"
            if rel['emotion']:
                context += f"  Emotional dimension: {rel['emotion']}\n"
            context += f"  Chapter: {rel['chapter']}\n\n"
        
        prompt = f"""Analyze this character's arc and development throughout "The Great Fire of Smyrna":

{context}

Provide a comprehensive character analysis that includes:

1. Character Arc Overview: How does this character develop and change throughout the story?
2. Motivations and Goals: What drives this character? How do their motivations evolve?
3. Key Relationships: How do their relationships with others shape their journey?
4. Role in the Historical Narrative: What is their significance to the broader historical events?
5. Emotional Journey: What emotional transformation do they undergo?
6. Thematic Significance: What themes or ideas does this character represent?

Write in a narrative, engaging style that brings the character to life while maintaining historical accuracy."""
        
        return self.call_ollama(prompt, 1800)
    
    def generate_story_analysis(self, story_structure: list, major_events: list, focus_theme: str) -> str:
        """Generate story progression analysis"""
        context = "STORY STRUCTURE ANALYSIS:\n\n"
        
        # Story arc breakdown
        arc_positions = {}
        for item in story_structure:
            position = item['position']
            if position not in arc_positions:
                arc_positions[position] = []
            arc_positions[position].append(item)
        
        context += "STORY ARC BREAKDOWN:\n"
        for position in ['setup', 'rising_action', 'climax', 'resolution']:
            if position in arc_positions:
                context += f"\n{position.upper()}:\n"
                for item in arc_positions[position][:5]:
                    context += f"  Chapter {item['sequence']}: {item['title']} (importance: {item['importance']})\n"
        
        context += "\nMAJOR TURNING POINTS:\n"
        for event in major_events:
            context += f"Chapter {event['sequence']} ({event['position']}): {event['event']}\n"
            context += f"  Function: {event['function']}\n"
            if event['consequences']:
                context += f"  Consequences: {event['consequences']}\n"
            context += "\n"
        
        focus_prompt = f" with special focus on {focus_theme}" if focus_theme else ""
        
        prompt = f"""Analyze the narrative structure and story progression of "The Great Fire of Smyrna"{focus_prompt}:

{context}

Provide a comprehensive analysis that includes:

1. Overall Narrative Arc: How is the story structured across setup, rising action, climax, and resolution?
2. Pacing and Tension: How does tension build throughout the narrative?
3. Key Turning Points: What are the most significant moments that drive the story forward?
4. Thematic Development: How do major themes emerge and develop?
5. Historical Context Integration: How are historical events woven into the narrative structure?
6. Emotional Journey: What is the overall emotional trajectory of the story?

Write as a literary analyst examining both the historical accuracy and narrative craft."""
        
        return self.call_ollama(prompt, 1800)
    
    def generate_relationship_analysis(self, relationships: list, entity1: str, entity2: str) -> str:
        """Generate relationship analysis between two entities"""
        context = f"RELATIONSHIP ANALYSIS: {entity1} and {entity2}\n\n"
        
        for rel in relationships:
            context += f"Relationship Type: {rel['relationship']}\n"
            context += f"Context: {rel['context']}\n"
            if rel['emotion']:
                context += f"Emotional Dimension: {rel['emotion']}\n"
            if rel['power']:
                context += f"Power Dynamic: {rel['power']}\n"
            context += f"Story Importance: {rel['importance']}\n"
            context += f"Evidence: {rel['evidence']}\n"
            context += f"Chapter: {rel['chapter']}\n\n"
        
        prompt = f"""Analyze the relationship between {entity1} and {entity2} in "The Great Fire of Smyrna":

{context}

Provide a detailed analysis that explores:

1. Nature of the Relationship: What is the fundamental dynamic between these two?
2. Evolution Over Time: How does their relationship change throughout the story?
3. Power Dynamics: Who has influence over whom, and how does this shift?
4. Emotional Dimensions: What are the emotional undercurrents in their interactions?
5. Impact on the Story: How does this relationship drive the narrative forward?
6. Historical Context: How does their relationship reflect the broader historical situation?
7. Symbolic Significance: What larger themes or ideas does this relationship represent?

Write with depth and nuance, considering both the personal and historical dimensions."""
        
        return self.call_ollama(prompt, 1500)
    
    def generate_entity_network_analysis(self, entity: str, relationships: list) -> str:
        """Generate network analysis for an entity"""
        context = f"RELATIONSHIP NETWORK FOR: {entity}\n\n"
        
        # Group by relationship type
        rel_types = {}
        for rel in relationships:
            rel_type = rel['relationship']
            if rel_type not in rel_types:
                rel_types[rel_type] = []
            rel_types[rel_type].append(rel)
        
        for rel_type, rels in rel_types.items():
            context += f"{rel_type} RELATIONSHIPS:\n"
            for rel in rels:
                context += f"  With {rel['entity2']} ({rel['other_category']}): {rel['context']}\n"
            context += "\n"
        
        prompt = f"""Analyze the relationship network and influence of {entity} in "The Great Fire of Smyrna":

{context}

Provide an analysis that covers:

1. Central Role: What is this entity's central function in the story?
2. Sphere of Influence: Who and what does this entity affect or control?
3. Relationship Patterns: What patterns emerge in how this entity relates to others?
4. Network Position: Is this entity a connector, leader, victim, or catalyst?
5. Story Function: How does this entity's network of relationships drive the plot?
6. Character/Entity Development: How do these relationships shape this entity's journey?

Focus on both the individual relationships and the overall pattern of connections."""
        
        return self.call_ollama(prompt, 1500)
    
    def generate_thematic_analysis(self, theme_development: list, theme_focus: str) -> str:
        """Generate thematic analysis"""
        context = "THEMATIC DEVELOPMENT ANALYSIS:\n\n"
        
        # Group themes by story position
        themes_by_position = {}
        for item in theme_development:
            position = item['position']
            if position not in themes_by_position:
                themes_by_position[position] = []
            themes_by_position[position].append(item)
        
        for position in ['setup', 'rising_action', 'climax', 'resolution']:
            if position in themes_by_position:
                context += f"\n{position.upper()} THEMES:\n"
                for item in themes_by_position[position]:
                    context += f"  {item['theme']}: {item['expression']}\n"
                    if item['characters']:
                        context += f"    Characters: {item['characters']}\n"
                    context += f"    Chapter: {item['chapter']}\n\n"
        
        focus_prompt = f" with particular attention to {theme_focus}" if theme_focus else ""
        
        prompt = f"""Analyze the thematic development in "The Great Fire of Smyrna"{focus_prompt}:

{context}

Provide a comprehensive thematic analysis that includes:

1. Major Themes: What are the central themes explored in the narrative?
2. Thematic Evolution: How do these themes develop and deepen throughout the story?
3. Character-Theme Connections: How do different characters embody or explore different themes?
4. Historical-Thematic Integration: How do the themes relate to the historical events?
5. Symbolic Elements: What symbols or motifs support the thematic development?
6. Modern Relevance: How do these historical themes connect to contemporary issues?

Write as a literary scholar examining both the artistic and historical dimensions of the work."""
        
        return self.call_ollama(prompt, 1800)
    
    def generate_temporal_analysis(self, temporal_flow: list, events_timeline: list, start_event: str, time_period: str) -> str:
        """Generate temporal flow analysis"""
        context = "TEMPORAL FLOW ANALYSIS:\n\n"
        
        context += "STORY PACING:\n"
        for item in temporal_flow:
            context += f"Chapter {item['sequence']}: {item['chapter']}\n"
            context += f"  Time: {item['time']}\n"
            context += f"  Moment: {item['moment']}\n"
            context += f"  Pacing: {item['pacing']}\n"
            if item['relationship']:
                context += f"  Temporal relationship: {item['relationship']}\n"
            context += "\n"
        
        context += "EVENTS TIMELINE:\n"
        for event in events_timeline:
            context += f"Chapter {event['sequence']}: {event['event']}\n"
            context += f"  Date: {event['date']}\n"
            context += f"  Function: {event['function']}\n"
            if event['consequences']:
                context += f"  Consequences: {event['consequences']}\n"
            context += "\n"
        
        focus_prompts = []
        if start_event:
            focus_prompts.append(f"starting from {start_event}")
        if time_period:
            focus_prompts.append(f"focusing on {time_period}")
        
        focus_text = " " + " and ".join(focus_prompts) if focus_prompts else ""
        
        prompt = f"""Analyze the temporal structure and flow of "The Great Fire of Smyrna"{focus_text}:

{context}

Provide an analysis that explores:

1. Temporal Structure: How is time organized and presented in the narrative?
2. Pacing Variations: Where does the story slow down or speed up, and why?
3. Historical Timeline: How do historical dates and events structure the narrative?
4. Cause and Effect: How do events in different time periods connect and influence each other?
5. Temporal Tension: How does the passage of time create suspense or urgency?
6. Memory and Reflection: How do past events influence present actions?

Focus on both the chronological progression and the narrative techniques used to manage time."""
        
        return self.call_ollama(prompt, 1800)
    
    def comprehensive_query(self, question: str):
        """Handle complex narrative queries"""
        # Determine query type and route appropriately
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['character', 'jennings', 'atatürk', 'horton']):
            # Extract character name
            for word in question.split():
                if word.strip('.,?!').title() in ['Jennings', 'Atatürk', 'Horton', 'Kemal']:
                    return self.analyze_character_arc(word.strip('.,?!'))
        
        elif any(word in question_lower for word in ['story', 'plot', 'narrative', 'structure']):
            theme = ""
            if 'refugee' in question_lower or 'evacuation' in question_lower:
                theme = "refugee crisis"
            elif 'diplomatic' in question_lower or 'international' in question_lower:
                theme = "international relations"
            return self.analyze_story_progression(theme)
        
        elif any(word in question_lower for word in ['relationship', 'between', 'and']):
            # Try to extract two entities
            words = question.split()
            entities = [w.strip('.,?!') for w in words if w[0].isupper() and len(w) > 3]
            if len(entities) >= 2:
                return self.explore_relationships(entities[0], entities[1])
            elif len(entities) == 1:
                return self.explore_relationships(entities[0])
        
        elif any(word in question_lower for word in ['theme', 'meaning', 'significance']):
            theme_focus = ""
            if 'humanitarian' in question_lower:
                theme_focus = "humanitarian crisis"
            elif 'cultural' in question_lower:
                theme_focus = "cultural conflict"
            return self.analyze_themes(theme_focus)
        
        elif any(word in question_lower for word in ['time', 'when', 'chronology', 'timeline']):
            return self.trace_temporal_flow()
        
        else:
            # General search and analysis
            return self.general_narrative_search(question)
    
    def general_narrative_search(self, question: str):
        """General search with narrative focus"""
        with self.driver.session(database="the-great-fire-db") as session:
            # Search across episodes with narrative metadata
            search_terms = [w.lower() for w in question.split() if len(w) > 3]
            
            episodes = []
            for term in search_terms[:3]:
                episode_query = """
                MATCH (ep:Episode)
                WHERE toLower(ep.content) CONTAINS $term
                RETURN ep.name as name, ep.content as content, ep.chapter_title as chapter,
                       ep.story_arc_position as position, ep.narrative_importance as importance
                ORDER BY ep.narrative_importance DESC, ep.chapter_sequence
                LIMIT 3
                """
                result = session.run(episode_query, {"term": term})
                for record in result:
                    episodes.append(dict(record))
            
            if not episodes:
                return "I couldn't find relevant information to answer your question."
            
            # Build context
            context = "RELEVANT NARRATIVE CONTENT:\n\n"
            for ep in episodes[:4]:
                context += f"From {ep['chapter']} ({ep['position']}, {ep['importance']} importance):\n"
                context += f"{ep['content'][:1000]}...\n\n"
            
            prompt = f"""Answer this question about "The Great Fire of Smyrna" using the narrative context provided:

Question: {question}

{context}

Provide a comprehensive answer that considers:
- Character development and motivations
- Historical context and significance  
- Narrative themes and meaning
- Relationships between people and events
- The broader story arc and progression

Write in an engaging, analytical style that brings the story to life."""
            
            return self.call_ollama(prompt, 1500)
    
    def close(self):
        self.driver.close()

def main():
    qa_system = NarrativeQASystem()
    
    print("🎭 NARRATIVE ANALYSIS SYSTEM - THE GREAT FIRE OF SMYRNA")
    print("=" * 70)
    print("Deep analysis of character arcs, story progression, and thematic development")
    print("\nSpecialty Analyses:")
    print("📚 Character Arc Analysis: 'Analyze Jennings character development'")
    print("📖 Story Progression: 'How does the story structure unfold?'")
    print("🔗 Relationship Analysis: 'What is the relationship between Atatürk and Jennings?'")
    print("🎨 Thematic Analysis: 'What are the major themes about humanitarian crisis?'")
    print("⏰ Temporal Analysis: 'How do events unfold chronologically?'")
    print("=" * 70)
    
    while True:
        question = input("\n🎭 Your narrative question (or 'quit' to exit): ").strip()
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if len(question) < 5:
            print("Please ask a more detailed question for narrative analysis.")
            continue
        
        print("\n🤔 Analyzing narrative elements...")
        answer = qa_system.comprehensive_query(question)
        print("\n📖 Narrative Analysis:")
        print("-" * 70)
        print(answer)
        print("-" * 70)
    
    qa_system.close()

if __name__ == "__main__":
    main()