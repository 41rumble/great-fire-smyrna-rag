#!/usr/bin/env python3
"""
Test with qwen2.5:3b - smaller but excellent at structured output
"""

import asyncio
import requests
from datetime import datetime, timezone
from neo4j import GraphDatabase

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.llm_client import LLMClient, LLMConfig
from graphiti_core.embedder import EmbedderClient
from typing import List

class QwenLLMClient(LLMClient):
    """LLM client using qwen2.5:3b - excellent at structured output"""
    
    def __init__(self, model_name="qwen2.5:3b", base_url="http://localhost:11434"):
        config = LLMConfig(
            model=model_name,
            base_url=base_url,
            max_tokens=4000,
            temperature=0.1
        )
        super().__init__(config)
        self.model_name = model_name
        self.base_url = base_url
        print(f"🦙 Using {model_name} - known for excellent structured output")
    
    async def _generate_response(self, messages: list, response_model=None, max_tokens: int = 4000, model_size=None) -> dict:
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
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.1
                    }
                }
            )
            
            if response.status_code == 200:
                content = response.json().get("response", "")
                return {"content": content}
            return {"content": ""}
        except:
            return {"content": ""}

class SimpleEmbedder(EmbedderClient):
    def __init__(self):
        super().__init__()
    
    async def create(self, input_data):
        try:
            text = str(input_data) if not isinstance(input_data, list) else " ".join(str(x) for x in input_data)
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text}
            )
            if response.status_code == 200:
                return response.json().get("embedding", [0.0] * 768)
            return [0.0] * 768
        except:
            return [0.0] * 768
    
    async def create_batch(self, input_data_list: List[str]):
        return [await self.create(data) for data in input_data_list]

async def test_qwen():
    print("🧪 TESTING QWEN2.5:3B - QUICK STRUCTURED OUTPUT TEST")
    print("=" * 60)
    
    # Check/download qwen2.5:3b (much smaller - ~2GB)
    try:
        response = requests.get("http://localhost:11434/api/tags")
        models = [m["name"] for m in response.json().get("models", [])]
        
        if "qwen2.5:3b" not in models:
            print("📥 Pulling qwen2.5:3b (smaller model, ~2GB)...")
            requests.post("http://localhost:11434/api/pull", json={"name": "qwen2.5:3b"})
            print("✅ Downloaded")
        else:
            print("✅ qwen2.5:3b already available")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Clean database
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()
    
    # Test with qwen2.5:3b
    llm_client = QwenLLMClient()
    embedder = SimpleEmbedder()
    
    graphiti = Graphiti(
        "bolt://localhost:7687",
        "neo4j", 
        "Sk1pper(())",
        llm_client=llm_client,
        embedder=embedder
    )
    
    await graphiti.build_indices_and_constraints()
    
    # Same test content
    test_content = """
    Captain Ioannis Theofanides was a Greek naval officer during the 1922 Smyrna crisis. 
    He worked with Asa Jennings to evacuate refugees. Jennings was an American YMCA worker.
    They coordinated with Turkish forces led by Mustafa Kemal Ataturk.
    """
    
    print("📝 Testing qwen2.5:3b entity extraction...")
    
    await graphiti.add_episode(
        name="Qwen Test Episode",
        episode_body=test_content,
        source=EpisodeType.text,
        source_description="Test with qwen2.5:3b",
        reference_time=datetime(1922, 9, 15, tzinfo=timezone.utc)
    )
    
    await asyncio.sleep(2)
    
    # Check results
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        result = session.run('MATCH (n) RETURN DISTINCT labels(n) as labels, count(*) as count ORDER BY count DESC')
        print("qwen2.5:3b created:")
        for record in result:
            print(f"   {record[0]}: {record[1]} nodes")
            
        result = session.run('MATCH (n:Entity) RETURN n.name LIMIT 5')
        entities = [record[0] for record in result]
        if entities:
            print("✅ Entities extracted:")
            for entity in entities:
                print(f"   - {entity}")
                
            # Test search
            print("\n🔍 Testing search...")
            try:
                results = await graphiti.search("Asa Jennings", num_results=2)
                if results and len(results) > 0:
                    print(f"✅ qwen2.5:3b search works! Found {len(results)} results")
                    for result in results:
                        if hasattr(result, 'fact'):
                            print(f"   • {result.fact}")
                else:
                    print("❌ No search results")
            except Exception as e:
                print(f"❌ Search error: {e}")
        else:
            print("❌ No entities extracted - structured output still not working")
    driver.close()

if __name__ == "__main__":
    asyncio.run(test_qwen())