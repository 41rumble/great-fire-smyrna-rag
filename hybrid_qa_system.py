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
                {"role": "system", "content": "You are a knowledgeable historian providing detailed analysis of the Great Fire of Smyrna (1922). Write comprehensive, engaging responses that tell the historical story clearly and naturally. Use flowing narrative prose that weaves together information from multiple sources. Avoid bullet points, numbered lists, or overly formal academic structure."},
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
            
            # 1. HIGHEST PRIORITY: Search for specific characters mentioned
            character_found = False
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
                LIMIT 1
                """
                result = session.run(character_query, {"name": name, "normalized_name": normalized_name})
                for record in result:
                    char = record["character"]
                    relationships = record["relationships"]
                    character_found = True
                    
                    char_info = f"AUTHORITATIVE CHARACTER PROFILE: {char.get('name', 'Unknown')}\n"
                    char_info += f"OFFICIAL ROLE: {char.get('role', 'Unknown')}\n"
                    if char.get('nationality'): char_info += f"Nationality: {char['nationality']}\n"
                    if char.get('significance'): char_info += f"Historical Significance: {char['significance']}\n"
                    if char.get('motivations'): char_info += f"Motivations: {char['motivations']}\n"
                    if char.get('development'): char_info += f"Character Development: {char['development']}\n"
                    
                    # Add key relationships
                    if relationships and any(rel['other'] for rel in relationships[:5]):
                        char_info += "KEY HISTORICAL RELATIONSHIPS:\n"
                        for rel in relationships[:5]:
                            if rel['other']:
                                char_info += f"  → {rel['other']}: {rel.get('context', 'Connected')}\n"
                    
                    # Put character info FIRST
                    context_parts.insert(0, char_info)
            
            # 2. Search episodes for broader context - MODEST INCREASE
            for word in words[:4]:
                episode_query = """
                MATCH (e:Episode)
                WHERE toLower(e.content) CONTAINS $word
                RETURN e.name AS name, e.content AS content
                ORDER BY e.chapter_sequence
                LIMIT 4
                """  # Modest increase from 3 to 4 episodes per word
                result = session.run(episode_query, {"word": word})
                for record in result:
                    content = record["content"][:1500]  # Modest increase from 1200 to 1500 chars
                    context_parts.append(f"FROM {record['name']}:\n{content}")
            
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
            print(f"📊 Up to 15 entities (was 10), 4 episodes per word (was 3), 1500 chars (was 1200)")
            
            # DEBUG: Show what sources we're actually finding
            for i, part in enumerate(context_parts[:3]):
                print(f"SOURCE {i+1}: {part[:100]}...")
            
            return "\n\n".join(context_parts[:15])  # Modest increase from 10 to 15 total entities
    
    async def answer_question(self, question: str):
        """Answer question using hybrid approach"""
        print(f"❓ Question: {question}")
        
        # Try Graphiti semantic search first, fall back to manual
        context = await self.search_with_graphiti(question)
        
        if not context:
            context = self.search_manually(question)
        
        if not context:
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