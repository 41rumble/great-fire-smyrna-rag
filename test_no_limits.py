#!/usr/bin/env python3
"""
Test removing limits completely - see what happens!
"""

import time
import requests
from neo4j import GraphDatabase
import asyncio

class NoLimitsQASystem:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        self.ollama_url = "http://localhost:11434/v1/chat/completions"
        self.model = "mistral-small3.1:latest"
        
        print("🚨 NO LIMITS QA SYSTEM - TESTING WHAT HAPPENS!")
        print("🔓 All limits removed - let's see what breaks...")
    
    def call_ollama(self, prompt: str, max_tokens: int = 2000) -> str:
        """Call local Ollama with higher token limit"""
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a knowledgeable historian providing detailed analysis of the Great Fire of Smyrna (1922)."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.4
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
    
    def search_with_no_limits(self, question: str):
        """Search with NO LIMITS - see what happens!"""
        print("🔓 Searching with NO LIMITS...")
        
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
            
            words = [w.lower().strip('.,?!') for w in question.split() if len(w) > 3]
            
            context_parts = []
            
            # 1. Search for ALL matching characters - NO LIMIT
            for name in key_names:
                normalized_name = name.replace('ü', 'u').replace('ä', 'a').replace('ö', 'o')
                
                character_query = """
                MATCH (c:Character)
                WHERE toLower(c.name) CONTAINS $name 
                   OR toLower(c.name) CONTAINS $normalized_name
                OPTIONAL MATCH (c)-[r:RELATES_TO]-(other)
                RETURN c AS character, collect({other: other.name, relationship: r.type, context: r.narrative_context}) as relationships
                """
                # NO LIMIT!
                
                result = session.run(character_query, {"name": name, "normalized_name": normalized_name})
                for record in result:
                    char = record["character"]
                    relationships = record["relationships"]
                    
                    char_info = f"CHARACTER: {char.get('name', 'Unknown')}\\n"
                    char_info += f"ROLE: {char.get('role', 'Unknown')}\\n"
                    if char.get('significance'): char_info += f"Significance: {char['significance']}\\n"
                    
                    # ALL relationships - NO LIMIT!
                    if relationships:
                        char_info += "ALL RELATIONSHIPS:\\n"
                        for rel in relationships:  # NO [:5] limit!
                            if rel['other']:
                                char_info += f"  → {rel['other']}: {rel.get('context', 'Connected')}\\n"
                    
                    context_parts.append(char_info)
            
            # 2. Search ALL episodes - NO LIMITS
            for word in words:  # ALL words, not just [:4]
                episode_query = """
                MATCH (e:Episode)
                WHERE toLower(e.content) CONTAINS $word
                RETURN e.name AS name, e.content AS content
                ORDER BY e.chapter_sequence
                """
                # NO LIMIT!
                
                result = session.run(episode_query, {"word": word})
                for record in result:
                    content = record["content"]  # NO truncation!
                    context_parts.append(f"EPISODE {record['name']}:\\n{content}")
            
            # 3. Search ALL events - NO LIMITS  
            for word in words:  # ALL words
                event_query = """
                MATCH (ev:Event)
                WHERE toLower(ev.name) CONTAINS $word
                   OR toLower(ev.narrative_function) CONTAINS $word
                RETURN ev AS event
                """
                # NO LIMIT!
                
                result = session.run(event_query, {"word": word})
                for record in result:
                    event = record["event"]
                    event_info = f"EVENT: {event.get('name', 'Unknown')}\\n"
                    if event.get('narrative_function'): event_info += f"Function: {event['narrative_function']}\\n"
                    if event.get('participants'): event_info += f"Participants: {event['participants']}\\n"
                    context_parts.append(event_info)
            
            search_time = time.time() - start_time
            
            # ALL context - NO LIMITS!
            total_context = "\\n\\n".join(context_parts)  # NO [:10] limit!
            
            context_size = len(total_context)
            word_count = len(total_context.split())
            
            print(f"🔥 RESULTS WITH NO LIMITS:")
            print(f"   🔍 Search time: {search_time:.2f}s")
            print(f"   📊 Total sources: {len(context_parts)}")
            print(f"   📏 Context size: {context_size:,} characters")
            print(f"   📝 Context words: {word_count:,} words")
            print(f"   ⚠️  Memory usage: ~{context_size/1024:.1f}KB")
            
            if context_size > 50000:
                print("   🚨 WARNING: Very large context - may cause issues!")
            
            return total_context
    
    async def answer_question(self, question: str):
        """Answer with no limits"""
        print(f"❓ Question: {question}")
        
        context = self.search_with_no_limits(question)
        
        if not context:
            return "No context found"
        
        # Test if context is too big
        context_size = len(context)
        if context_size > 100000:  # 100KB
            print(f"🚨 MASSIVE CONTEXT ({context_size:,} chars) - This might break!")
        
        prompt = f"""Question: {question}

MASSIVE CONTEXT (NO LIMITS):

{context}

Answer based on this information:"""
        
        print("🤔 Generating answer with unlimited context...")
        answer_start = time.time()
        answer = self.call_ollama(prompt, 2000)
        answer_time = time.time() - answer_start
        
        print(f"⏱️  Answer generation: {answer_time:.2f}s")
        
        return answer
    
    def close(self):
        self.driver.close()

async def test_no_limits():
    """Test what happens with no limits"""
    
    print("🚨 TESTING NO LIMITS - DANGER ZONE!")
    print("=" * 60)
    
    qa_system = NoLimitsQASystem()
    
    test_questions = [
        "What was Asa Jennings' role in the evacuation?",
        "How did American officials work together?",  # Broader query
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\\n{i}. NO LIMITS TEST")
        print(f"Question: {question}")
        print("-" * 40)
        
        try:
            total_start = time.time()
            answer = await qa_system.answer_question(question)
            total_time = time.time() - total_start
            
            print(f"\\n💡 Answer (No Limits):")
            print(answer[:500] + "..." if len(answer) > 500 else answer)
            print(f"\\n⏱️  Total time: {total_time:.2f}s")
            print(f"📏 Answer length: {len(answer)} chars")
            
        except Exception as e:
            print(f"💥 SYSTEM BROKE: {e}")
    
    qa_system.close()
    print("\\n🏁 NO LIMITS TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_no_limits())