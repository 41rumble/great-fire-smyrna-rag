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
    
    def compress_knowledge(self, full_context: str, question: str) -> str:
        """Use LLM to intelligently compress large context while preserving relevant information"""
        compression_prompt = f"""You are a research assistant helping to extract and summarize relevant information.

QUESTION: {question}

LARGE CONTEXT TO COMPRESS:
{full_context}

Your task: Extract and compress the most relevant information to answer the question. Focus on:
1. Key characters mentioned in the question
2. Their roles, relationships, and actions relevant to the question
3. Important events and their consequences
4. Historical context needed to understand the situation

Provide a well-organized summary that preserves all essential information while removing redundancy and irrelevant details. Be comprehensive but concise."""

        try:
            # Use same model but with compression-focused parameters
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert research assistant who extracts and summarizes historical information efficiently and accurately."},
                    {"role": "user", "content": compression_prompt}
                ],
                "max_tokens": 1500,  # Longer for compression task
                "temperature": 0.3,  # More focused for summarization
                "frequency_penalty": 0.5,
                "presence_penalty": 0.3
            }
            
            response = requests.post(self.ollama_url, json=data)
            if response.status_code == 200:
                result = response.json()
                compressed = result['choices'][0]['message']['content']
                print(f"📊 Compressed from {len(full_context)} to {len(compressed)} characters ({len(compressed)/len(full_context)*100:.1f}%)")
                return compressed
            else:
                print(f"⚠️  Compression failed, using truncated context")
                return full_context[:8000]  # Fallback to truncation
        except Exception as e:
            print(f"⚠️  Compression error: {e}, using truncated context")
            return full_context[:8000]  # Fallback to truncation
    
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
            print(f"📊 Found {len(context_parts)} entities, using intelligent compression if needed")
            
            # DEBUG: Show what sources we're actually finding
            for i, part in enumerate(context_parts[:3]):
                print(f"SOURCE {i+1}: {part[:100]}...")
            
            # Intelligent compression: if we have too much context, compress it
            full_context = "\n\n".join(context_parts)
            
            # Update entity count tracking for server
            self.last_entities_found = len(context_parts)
            
            if len(full_context) > 8000:  # If context is large, compress it intelligently
                print("🗜️  Large context detected - using intelligent compression...")
                compressed_context = self.compress_knowledge(full_context, question)
                # Mark that compression was used
                self.compression_used = True
                return compressed_context
            else:
                self.compression_used = False
                return "\n\n".join(context_parts)  # Use all context if small enough
    
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