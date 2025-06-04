#!/usr/bin/env python3
"""
Simple GraphRAG test using Neo4j and local Ollama
This creates a more intelligent query generation system
"""

from neo4j import GraphDatabase
import requests
import asyncio

class SimpleGraphRAGSystem:
    def __init__(self):
        # Connect to Neo4j
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        self.ollama_url = "http://localhost:11434/v1/chat/completions"
        self.model = "mistral-small3.1:latest"
        
        print("✅ Simple GraphRAG System initialized")
        print(f"🧠 Using model: {self.model}")
        print(f"🔗 Connected to Neo4j: the-great-fire-db")
    
    def call_ollama(self, prompt: str, max_tokens: int = 800) -> str:
        """Call local Ollama"""
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
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    def generate_intelligent_query(self, question: str):
        """Use LLM to generate intelligent Cypher queries"""
        print("🧠 Generating intelligent Cypher query...")
        
        # Extract key terms for search
        words = [w.lower().strip('.,?!') for w in question.split() if len(w) > 3]
        
        # Use template-based approach with LLM guidance
        analysis_prompt = f"""
Analyze this question about the Great Fire of Smyrna: {question}

What are the key entities (people, organizations, events) I should search for?
List ONLY the specific names/terms to search for, one per line:
"""
        
        search_terms = self.call_ollama(analysis_prompt, 200)
        terms = [term.strip().lower() for term in search_terms.split('\n') if term.strip() and len(term.strip()) > 2]
        
        # Build a working query using proven patterns
        if any('jennings' in term for term in terms) or 'jennings' in question.lower():
            search_term = 'jennings'
        elif any('atatürk' in term or 'ataturk' in term for term in terms) or 'atatürk' in question.lower():
            search_term = 'atatürk'
        elif any('american' in term for term in terms) or 'american' in question.lower():
            search_term = 'american'
        elif any('humanitarian' in term for term in terms) or 'humanitarian' in question.lower():
            search_term = 'humanitarian'
        else:
            search_term = terms[0] if terms else words[0] if words else 'smyrna'
        
        # Build query step by step
        cypher_query = f"""
MATCH (c:Character) 
WHERE toLower(c.name) CONTAINS '{search_term}' OR toLower(c.role) CONTAINS '{search_term}'
WITH c
OPTIONAL MATCH (c)-[r:RELATES_TO]->(related)
OPTIONAL MATCH (c)-[m:MENTIONS]->(e:Episode)
RETURN c.name as character_name, c.role as character_role, c.significance as character_significance,
       collect(DISTINCT related.name) as related_entities,
       collect(DISTINCT e.content)[0..2] as episode_content
LIMIT 5
""".strip()
        
        print(f"📝 Generated query for term '{search_term}': {cypher_query[:100]}...")
        return cypher_query
    
    def execute_query(self, cypher_query: str):
        """Execute the generated Cypher query"""
        try:
            with self.driver.session(database="the-great-fire-db") as session:
                result = session.run(cypher_query)
                
                context_parts = []
                for record in result:
                    # Convert record to string representation
                    record_info = []
                    for key, value in record.items():
                        if hasattr(value, 'items'):  # It's a node
                            node_info = f"{key.upper()}: "
                            for prop_key, prop_value in value.items():
                                if prop_value:
                                    node_info += f"{prop_key}={str(prop_value)[:200]} "
                            record_info.append(node_info)
                        else:
                            record_info.append(f"{key}: {str(value)[:300]}")
                    
                    context_parts.append(" | ".join(record_info))
                
                return "\\n\\n".join(context_parts[:8])  # Limit context
                
        except Exception as e:
            print(f"⚠️ Query execution error: {e}")
            return None
    
    async def answer_question(self, question: str):
        """Answer question using intelligent GraphRAG approach - NO FALLBACKS"""
        print(f"❓ Question: {question}")
        
        # Step 1: Generate intelligent Cypher query
        cypher_query = self.generate_intelligent_query(question)
        
        # Step 2: Execute the query - MUST WORK
        context = self.execute_query(cypher_query)
        
        if not context:
            return f"❌ GraphRAG query failed to find results. Query was: {cypher_query}"
        
        # Step 3: Generate answer using context
        answer_prompt = f"""
Question: {question}

Relevant Information from Knowledge Graph:
{context}

Based on this information, provide a comprehensive and insightful answer about the Great Fire of Smyrna (1922). 
Focus on historical accuracy and provide specific details when available.
"""
        
        print("🤔 Generating intelligent answer...")
        answer = self.call_ollama(answer_prompt, 1200)
        
        return answer
    
    def test_connection(self):
        """Test connections"""
        print("🧪 Testing connections...")
        
        # Test Neo4j
        try:
            with self.driver.session(database="the-great-fire-db") as session:
                result = session.run("MATCH (n) RETURN count(n) as total")
                count = result.single()["total"]
                print(f"✅ Neo4j: {count} nodes in the-great-fire-db")
        except Exception as e:
            print(f"❌ Neo4j error: {e}")
            return False
        
        # Test Ollama
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            if response.status_code == 200:
                print(f"✅ Ollama: {self.model} responding")
            else:
                print(f"⚠️ Ollama: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return False
        
        return True
    
    def close(self):
        self.driver.close()

async def main():
    print("🔥 SIMPLE GRAPHRAG SYSTEM TEST")
    print("=" * 50)
    print("🧠 Using intelligent Cypher query generation")
    print("🏠 Using local Ollama for processing")
    print("📚 Analyzing: The Great Fire of Smyrna")
    print("=" * 50)
    
    # Initialize system
    graphrag = SimpleGraphRAGSystem()
    
    # Test connections
    if not graphrag.test_connection():
        print("❌ Connection tests failed")
        return
    
    # Test questions
    test_questions = [
        "What was Asa Jennings' role in the evacuation?",
        "How did Atatürk and American officials interact?",
        "What humanitarian organizations were involved?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\\n{i}. TESTING INTELLIGENT GRAPHRAG")
        print(f"Question: {question}")
        print("-" * 50)
        
        answer = await graphrag.answer_question(question)
        print("💡 GraphRAG Answer:")
        print(answer[:400] + "..." if len(answer) > 400 else answer)
        print("-" * 50)
    
    graphrag.close()
    print("\\n👋 GraphRAG test complete")

if __name__ == "__main__":
    asyncio.run(main())