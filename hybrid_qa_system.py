import os
import asyncio
import requests
from dotenv import load_dotenv

load_dotenv()

# Only set OpenAI key if doing Graphiti search, but not required
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

if False:  # Disabled graphiti import
    os.environ["OPENAI_API_KEY"] = OPENAI_KEY
    # from graphiti_core import Graphiti

from neo4j import GraphDatabase

class HybridQASystem:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        self.ollama_url = "http://localhost:11434/v1/chat/completions"
        self.model = "mistral-small3.1:latest"
        self.last_entities_found = 0  # Track entity count for server reporting
        self.compression_used = False  # Track if compression was used
        
        # Disable Graphiti for now due to schema mismatch
        self.use_graphiti = False
        if False:  # self.use_graphiti:
            try:
                self.graphiti = Graphiti(
                    uri=os.getenv("NEO4J_URI"),
                    user=os.getenv("NEO4J_USERNAME"),
                    password=os.getenv("NEO4J_PASSWORD")
                )
                print("✅ Graphiti semantic search enabled")
            except Exception as e:
                print(f"⚠️  Graphiti unavailable, falling back to manual search: {e}")
                self.use_graphiti = False
        else:
            print("ℹ️  Using manual search (set OPENAI_API_KEY for Graphiti semantic search)")
    
    def call_ollama(self, prompt: str, max_tokens: int = 1200) -> str:
        """Call local Ollama for private Q&A"""
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a knowledgeable historian providing detailed analysis of the Great Fire of Smyrna (1922). Write comprehensive, engaging responses that tell the historical story clearly and naturally. Use flowing narrative prose that weaves together information from multiple sources. Avoid bullet points, numbered lists, repetitive phrases, or overly formal academic structure. Be concise and avoid repeating the same information."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.5,
            "top_p": 0.9,
            "frequency_penalty": 1.2,
            "presence_penalty": 0.8
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
    
    def batch_compress_episodes(self, episodes: list, question: str) -> list:
        """Compress multiple episodes in one fast LLM call"""
        if not episodes:
            return []
        
        # Build batch compression prompt
        episodes_text = ""
        for i, ep in enumerate(episodes, 1):
            episodes_text += f"\n--- EPISODE {i}: {ep['name']} ---\n{ep['content'][:3000]}\n"  # Limit each episode to 3000 chars
        
        batch_prompt = f"""QUESTION: {question}

Extract ONLY relevant information from these episodes to answer the question. For each episode, provide a focused summary of relevant content.

{episodes_text}

For each episode, write: "FROM [episode_name]: [relevant summary]" 
Focus only on information that helps answer the question. Be concise but preserve key details."""

        try:
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Extract relevant information efficiently. Write focused summaries for each episode."},
                    {"role": "user", "content": batch_prompt}
                ],
                "max_tokens": 1200,  # Reasonable limit for batch processing
                "temperature": 0.2,
                "frequency_penalty": 0.4,
                "presence_penalty": 0.3
            }
            
            response = requests.post(self.ollama_url, json=data)
            if response.status_code == 200:
                result = response.json()
                compressed_batch = result['choices'][0]['message']['content']
                print(f"📦 Batch compressed {len(episodes)} large episodes in one call")
                
                # Split the response back into individual episode summaries
                return [compressed_batch]  # Return as single block for now
            else:
                print(f"⚠️  Batch compression failed, using truncated episodes")
                return [f"FROM {ep['name']} (truncated):\n{ep['content'][:800]}" for ep in episodes]
                
        except Exception as e:
            print(f"⚠️  Batch compression error: {e}")
            return [f"FROM {ep['name']} (truncated):\n{ep['content'][:800]}" for ep in episodes]
    
    async def search_with_graphiti(self, question: str):
        """Use Graphiti's semantic search (if available)"""
        if not self.use_graphiti:
            return None
        
        try:
            print("🧠 Using Graphiti semantic search...")
            results = await self.graphiti.search(question)
            
            if results:
                # Graphiti returns rich, structured results
                context_parts = []
                for i, result in enumerate(results[:5]):
                    # Extract content from Graphiti result
                    content = str(result)[:1000]  # Adjust based on actual structure
                    context_parts.append(f"SOURCE {i+1}:\n{content}")
                
                return "\n\n".join(context_parts)
            
        except Exception as e:
            print(f"⚠️  Graphiti search error: {e}")
        
        return None
    
    def search_manually(self, question: str):
        """Enhanced manual search using Neo4j with comprehensive entity lookup"""
        print("🔍 Using enhanced Neo4j search...")
        
        with self.driver.session(database="the-great-fire-db") as session:
            # Extract key entities from question
            key_names = []
            question_lower = question.lower()
            
            # Look for specific character names and related terms
            known_characters = ["atatürk", "ataturk", "kemal", "jennings", "bristol", "horton", "powell"]
            for char in known_characters:
                if char in question_lower:
                    key_names.append(char)
            
            # Add related search terms for better context discovery
            if any(term in question_lower for term in ["atatürk", "turkish", "turkey"]):
                key_names.extend(["bristol", "american", "republic"])
            if "american" in question_lower and "officials" in question_lower:
                key_names.extend(["bristol", "engagement", "policy"])
            if "humanitarian" in question_lower:
                key_names.extend(["relief", "organization", "jennings"])
            
            # Also extract other significant words
            words = [w.lower().strip('.,?!') for w in question.split() if len(w) > 3 and w.lower() not in ['with', 'that', 'this', 'were', 'have', 'from']]
            
            # PRIORITY ORDER: Character nodes first, then episodes
            context_parts = []
            
            # 1. BALANCED CHARACTER SEARCH: Find all relevant characters, not just first match
            character_profiles = []
            for name in key_names:
                # Normalize the search name (remove accents, etc.)
                normalized_name = name.replace('ü', 'u').replace('ä', 'a').replace('ö', 'o')
                
                character_query = """
                MATCH (c:Character)
                WHERE toLower(c.name) CONTAINS $name 
                   OR toLower(c.name) CONTAINS $normalized_name
                   OR toLower(replace(replace(c.name, 'ü', 'u'), 'ä', 'a')) CONTAINS $name
                OPTIONAL MATCH (c)-[r:RELATES_TO]-(other)
                RETURN c AS character, collect({other: other.name, relationship: r.type, context: r.narrative_context}) as relationships
                ORDER BY c.name
                """
                result = session.run(character_query, {"name": name, "normalized_name": normalized_name})
                
                for record in result:
                    char = record["character"]
                    relationships = record["relationships"]
                    
                    char_info = f"CHARACTER: {char.get('name', 'Unknown')}\n"
                    char_info += f"Role: {char.get('role', 'Unknown')}\n"
                    if char.get('nationality'): char_info += f"Nationality: {char['nationality']}\n"
                    if char.get('significance'): char_info += f"Significance: {char['significance'][:200]}...\n" if len(char.get('significance', '')) > 200 else f"Significance: {char.get('significance', '')}\n"
                    
                    # Add condensed relationships for balanced coverage
                    if relationships and any(rel['other'] for rel in relationships[:3]):
                        char_info += "Key Relationships: "
                        rel_list = [f"{rel['other']}" for rel in relationships[:3] if rel['other']]
                        char_info += ", ".join(rel_list) + "\n"
                    
                    character_profiles.append(char_info)
            
            # Add character profiles with balanced priority
            context_parts.extend(character_profiles)
            
            # 1b. BROADER CHARACTER DISCOVERY: For questions about groups/roles
            if any(term in question_lower for term in ["officials", "americans", "turkish", "military", "diplomatic"]):
                broader_char_query = """
                MATCH (c:Character)
                WHERE toLower(c.role) CONTAINS 'official' 
                   OR toLower(c.role) CONTAINS 'officer'
                   OR toLower(c.role) CONTAINS 'ambassador'
                   OR toLower(c.role) CONTAINS 'minister'
                   OR toLower(c.nationality) CONTAINS 'american'
                   OR toLower(c.nationality) CONTAINS 'turkish'
                RETURN c.name as name, c.role as role, c.nationality as nationality
                ORDER BY c.name
                LIMIT 6
                """
                result = session.run(broader_char_query)
                for record in result:
                    context_parts.append(f"OFFICIAL: {record['name']} - {record['role']} ({record['nationality']})")
            
            # 2. Search episodes for broader context - STREAMLINED  
            large_episodes = []
            small_episodes = []
            
            for word in words[:3]:  # Reduced from 4 to 3 words for speed
                episode_query = """
                MATCH (e:Episode)
                WHERE toLower(e.content) CONTAINS $word
                RETURN e.name AS name, e.content AS content
                ORDER BY e.chapter_sequence
                LIMIT 3
                """  # Reduced to 3 episodes per word for speed
                result = session.run(episode_query, {"word": word})
                for record in result:
                    full_content = record["content"]
                    episode_name = record["name"]
                    
                    if len(full_content) > 2000:  # Large episode
                        large_episodes.append({"name": episode_name, "content": full_content})
                    else:
                        # Small episodes go directly to context
                        small_episodes.append(f"FROM {episode_name}:\n{full_content}")
            
            # Add small episodes first
            context_parts.extend(small_episodes)
            
            # BATCH compress large episodes (max 4 to avoid timeout)
            if large_episodes:
                compressed_episodes = self.batch_compress_episodes(large_episodes[:4], question)
                context_parts.extend(compressed_episodes)
            
            # 3. Search events related to the question
            for word in words[:2]:
                event_query = """
                MATCH (ev:Event)
                WHERE toLower(ev.name) CONTAINS $word
                   OR toLower(ev.narrative_function) CONTAINS $word
                RETURN ev AS event
                LIMIT 2
                """
                result = session.run(event_query, {"word": word})
                for record in result:
                    event = record["event"]
                    event_info = f"EVENT: {event.get('name', 'Unknown')}\n"
                    if event.get('narrative_function'): event_info += f"Function: {event['narrative_function']}\n"
                    if event.get('participants'): event_info += f"Participants: {event['participants']}\n"
                    if event.get('consequences'): event_info += f"Consequences: {event['consequences']}\n"
                    context_parts.append(event_info)
            
            print(f"🔍 Found {len(context_parts)} context sources")
            if large_episodes:
                print(f"📦 Streamlined: {len(large_episodes)} large episodes batch-compressed, {len(small_episodes)} small episodes kept full")
            else:
                print(f"📦 All episodes small enough - no compression needed")
            
            # DEBUG: Show what sources we're actually finding
            for i, part in enumerate(context_parts[:3]):
                print(f"SOURCE {i+1}: {part[:100]}...")
            
            # Set entity count and return assembled context
            self.last_entities_found = len(context_parts)
            final_context = "\n\n".join(context_parts)
            
            print(f"📊 Final context: {len(final_context)} characters from {self.last_entities_found} entities")
            
            return final_context
    
    async def answer_question(self, question: str):
        """Answer question using hybrid approach"""
        print(f"❓ Question: {question}")
        
        # Initialize entity count
        self.last_entities_found = 0
        
        # Try Graphiti semantic search first, fall back to manual
        context = await self.search_with_graphiti(question)
        
        if not context:
            context = self.search_manually(question)
        else:
            # If Graphiti was used, set a default entity count
            self.last_entities_found = 5  # Default for Graphiti results
        
        if not context:
            self.last_entities_found = 0
            return "I couldn't find relevant information to answer your question."
        
        # Create narrative prompt
        prompt = f"""Question: {question}

Historical sources and context:

{context}

Answer this question by weaving together the information from these sources into a clear, engaging narrative. Write in flowing prose that tells the historical story naturally, avoiding bullet points or numbered lists. If there's an "AUTHORITATIVE CHARACTER PROFILE" in the sources, prioritize that biographical information over episode excerpts."""
        
        print("🤔 Generating answer with local Ollama...")
        answer = self.call_ollama(prompt, 1200)
        
        return answer
    
    def close(self):
        self.driver.close()

async def main():
    qa_system = HybridQASystem()
    
    print("🔥 HYBRID GREAT FIRE OF SMYRNA Q&A SYSTEM")
    print("=" * 60)
    if qa_system.use_graphiti:
        print("🧠 Semantic Search: OpenAI-powered Graphiti")
    else:
        print("🔍 Search: Manual Neo4j queries")
    print("💬 Answer Generation: Local Ollama (private)")
    print("=" * 60)
    
    print("\nExample questions:")
    print("• What was the nature of Atatürk and Jennings' relationship?")
    print("• How did the American relief effort organize the evacuation?")
    print("• What role did the Turkish military play in the events?")
    print("• How did international diplomacy affect the crisis?")
    print("• What were the long-term consequences of the Great Fire?")
    
    while True:
        question = input("\n❓ Your question (or 'quit' to exit): ").strip()
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if len(question) < 5:
            print("Please ask a more detailed question.")
            continue
            
        print()
        answer = await qa_system.answer_question(question)
        print("💡 Answer:")
        print("-" * 60)
        print(answer)
        print("-" * 60)
    
    qa_system.close()

if __name__ == "__main__":
    asyncio.run(main())