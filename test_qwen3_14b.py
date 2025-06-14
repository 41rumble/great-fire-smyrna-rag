#!/usr/bin/env python3
"""
Test with qwen3:14b - your installed model that should be excellent at structured output
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

class Qwen3LLMClient(LLMClient):
    """LLM client using qwen3:14b - excellent large model for structured output"""
    
    def __init__(self, model_name="qwen3:14b", base_url="http://localhost:11434"):
        config = LLMConfig(
            model=model_name,
            base_url=base_url,
            max_tokens=4000,
            temperature=0.1  # Low temperature for consistent structured output
        )
        super().__init__(config)
        self.model_name = model_name
        self.base_url = base_url
        print(f"🧠 Using {model_name} - powerful model, excellent at structured output")
    
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
            
            # Add emphasis for structured output if this looks like an extraction task
            if any(keyword in prompt.lower() for keyword in ["extract", "json", "entities", "facts"]):
                prompt += "\nProvide a precise, well-structured response following the exact format requested."
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1
                    }
                }
            )
            
            if response.status_code == 200:
                content = response.json().get("response", "")
                return {"content": content}
            return {"content": ""}
        except Exception as e:
            print(f"❌ Qwen3 LLM error: {e}")
            return {"content": ""}

class FastEmbedder(EmbedderClient):
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

async def test_qwen3_14b():
    print("🧠 TESTING QWEN3:14B - POWERFUL STRUCTURED OUTPUT")
    print("=" * 60)
    
    # Verify qwen3:14b is available
    try:
        response = requests.get("http://localhost:11434/api/tags")
        models = [m["name"] for m in response.json().get("models", [])]
        
        if "qwen3:14b" in models:
            print("✅ qwen3:14b confirmed available")
        else:
            print("❌ qwen3:14b not found in available models")
            print("Available models:")
            for model in models:
                print(f"   - {model}")
            return
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return
    
    # Clean database
    print("🧹 Cleaning database...")
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()
    
    # Initialize with qwen3:14b
    llm_client = Qwen3LLMClient()
    embedder = FastEmbedder()
    
    graphiti = Graphiti(
        "bolt://localhost:7687",
        "neo4j", 
        "Sk1pper(())",
        llm_client=llm_client,
        embedder=embedder
    )
    
    await graphiti.build_indices_and_constraints()
    print("✅ Graphiti initialized with qwen3:14b")
    
    # Test with rich historical content
    test_content = """
    Captain Ioannis Theofanides was a Greek naval officer during the 1922 Smyrna crisis. 
    He worked with Asa Jennings to evacuate refugees from the burning city. Jennings was an American YMCA worker 
    who became a key figure in the refugee evacuation. They coordinated with Turkish forces led by Mustafa Kemal Ataturk.
    The evacuation involved Greek ships, American naval vessels, and international relief organizations.
    Thousands of refugees were saved through their coordinated efforts during September 1922.
    """
    
    print("📝 Adding episode with qwen3:14b for entity extraction...")
    
    await graphiti.add_episode(
        name="Qwen3 Historical Test",
        episode_body=test_content,
        source=EpisodeType.text,
        source_description="Test qwen3:14b entity extraction",
        reference_time=datetime(1922, 9, 15, tzinfo=timezone.utc)
    )
    
    print("✅ Episode added, waiting for processing...")
    await asyncio.sleep(3)
    
    # Check what qwen3:14b created
    print("\n🔍 Analyzing qwen3:14b results...")
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        # Check node types
        result = session.run('MATCH (n) RETURN DISTINCT labels(n) as labels, count(*) as count ORDER BY count DESC')
        print("qwen3:14b created:")
        for record in result:
            print(f"   {record[0]}: {record[1]} nodes")
            
        # Check entities
        result = session.run('MATCH (n:Entity) RETURN n.name ORDER BY n.name LIMIT 10')
        entities = [record[0] for record in result]
        if entities:
            print("\n✅ Entities extracted by qwen3:14b:")
            for entity in entities[:8]:  # Show first 8
                print(f"   - {entity}")
            if len(entities) > 8:
                print(f"   ... and {len(entities) - 8} more")
        else:
            print("\n❌ No entities extracted")
            
        # Check facts/relationships
        result = session.run('MATCH ()-[r]->() WHERE r.fact IS NOT NULL RETURN r.fact LIMIT 5')
        facts = [record[0] for record in result]
        if facts:
            print("\n✅ Facts generated by qwen3:14b:")
            for fact in facts:
                print(f"   • {fact}")
        else:
            print("\n❌ No facts generated")
            
        # Count relationships
        result = session.run('MATCH ()-[r]->() RETURN count(r) as total_facts')
        total_facts = result.single()['total_facts']
        print(f"\nTotal relationships: {total_facts}")
        
    driver.close()
    
    # Test search if entities were created
    if entities:
        print("\n🔍 Testing search with qwen3:14b...")
        
        test_searches = ["Asa Jennings", "Greek naval officer", "Smyrna crisis", "refugee evacuation"]
        
        for search_term in test_searches:
            try:
                results = await graphiti.search(search_term, num_results=2)
                if results and len(results) > 0:
                    print(f"✅ '{search_term}': {len(results)} results")
                    for result in results:
                        if hasattr(result, 'fact'):
                            print(f"   • {result.fact}")
                else:
                    print(f"❌ '{search_term}': No results")
            except Exception as e:
                print(f"❌ '{search_term}': Error - {e}")
    
    print(f"\n🧠 QWEN3:14B TEST COMPLETE!")
    
    if entities:
        print("🎉 SUCCESS! qwen3:14b successfully extracted entities and facts!")
        print("📚 Ready to process your historical books with qwen3:14b")
    else:
        print("❌ Entity extraction still not working - may need different approach")

if __name__ == "__main__":
    asyncio.run(test_qwen3_14b())