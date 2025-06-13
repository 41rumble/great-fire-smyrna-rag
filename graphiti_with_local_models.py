#!/usr/bin/env python3
"""
Set up Graphiti with local Ollama models for LLM and embeddings
"""

import os
import asyncio
import requests
from datetime import datetime
from neo4j import GraphDatabase
from typing import List
import json

# Import Graphiti and base classes
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMClient, LLMConfig
from graphiti_core.embedder import EmbedderClient

class OllamaLLMClient(LLMClient):
    """Custom LLM client using local Ollama"""
    
    def __init__(self, model_name="mistral-small3.1:latest", base_url="http://localhost:11434"):
        # Create a config for the parent class
        config = LLMConfig(
            model=model_name,
            base_url=base_url,
            max_tokens=4000,
            temperature=0.7
        )
        super().__init__(config)
        self.model_name = model_name
        self.base_url = base_url
    
    async def _generate_response(
        self,
        messages: list,
        response_model=None,
        max_tokens: int = 4000,
        model_size=None
    ) -> dict:
        """Generate response using Ollama with correct method signature"""
        try:
            # Convert messages to a single prompt
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
                        "num_predict": max_tokens
                    }
                }
            )
            
            if response.status_code == 200:
                content = response.json().get("response", "")
                return {"content": content}
            else:
                print(f"❌ LLM generation failed: {response.status_code}")
                return {"content": ""}
                
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return {"content": ""}

class OllamaEmbedder(EmbedderClient):
    """Custom embedder using local Ollama"""
    
    def __init__(self, model_name="nomic-embed-text:latest", base_url="http://localhost:11434"):
        super().__init__()
        self.model_name = model_name
        self.base_url = base_url
    
    async def create(self, text: str) -> List[float]:
        """Create single embedding"""
        try:
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
                print(f"❌ Embedding failed for text: {text[:50]}...")
                return [0.0] * 768  # Fallback
                
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            return [0.0] * 768  # Fallback
    
    async def create_batch(self, texts: List[str]) -> List[List[float]]:
        """Create batch embeddings"""
        embeddings = []
        
        for text in texts:
            embedding = await self.create(text)
            embeddings.append(embedding)
        
        return embeddings

async def setup_graphiti_with_local():
    """Set up Graphiti with local Ollama models"""
    
    print("🦙 SETTING UP GRAPHITI WITH LOCAL OLLAMA")
    print("=" * 60)
    
    # Initialize local model clients
    llm_client = OllamaLLMClient()
    embedder = OllamaEmbedder()
    
    # Test that models are available
    print("🔍 Testing local models...")
    
    try:
        # Test LLM
        test_response = await llm_client._generate_response([{"role": "user", "content": "Hello"}])
        if test_response and test_response.get("content"):
            print("✅ LLM (mistral-small3.1) working")
        else:
            print("❌ LLM test failed")
            return
        
        # Test embedder
        test_embeddings = await embedder.create_batch(["test"])
        if test_embeddings and len(test_embeddings[0]) > 0:
            print("✅ Embedder (nomic-embed-text) working")
        else:
            print("❌ Embedder test failed")
            return
            
    except Exception as e:
        print(f"❌ Model testing failed: {e}")
        return
    
    # Initialize Graphiti with local models
    print("🧠 Initializing Graphiti with local models...")
    
    graphiti = Graphiti(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="Sk1pper(())",
        llm_client=llm_client,
        embedder=embedder
    )
    
    # Connect to Neo4j to get your existing data
    neo4j_driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "Sk1pper(())")
    )
    
    # Get episodes from all sources
    print("📖 Reading your book data...")
    
    with neo4j_driver.session(database="the-great-fire-db") as session:
        query = """
        MATCH (e:Episode)-[:FROM_SOURCE]->(s:Source)
        WHERE e.content IS NOT NULL AND size(e.content) > 200
        RETURN e.name as name, e.content as content, 
               s.title as source_title, s.author as source_author, 
               s.sourceId as sourceId, s.perspective as perspective,
               e.chapter_title as chapter
        ORDER BY s.sourceId, e.name
        LIMIT 20
        """
        
        result = session.run(query)
        episodes = []
        
        for record in result:
            episodes.append({
                "name": record["name"],
                "content": record["content"],
                "source_title": record["source_title"],
                "source_author": record["source_author"],
                "sourceId": record["sourceId"],
                "perspective": record["perspective"],
                "chapter": record["chapter"]
            })
    
    neo4j_driver.close()
    
    if not episodes:
        print("❌ No episodes found")
        return
    
    print(f"📚 Found {len(episodes)} episodes to ingest")
    
    # Group by source
    sources = {}
    for episode in episodes:
        source_id = episode['sourceId']
        if source_id not in sources:
            sources[source_id] = []
        sources[source_id].append(episode)
    
    # Ingest each source
    for source_id, source_episodes in sources.items():
        source_title = source_episodes[0]['source_title']
        print(f"\n📚 Processing: {source_title}")
        print(f"   Episodes: {len(source_episodes)}")
        
        for i, episode in enumerate(source_episodes):
            print(f"   🔄 Episode {i+1}/{len(source_episodes)}: {episode['name'][:50]}...")
            
            try:
                # Create rich episode body
                episode_body = f"""
SOURCE: {episode['source_title']} by {episode['source_author']}
PERSPECTIVE: {episode['perspective']}
CHAPTER: {episode['chapter']}

{episode['content']}
"""
                
                # Add to Graphiti
                await graphiti.add_episode(
                    name=f"[{source_id}] {episode['name']}",
                    episode_body=episode_body,
                    source_description=f"{episode['source_title']} - {episode['chapter']}",
                    reference_time=datetime(1922, 9, 15)
                )
                
                print(f"      ✅ Added successfully")
                
            except Exception as e:
                print(f"      ❌ Failed: {e}")
            
            # Small delay
            await asyncio.sleep(1)
    
    # Test search
    print(f"\n🔍 Testing search...")
    
    test_queries = ["Girdis family", "Smyrna fire"]
    
    for query in test_queries:
        try:
            results = await graphiti.search(query=query, num_results=2)
            
            if results and hasattr(results, 'results') and len(results.results) > 0:
                print(f"✅ '{query}': {len(results.results)} results found")
            else:
                print(f"❌ '{query}': No results")
                
        except Exception as e:
            print(f"❌ '{query}': Search error - {e}")
    
    print(f"\n🎉 GRAPHITI WITH LOCAL MODELS COMPLETE!")
    print("🦙 Using 100% local Ollama - no external API calls!")

if __name__ == "__main__":
    asyncio.run(setup_graphiti_with_local())