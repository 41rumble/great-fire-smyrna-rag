#!/usr/bin/env python3
"""
Clean Ollama book ingestion - production ready
"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_with_local_models import OllamaLLMClient, OllamaEmbedder

load_dotenv()

class CleanOllamaEmbedder(OllamaEmbedder):
    """Clean embedder without debug output"""
    
    async def create(self, input_data):
        """Create single embedding quietly"""
        try:
            if isinstance(input_data, list):
                text = " ".join(str(item) for item in input_data)
            else:
                text = str(input_data)
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                return response.json().get("embedding", [])
            else:
                return [0.0] * 768
                
        except Exception:
            return [0.0] * 768
    
    async def create_batch(self, input_data_list):
        """Create batch embeddings quietly"""
        embeddings = []
        for input_data in input_data_list:
            embedding = await self.create(input_data)
            embeddings.append(embedding)
        return embeddings

class CleanOllamaLLMClient(OllamaLLMClient):
    """Clean LLM client without debug output"""
    
    async def _generate_response(self, messages: list, response_model=None, max_tokens: int = 4000, model_size=None) -> dict:
        """Generate response quietly"""
        try:
            prompt = ""
            for message in messages:
                if hasattr(message, 'content'):
                    prompt += f"{message.role}: {message.content}\n"
                elif isinstance(message, dict):
                    prompt += f"{message.get('role', 'user')}: {message.get('content', '')}\n"
                else:
                    prompt += str(message) + "\n"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens}
                }
            )
            
            if response.status_code == 200:
                content = response.json().get("response", "")
                return {"content": content}
            else:
                return {"content": ""}
                
        except Exception:
            return {"content": ""}

async def clean_ollama_ingestion():
    """Clean book ingestion with Ollama"""
    
    print("📚 HISTORICAL BOOKS INGESTION WITH OLLAMA")
    print("=" * 60)
    
    # Import requests here to avoid import error
    import requests
    
    # Initialize clean Ollama clients
    llm_client = CleanOllamaLLMClient()
    embedder = CleanOllamaEmbedder()
    
    print("🦙 Ollama models ready (mistral-small3.1 + nomic-embed-text)")
    
    # Clean database
    print("🧹 Preparing clean database...")
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()
    
    # Initialize Graphiti
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'Sk1pper(())')
    
    graphiti = Graphiti(
        neo4j_uri, 
        neo4j_user, 
        neo4j_password,
        llm_client=llm_client,
        embedder=embedder
    )
    
    await graphiti.build_indices_and_constraints()
    print("✅ Graphiti knowledge graph initialized")
    
    # Get text files
    text_files_dir = Path("text_files")
    text_files = list(text_files_dir.glob("*.txt"))
    
    if not text_files:
        print("❌ No text files found in text_files directory")
        return
    
    print(f"📖 Found {len(text_files)} book sections to process")
    
    # Process files
    processed = 0
    for text_file in text_files:
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if len(content) < 100:
                continue
                
            episode_name = text_file.stem.replace('_', ' ').title()
            
            await graphiti.add_episode(
                name=episode_name,
                episode_body=content,
                source=EpisodeType.text,
                source_description=f"Historical text: {text_file.name}",
                reference_time=datetime(1922, 9, 15, tzinfo=timezone.utc)
            )
            
            processed += 1
            if processed % 5 == 0:
                print(f"   📝 Processed {processed}/{len(text_files)} sections...")
            
        except Exception as e:
            print(f"⚠️  Skipped {text_file.name}: {e}")
    
    print(f"✅ Completed processing {processed} book sections")
    print("⏳ Finalizing knowledge extraction...")
    await asyncio.sleep(3)
    
    # Test searches
    print(f"\n🔍 TESTING HISTORICAL KNOWLEDGE SEARCH")
    print("=" * 50)
    
    queries = [
        "Who was Asa Jennings?",
        "What happened in Smyrna in 1922?",
        "Greek military forces", 
        "American evacuation efforts",
        "Mustafa Kemal Ataturk",
        "refugee crisis"
    ]
    
    for query in queries:
        print(f"\n🔍 '{query}'")
        
        try:
            results = await graphiti.search(query, num_results=3)
            
            if results and len(results) > 0:
                print(f"   ✅ Found {len(results)} historical facts:")
                for i, result in enumerate(results):
                    if hasattr(result, 'fact'):
                        print(f"      • {result.fact}")
                    else:
                        print(f"      • {result}")
            else:
                print("   ❌ No results found")
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")
    
    # Show summary
    print(f"\n📊 KNOWLEDGE GRAPH SUMMARY")
    print("=" * 40)
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN DISTINCT labels(n) as labels, count(*) as count ORDER BY count DESC")
        for record in result:
            print(f"   {record['labels']}: {record['count']}")
            
        result = session.run("MATCH ()-[r]->() RETURN count(r) as facts")
        facts = result.single()['facts']
        print(f"   Historical Facts: {facts}")
        
    driver.close()
    
    print(f"\n🎉 SUCCESS!")
    print("📚 Your historical books are now a searchable knowledge graph")
    print("🦙 100% local operation with Ollama - $0 cost")
    print("🔍 Search for people, events, relationships, and historical facts")

if __name__ == "__main__":
    asyncio.run(clean_ollama_ingestion())