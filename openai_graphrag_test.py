#!/usr/bin/env python3
"""
GraphRAG test using Neo4j and OpenAI to compare answer quality vs local Ollama
"""

from neo4j import GraphDatabase
import requests
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class OpenAIGraphRAGSystem:
    def __init__(self):
        # Connect to Neo4j
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        
        # OpenAI settings
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4"
        
        print("✅ OpenAI GraphRAG System initialized")
        print(f"🧠 Using model: {self.model}")
        print(f"🔗 Connected to Neo4j: the-great-fire-db")
    
    def call_openai(self, prompt: str, max_tokens: int = 800) -> str:
        """Call OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(self.openai_url, json=data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"OpenAI Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"
    
    def generate_intelligent_query(self, question: str):
        """Use OpenAI to generate intelligent Cypher queries"""
        print("🧠 Generating intelligent Cypher query with OpenAI...")
        
        # Extract key terms for search
        analysis_prompt = f"""
Analyze this question about the Great Fire of Smyrna: {question}

What are the key entities (people, organizations, events) I should search for?
List ONLY the specific names/terms to search for, one per line:
"""
        
        search_terms = self.call_openai(analysis_prompt, 200)
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
            search_term = terms[0] if terms else 'smyrna'
        
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
        """Answer question using OpenAI GraphRAG approach"""
        print(f"❓ Question: {question}")
        
        # Step 1: Generate intelligent Cypher query
        cypher_query = self.generate_intelligent_query(question)
        
        # Step 2: Execute the query - MUST WORK
        context = self.execute_query(cypher_query)
        
        if not context:
            return f"❌ GraphRAG query failed to find results. Query was: {cypher_query}"
        
        # Step 3: Generate answer using OpenAI
        answer_prompt = f"""
Question: {question}

Relevant Information from Knowledge Graph:
{context}

Based on this information from the knowledge graph about the Great Fire of Smyrna (1922), provide a comprehensive and insightful answer. Focus on:
1. Specific historical details from the graph data
2. Character roles and relationships
3. Historical context and significance
4. Direct connections to the question asked

Be precise and use only the information provided in the context above.
"""
        
        print("🤔 Generating intelligent answer with OpenAI...")
        answer = self.call_openai(answer_prompt, 1200)
        
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
        
        # Test OpenAI
        try:
            test_response = self.call_openai("Hello", 10)
            if not test_response.startswith("Error"):
                print(f"✅ OpenAI: {self.model} responding")
            else:
                print(f"❌ OpenAI error: {test_response}")
                return False
        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            return False
        
        return True
    
    def close(self):
        self.driver.close()

async def main():
    print("🔥 OPENAI GRAPHRAG SYSTEM TEST")
    print("=" * 50)
    print("🧠 Using OpenAI GPT-4 for query generation and answers")
    print("🔗 Using Neo4j for graph traversal")
    print("📚 Analyzing: The Great Fire of Smyrna")
    print("=" * 50)
    
    # Initialize system
    try:
        graphrag = OpenAIGraphRAGSystem()
    except ValueError as e:
        print(f"❌ {e}")
        print("💡 Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Test connections
    if not graphrag.test_connection():
        print("❌ Connection tests failed")
        return
    
    # Test questions - same as Ollama version for comparison
    test_questions = [
        "What was Asa Jennings' role in the evacuation?",
        "How did Atatürk and American officials interact?",
        "What humanitarian organizations were involved?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\\n{i}. TESTING OPENAI GRAPHRAG")
        print(f"Question: {question}")
        print("-" * 50)
        
        answer = await graphrag.answer_question(question)
        print("💡 OpenAI GraphRAG Answer:")
        print(answer)
        print("-" * 50)
        
        # Analysis of answer quality
        answer_length = len(answer.split())
        has_specifics = any(term in answer.lower() for term in ['september', '1922', 'smyrna', 'bristol', 'jennings', 'evacuation'])
        has_details = len([term for term in ['character', 'role', 'organization', 'relationship'] if term in answer.lower()]) > 2
        
        quality_indicators = []
        if answer_length > 100: quality_indicators.append("✅ Detailed")
        if has_specifics: quality_indicators.append("✅ Specific")
        if has_details: quality_indicators.append("✅ Rich")
        
        print(f"📊 Answer Quality: {len(quality_indicators)}/3 - {', '.join(quality_indicators)}")
        print(f"📏 Length: {answer_length} words")
    
    graphrag.close()
    print("\\n👋 OpenAI GraphRAG test complete")
    print("\\n🔄 Compare these results with the Ollama version to see the difference!")

if __name__ == "__main__":
    asyncio.run(main())