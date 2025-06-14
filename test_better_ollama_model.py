#!/usr/bin/env python3
"""
Test Graphiti with better Ollama model for structured output
"""

import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from neo4j import GraphDatabase
import requests

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.llm_client import LLMClient, LLMConfig
from graphiti_core.embedder import EmbedderClient
from typing import List

load_dotenv()

class BetterOllamaLLMClient(LLMClient):
    """LLM client using llama3.1:8b for better structured output"""
    
    def __init__(self, model_name="llama3.1:8b", base_url="http://localhost:11434"):
        config = LLMConfig(
            model=model_name,
            base_url=base_url,
            max_tokens=4000,
            temperature=0.1  # Lower temperature for more consistent structured output
        )
        super().__init__(config)
        self.model_name = model_name
        self.base_url = base_url
        print(f"🦙 Using {model_name} for better structured output")
    
    async def _generate_response(self, messages: list, response_model=None, max_tokens: int = 4000, model_size=None) -> dict:
        """Generate structured response using llama3.1"""
        try:
            # Build prompt with emphasis on structure
            prompt = ""
            for message in messages:
                if hasattr(message, 'content'):
                    prompt += f"{message.role}: {message.content}\n"
                elif isinstance(message, dict):
                    prompt += f"{message.get('role', 'user')}: {message.get('content', '')}\n"
                else:
                    prompt += str(message) + "\n"
            
            # Add instruction for structured output
            if "extract" in prompt.lower() or "json" in prompt.lower():
                prompt += "\nRespond with valid JSON only. Be precise and follow the format exactly."
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                }
            )
            
            if response.status_code == 200:
                content = response.json().get("response", "")
                return {"content": content}
            else:
                return {"content": ""}
                
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return {"content": ""}

class SimpleOllamaEmbedder(EmbedderClient):
    """Simple embedder for testing"""
    
    def __init__(self, model_name="nomic-embed-text:latest", base_url="http://localhost:11434"):
        super().__init__()
        self.model_name = model_name
        self.base_url = base_url
    
    async def create(self, input_data):
        try:
            text = str(input_data) if not isinstance(input_data, list) else " ".join(str(x) for x in input_data)
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text}
            )
            
            if response.status_code == 200:
                return response.json().get("embedding", [0.0] * 768)
            return [0.0] * 768
        except:
            return [0.0] * 768
    
    async def create_batch(self, input_data_list: List[str]):
        return [await self.create(data) for data in input_data_list]

async def test_better_model():
    """Test with better Ollama model"""
    
    print("🧪 TESTING BETTER OLLAMA MODEL FOR STRUCTURED OUTPUT")
    print("=" * 70)
    
    # Check if llama3.1:8b is available
    print("🔍 Checking if llama3.1:8b is available...")
    try:
        response = requests.get("http://localhost:11434/api/tags")
        models = [m["name"] for m in response.json().get("models", [])]
        
        if "llama3.1:8b" not in models:
            print("📥 llama3.1:8b not found. Pulling model...")
            print("⏳ This may take a few minutes...")
            
            pull_response = requests.post(
                "http://localhost:11434/api/pull",
                json={"name": "llama3.1:8b"}
            )
            
            if pull_response.status_code == 200:
                print("✅ llama3.1:8b downloaded successfully")
            else:
                print("❌ Failed to download llama3.1:8b")
                print("💡 You can manually run: ollama pull llama3.1:8b")
                return
        else:
            print("✅ llama3.1:8b is available")
            
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return
    
    # Clean database
    print("🧹 Cleaning database...")
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()
    
    # Initialize with better model
    llm_client = BetterOllamaLLMClient()
    embedder = SimpleOllamaEmbedder()
    
    graphiti = Graphiti(
        "bolt://localhost:7687",
        "neo4j", 
        "Sk1pper(())",
        llm_client=llm_client,
        embedder=embedder
    )
    
    await graphiti.build_indices_and_constraints()
    print("✅ Graphiti initialized with llama3.1:8b")
    
    # Test with the same content that worked with OpenAI
    test_content = """
    Captain Ioannis Theofanides was a Greek naval officer during the 1922 Smyrna crisis. 
    He worked with Asa Jennings to evacuate refugees. Jennings was an American YMCA worker.
    They coordinated with Turkish forces led by Mustafa Kemal Ataturk.
    """
    
    print("📝 Adding test episode with llama3.1:8b...")
    
    await graphiti.add_episode(
        name="Llama3.1 Test Episode",
        episode_body=test_content,
        source=EpisodeType.text,
        source_description="Test with llama3.1:8b",
        reference_time=datetime(1922, 9, 15, tzinfo=timezone.utc)
    )
    
    print("✅ Episode added")
    await asyncio.sleep(3)
    
    # Check what was created
    print("\n🔍 Checking what llama3.1:8b created...")
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        result = session.run('MATCH (n) RETURN DISTINCT labels(n) as labels, count(*) as count ORDER BY count DESC')
        print("llama3.1:8b created:")
        for record in result:
            print(f"   {record[0]}: {record[1]} nodes")
            
        result = session.run('MATCH (n:Entity) RETURN n.name LIMIT 10')
        entities = [record[0] for record in result]
        if entities:
            print("Entities extracted:")
            for entity in entities:
                print(f"   - {entity}")
        else:
            print("❌ No entities extracted")
            
        result = session.run('MATCH ()-[r]->() WHERE r.fact IS NOT NULL RETURN r.fact LIMIT 3')
        facts = [record[0] for record in result]
        if facts:
            print("Facts generated:")
            for fact in facts:
                print(f"   • {fact}")
        else:
            print("❌ No facts generated")
    driver.close()
    
    # Test search
    if entities:
        print("\n🔍 Testing search with llama3.1:8b...")
        try:
            results = await graphiti.search("Asa Jennings", num_results=2)
            if results and len(results) > 0:
                print(f"✅ llama3.1:8b search successful: {len(results)} results")
                for result in results:
                    if hasattr(result, 'fact'):
                        print(f"   • {result.fact}")
            else:
                print("❌ No search results")
        except Exception as e:
            print(f"❌ Search error: {e}")
    
    print(f"\n🧪 BETTER MODEL TEST COMPLETE!")

if __name__ == "__main__":
    asyncio.run(test_better_model())