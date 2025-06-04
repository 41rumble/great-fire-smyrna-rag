#!/usr/bin/env python3
"""
Enhanced QA system using Neo4j GraphRAG with local Ollama
This replaces manual Cypher queries with intelligent, auto-generated ones
"""

from neo4j import GraphDatabase
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.retrievers import VectorCypherRetriever
from neo4j_graphrag.generation import GraphRAG
import requests
import asyncio

class Neo4jGraphRAGSystem:
    def __init__(self):
        # Connect to Neo4j
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        
        # Setup local Ollama LLM - same model as your existing setup
        self.llm = OllamaLLM(
            model_name="mistral-small3.1:latest",
            base_url="http://localhost:11434"
        )
        
        print("✅ Neo4j GraphRAG System initialized with local Ollama")
        print(f"📊 Using model: mistral-small3.1:latest")
        print(f"🔗 Connected to Neo4j database: the-great-fire-db")
    
    def setup_retriever(self):
        """Setup the retriever for your custom schema"""
        try:
            # Create a Cypher retriever for your specific schema
            retriever = VectorCypherRetriever(
                driver=self.driver,
                database="the-great-fire-db",
                # Custom retrieval query for your schema
                retrieval_query="""
                // Find relevant characters, episodes, and relationships
                MATCH (c:Character)
                WHERE toLower(c.name) CONTAINS toLower($query) 
                   OR toLower(c.role) CONTAINS toLower($query)
                   OR toLower(c.significance) CONTAINS toLower($query)
                OPTIONAL MATCH (c)-[r:RELATES_TO]-(other)
                WITH c, collect({other: other.name, relationship: r.type, context: r.narrative_context}) as relationships
                
                // Also find relevant episodes
                OPTIONAL MATCH (e:Episode)
                WHERE toLower(e.content) CONTAINS toLower($query)
                
                // And relevant events
                OPTIONAL MATCH (ev:Event)
                WHERE toLower(ev.name) CONTAINS toLower($query)
                   OR toLower(ev.narrative_function) CONTAINS toLower($query)
                
                RETURN 
                  c.name as character_name,
                  c.role as character_role,
                  c.significance as character_significance,
                  c.motivations as character_motivations,
                  relationships,
                  collect(DISTINCT e.content)[0..2] as episode_content,
                  collect(DISTINCT ev.name) as related_events
                LIMIT 5
                """,
                index_name="character_search"  # We'll create this if needed
            )
            
            return retriever
            
        except Exception as e:
            print(f"⚠️ Could not setup vector retriever: {e}")
            print("📝 Using basic Cypher retriever instead...")
            
            # Fallback to simpler retriever
            return VectorCypherRetriever(
                driver=self.driver,
                database="the-great-fire-db",
                retrieval_query="""
                MATCH (n)
                WHERE toLower(n.name) CONTAINS toLower($query)
                   OR (n.content IS NOT NULL AND toLower(n.content) CONTAINS toLower($query))
                RETURN n.name as name, 
                       labels(n) as type,
                       coalesce(n.role, n.significance, n.content[0..500]) as description
                LIMIT 10
                """
            )
    
    async def answer_question(self, question: str):
        """Answer question using Neo4j GraphRAG with local Ollama"""
        print(f"🤔 Processing question with GraphRAG: {question}")
        
        try:
            # Setup retriever
            retriever = self.setup_retriever()
            
            # Create GraphRAG instance
            graphrag = GraphRAG(
                llm=self.llm,
                retriever=retriever
            )
            
            # Process the question
            print("🔍 GraphRAG is analyzing your question and generating optimized queries...")
            result = graphrag.search(question)
            
            print("✅ GraphRAG analysis complete")
            return result.answer
            
        except Exception as e:
            print(f"❌ GraphRAG error: {e}")
            print("🔄 Falling back to simple search...")
            return await self.fallback_search(question)
    
    async def fallback_search(self, question: str):
        """Fallback to your existing manual search if GraphRAG fails"""
        print("🔍 Using fallback manual search...")
        
        with self.driver.session(database="the-great-fire-db") as session:
            # Simple character search
            words = [w.lower().strip('.,?!') for w in question.split() if len(w) > 3]
            
            context_parts = []
            
            for word in words[:3]:
                # Search characters
                char_query = """
                MATCH (c:Character)
                WHERE toLower(c.name) CONTAINS $word
                RETURN c.name as name, c.role as role, c.significance as significance
                LIMIT 2
                """
                result = session.run(char_query, {"word": word})
                for record in result:
                    context_parts.append(f"CHARACTER: {record['name']} - {record['role']} - {record['significance']}")
                
                # Search episodes
                episode_query = """
                MATCH (e:Episode)
                WHERE toLower(e.content) CONTAINS $word
                RETURN e.name, substring(e.content, 0, 300) as content
                LIMIT 1
                """
                result = session.run(episode_query, {"word": word})
                for record in result:
                    context_parts.append(f"FROM {record['e.name']}: {record['content']}")
            
            if not context_parts:
                return "I couldn't find relevant information to answer your question."
            
            # Use local Ollama to generate answer
            context = "\n\n".join(context_parts)
            
            # Call Ollama directly (same as your existing system)
            data = {
                "model": "mistral-small3.1:latest",
                "messages": [
                    {"role": "user", "content": f"Question: {question}\n\nContext: {context}\n\nAnswer based on this information:"}
                ],
                "max_tokens": 1200,
                "temperature": 0.4
            }
            
            response = requests.post("http://localhost:11434/v1/chat/completions", json=data)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error generating answer: {response.status_code}"
    
    def test_connection(self):
        """Test Neo4j and Ollama connectivity"""
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
                "http://localhost:11434/v1/chat/completions",
                json={
                    "model": "mistral-small3.1:latest",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Ollama: mistral-small3.1:latest responding")
            else:
                print(f"⚠️ Ollama: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return False
        
        return True
    
    def close(self):
        """Clean up connections"""
        self.driver.close()

async def main():
    """Test the GraphRAG system"""
    print("🔥 NEO4J GRAPHRAG + LOCAL OLLAMA SYSTEM")
    print("=" * 60)
    print("🧠 Using Neo4j GraphRAG for intelligent query generation")
    print("🏠 Using local Ollama (mistral-small3.1) for processing")
    print("📚 Analyzing: The Great Fire of Smyrna")
    print("=" * 60)
    
    # Initialize system
    graphrag = Neo4jGraphRAGSystem()
    
    # Test connections
    if not graphrag.test_connection():
        print("❌ Connection tests failed. Please check Neo4j and Ollama are running.")
        return
    
    print("\n🎯 System ready! GraphRAG will automatically:")
    print("  • Analyze your questions")
    print("  • Generate optimal Cypher queries") 
    print("  • Traverse relationships intelligently")
    print("  • Synthesize comprehensive answers")
    print("\nExample questions to try:")
    print("  • What was Asa Jennings' role in the evacuation?")
    print("  • How were Turkish and American officials connected?")
    print("  • What humanitarian organizations were involved?")
    
    # Interactive loop
    while True:
        question = input("\n🤔 Your question (or 'quit' to exit): ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if len(question) < 5:
            print("Please ask a more detailed question.")
            continue
        
        print()
        answer = await graphrag.answer_question(question)
        print("💡 GraphRAG Answer:")
        print("-" * 50)
        print(answer)
        print("-" * 50)
    
    graphrag.close()
    print("👋 GraphRAG session ended")

if __name__ == "__main__":
    asyncio.run(main())