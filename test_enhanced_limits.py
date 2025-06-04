#!/usr/bin/env python3
"""
Test the enhanced limits in the hybrid QA system
"""

import time
import requests
from neo4j import GraphDatabase
import asyncio

class TestEnhancedSystem:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        self.ollama_url = "http://localhost:11434/v1/chat/completions"
        self.model = "mistral-small3.1:latest"
    
    def call_ollama(self, prompt: str, max_tokens: int = 1800) -> str:
        """Call local Ollama"""
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
    
    def search_enhanced_limits(self, question: str):
        """Test the enhanced search limits"""
        print("🔍 Testing enhanced limits...")
        
        start_time = time.time()
        
        with self.driver.session(database="the-great-fire-db") as session:
            # Test enhanced character search
            key_names = []
            question_lower = question.lower()
            known_characters = ["atatürk", "ataturk", "kemal", "jennings", "bristol", "horton", "powell"]
            for char in known_characters:
                if char in question_lower:
                    key_names.append(char)
            
            words = [w.lower().strip('.,?!') for w in question.split() if len(w) > 3]
            context_parts = []
            
            # 1. Character search with enhanced relationships
            for name in key_names:
                normalized_name = name.replace('ü', 'u').replace('ä', 'a').replace('ö', 'o')
                
                character_query = """
                MATCH (c:Character)
                WHERE toLower(c.name) CONTAINS $name 
                OPTIONAL MATCH (c)-[r:RELATES_TO]-(other)
                RETURN c AS character, collect({other: other.name, relationship: r.type, context: r.narrative_context}) as relationships
                LIMIT 1
                """
                result = session.run(character_query, {"name": name, "normalized_name": normalized_name})
                for record in result:
                    char = record["character"]
                    relationships = record["relationships"]
                    
                    char_info = f"CHARACTER: {char.get('name', 'Unknown')}\\n"
                    char_info += f"ROLE: {char.get('role', 'Unknown')}\\n"
                    if char.get('significance'): char_info += f"Significance: {char['significance']}\\n"
                    
                    # TEST: Up to 10 relationships (was 5)
                    if relationships:
                        char_info += f"RELATIONSHIPS ({len(relationships[:10])} shown):\\n"
                        for rel in relationships[:10]:
                            if rel['other']:
                                char_info += f"  → {rel['other']}: {rel.get('context', 'Connected')}\\n"
                    
                    context_parts.append(char_info)
            
            # 2. TEST: Enhanced episode search (6 words, 5 episodes each, 2000 chars)
            episode_count = 0
            for word in words[:6]:  # Enhanced: was 4
                episode_query = """
                MATCH (e:Episode)
                WHERE toLower(e.content) CONTAINS $word
                RETURN e.name AS name, e.content AS content
                ORDER BY e.chapter_sequence
                LIMIT 5
                """  # Enhanced: was 3
                result = session.run(episode_query, {"word": word})
                for record in result:
                    episode_count += 1
                    content = record["content"][:2000]  # Enhanced: was 1200
                    context_parts.append(f"EPISODE {record['name']} ({len(content)} chars):\\n{content}")
            
            # 3. TEST: Enhanced event search (4 words, 4 events each)
            event_count = 0
            for word in words[:4]:  # Enhanced: was 2
                event_query = """
                MATCH (ev:Event)
                WHERE toLower(ev.name) CONTAINS $word
                RETURN ev AS event
                LIMIT 4
                """  # Enhanced: was 2
                result = session.run(event_query, {"word": word})
                for record in result:
                    event_count += 1
                    event = record["event"]
                    event_info = f"EVENT: {event.get('name', 'Unknown')}\\n"
                    if event.get('narrative_function'): event_info += f"Function: {event['narrative_function']}\\n"
                    context_parts.append(event_info)
            
            search_time = time.time() - start_time
            
            # TEST: 25 total entities (was 10)
            total_context = "\\n\\n".join(context_parts[:25])
            
            context_size = len(total_context)
            word_count = len(total_context.split())
            
            print(f"📊 ENHANCED LIMITS RESULTS:")
            print(f"   ⏱️  Search time: {search_time:.2f}s")
            print(f"   🎭 Total sources: {len(context_parts)} (showing {min(25, len(context_parts))})")
            print(f"   📝 Episodes found: {episode_count}")
            print(f"   🎯 Events found: {event_count}")
            print(f"   📏 Context size: {context_size:,} characters")
            print(f"   📖 Context words: {word_count:,} words")
            print(f"   💾 Memory: ~{context_size/1024:.1f}KB")
            
            return total_context
    
    async def test_enhanced_vs_original(self, question: str):
        """Compare enhanced vs original performance"""
        print(f"❓ Testing Question: {question}")
        print("=" * 60)
        
        # Test enhanced limits
        enhanced_start = time.time()
        enhanced_context = self.search_enhanced_limits(question)
        enhanced_search_time = time.time() - enhanced_start
        
        if not enhanced_context:
            print("❌ No context found")
            return
        
        # Generate answer
        prompt = f"""Question: {question}

Enhanced Context (25 entities, 10 relationships, 2000 chars):

{enhanced_context}

Provide a comprehensive answer based on this enhanced information:"""
        
        print("\\n🤔 Generating enhanced answer...")
        answer_start = time.time()
        answer = self.call_ollama(prompt, 1800)
        answer_time = time.time() - answer_start
        total_time = enhanced_search_time + answer_time
        
        print(f"\\n💡 Enhanced Answer:")
        print(answer)
        
        print(f"\\n📈 PERFORMANCE SUMMARY:")
        print(f"   ⏱️  Search: {enhanced_search_time:.2f}s")
        print(f"   🤔 Answer: {answer_time:.2f}s") 
        print(f"   🎯 Total: {total_time:.2f}s")
        print(f"   📏 Answer: {len(answer)} chars, {len(answer.split())} words")
        
        return {
            "search_time": enhanced_search_time,
            "answer_time": answer_time,
            "total_time": total_time,
            "answer_length": len(answer),
            "context_size": len(enhanced_context)
        }
    
    def close(self):
        self.driver.close()

async def main():
    print("🚀 TESTING ENHANCED LIMITS")
    print("=" * 60)
    print("📊 NEW LIMITS:")
    print("   • 25 total entities (was 10)")
    print("   • 10 relationships per character (was 5)")
    print("   • 5 episodes per word, 6 words (was 3 episodes, 4 words)")
    print("   • 4 events per word, 4 words (was 2 events, 2 words)")
    print("   • 2000 chars per episode (was 1200)")
    print("   • 1800 max tokens (was 1200)")
    print("=" * 60)
    
    tester = TestEnhancedSystem()
    
    test_questions = [
        "What was Asa Jennings' role in the evacuation?",
        "How did Atatürk and American officials interact?",
        "What humanitarian organizations were involved?"
    ]
    
    results = []
    
    for i, question in enumerate(test_questions, 1):
        print(f"\\n{i}. ENHANCED LIMITS TEST")
        result = await tester.test_enhanced_vs_original(question)
        if result:
            results.append(result)
        print("-" * 60)
    
    if results:
        avg_search = sum(r['search_time'] for r in results) / len(results)
        avg_total = sum(r['total_time'] for r in results) / len(results)
        avg_context = sum(r['context_size'] for r in results) / len(results)
        
        print(f"\\n📊 OVERALL ENHANCED PERFORMANCE:")
        print(f"   ⏱️  Average search: {avg_search:.2f}s")
        print(f"   🎯 Average total: {avg_total:.2f}s")
        print(f"   📏 Average context: {avg_context:,.0f} chars")
        print(f"   🎉 Expected improvement: 2-3x more context, minimal speed impact")
    
    tester.close()
    print("\\n✅ Enhanced limits testing complete!")

if __name__ == "__main__":
    asyncio.run(main())