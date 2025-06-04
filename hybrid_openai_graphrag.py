#!/usr/bin/env python3
"""
Hybrid GraphRAG: OpenAI for Cypher query generation, local Ollama for answers
"""

from neo4j import GraphDatabase
import requests
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class HybridOpenAIGraphRAG:
    def __init__(self):
        # Connect to Neo4j
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        
        # OpenAI for query generation
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        
        # Local Ollama for answers
        self.ollama_url = "http://localhost:11434/v1/chat/completions"
        self.ollama_model = "mistral-small3.1:latest"
        
        print("✅ Hybrid OpenAI + Ollama GraphRAG System initialized")
        print(f"🧠 Query Generation: OpenAI GPT-4")
        print(f"💬 Answer Generation: Local Ollama ({self.ollama_model})")
        print(f"🔗 Connected to Neo4j: the-great-fire-db")
    
    def call_openai(self, prompt: str, max_tokens: int = 300) -> str:
        """Call OpenAI API for query generation"""
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1  # Low temperature for precise Cypher generation
        }
        
        try:
            response = requests.post(self.openai_url, json=data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"OpenAI Error: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    def call_ollama(self, prompt: str, max_tokens: int = 1200) -> str:
        """Call local Ollama for answer generation"""
        data = {
            "model": self.ollama_model,
            "messages": [
                {"role": "system", "content": "You are a knowledgeable historian providing detailed analysis of the Great Fire of Smyrna (1922). Write comprehensive, insightful responses based on the provided graph data."},
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
                return f"Ollama Error: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    def generate_intelligent_query(self, question: str):
        """Use OpenAI to generate precise Cypher queries"""
        print("🧠 Generating Cypher query with OpenAI GPT-4...")
        
        schema_prompt = f"""
You are an expert Neo4j Cypher query generator for a database about "The Great Fire of Smyrna" (1922).

EXACT DATABASE SCHEMA:
- Node Labels: Character, Episode, Event, Location, Organization  
- Relationship Types: RELATES_TO, MENTIONS, SAYS
- Character properties: name, role, nationality, significance, motivations, development
- Episode properties: name, content, chapter_sequence

PROVEN WORKING PATTERNS:
1. Find Characters: MATCH (c:Character) WHERE toLower(c.name) CONTAINS 'search_term'
2. Get Relationships: OPTIONAL MATCH (c)-[r:RELATES_TO]->(related)  
3. Get Episodes: OPTIONAL MATCH (c)-[m:MENTIONS]->(e:Episode)

QUESTION: {question}

Generate a single, working Cypher query that:
1. Finds relevant Characters using CONTAINS on name or role
2. Gets their RELATES_TO relationships 
3. Gets Episodes they MENTION
4. Returns character details, relationships, and episode content
5. Limits results to 5

Return ONLY the Cypher query, no explanation:
"""
        
        cypher_query = self.call_openai(schema_prompt, 400)
        
        # Clean up the response
        cypher_query = cypher_query.strip()
        if "```" in cypher_query:
            parts = cypher_query.split("```")
            for part in parts:
                if "MATCH" in part:
                    cypher_query = part
                    break
        
        # Remove any markdown or extra text
        lines = cypher_query.split('\n')
        query_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                query_lines.append(line)
        
        cypher_query = '\n'.join(query_lines)
        
        print(f"📝 Generated Cypher: {cypher_query}")
        return cypher_query
    
    def execute_query(self, cypher_query: str):
        """Execute the OpenAI-generated Cypher query"""
        try:
            with self.driver.session(database="the-great-fire-db") as session:
                result = session.run(cypher_query)
                
                context_parts = []
                for record in result:
                    record_info = []
                    for key, value in record.items():
                        if isinstance(value, list):
                            # Handle lists (like collected data)
                            if value and any(v for v in value if v):  # Non-empty list
                                record_info.append(f"{key}: {', '.join(str(v) for v in value[:3] if v)}")
                        elif hasattr(value, 'items'):  # Neo4j node
                            node_info = f"{key.upper()}: "
                            for prop_key, prop_value in value.items():
                                if prop_value:
                                    node_info += f"{prop_key}={str(prop_value)[:150]} "
                            record_info.append(node_info)
                        elif value:  # Simple value
                            record_info.append(f"{key}: {str(value)[:200]}")
                    
                    if record_info:
                        context_parts.append(" | ".join(record_info))
                
                return "\\n\\n".join(context_parts[:6])
                
        except Exception as e:
            print(f"⚠️ Query execution error: {e}")
            return None
    
    async def answer_question(self, question: str):
        """Answer using OpenAI queries + Ollama responses"""
        print(f"❓ Question: {question}")
        
        # Step 1: Generate Cypher with OpenAI
        cypher_query = self.generate_intelligent_query(question)
        
        # Step 2: Execute query
        context = self.execute_query(cypher_query)
        
        if not context:
            return f"❌ OpenAI-generated query failed. Query: {cypher_query}"
        
        # Step 3: Generate answer with local Ollama
        answer_prompt = f"""
Question: {question}

Knowledge Graph Data:
{context}

Based on this specific information from the Great Fire of Smyrna knowledge graph, provide a comprehensive and historically accurate answer. Focus on the actual data provided and avoid speculation.
"""
        
        print("🤔 Generating answer with local Ollama...")
        answer = self.call_ollama(answer_prompt)
        
        return answer
    
    def test_connection(self):
        """Test all connections"""
        print("🧪 Testing connections...")
        
        # Test Neo4j
        try:
            with self.driver.session(database="the-great-fire-db") as session:
                result = session.run("MATCH (n) RETURN count(n) as total")
                count = result.single()["total"]
                print(f"✅ Neo4j: {count} nodes")
        except Exception as e:
            print(f"❌ Neo4j: {e}")
            return False
        
        # Test OpenAI
        test_response = self.call_openai("Hello", 5)
        if not test_response.startswith("Error"):
            print("✅ OpenAI: Connected")
        else:
            print(f"❌ OpenAI: {test_response}")
            return False
        
        # Test Ollama
        test_response = self.call_ollama("Hello", 5)
        if not test_response.startswith("Error"):
            print("✅ Ollama: Connected")
        else:
            print(f"❌ Ollama: {test_response}")
            return False
        
        return True
    
    def close(self):
        self.driver.close()

async def main():
    print("🔥 HYBRID OPENAI + OLLAMA GRAPHRAG TEST")
    print("=" * 60)
    print("🧠 Cypher Generation: OpenAI GPT-4 (precise queries)")
    print("💬 Answer Generation: Local Ollama (private responses)")
    print("🔗 Graph Database: Neo4j")
    print("=" * 60)
    
    # Initialize system
    try:
        graphrag = HybridOpenAIGraphRAG()
    except ValueError as e:
        print(f"❌ {e}")
        return
    
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
        print(f"\\n{i}. TESTING HYBRID GRAPHRAG")
        print(f"Question: {question}")
        print("-" * 50)
        
        answer = await graphrag.answer_question(question)
        print("💡 Hybrid Answer (OpenAI Queries + Ollama Response):")
        print(answer)
        print("-" * 50)
        
        # Quick quality assessment
        answer_length = len(answer.split())
        has_specifics = any(term in answer.lower() for term in ['jennings', 'atatürk', 'smyrna', '1922', 'evacuation'])
        
        quality = "📊 Quality: "
        if answer_length > 100: quality += "✅ Detailed "
        if has_specifics: quality += "✅ Specific "
        if not answer.startswith("❌"): quality += "✅ Success"
        
        print(f"{quality} | Length: {answer_length} words")
    
    graphrag.close()
    print("\\n👋 Hybrid GraphRAG test complete!")
    print("\\n🔄 This combines OpenAI's precise query generation with local Ollama's private responses")

if __name__ == "__main__":
    asyncio.run(main())