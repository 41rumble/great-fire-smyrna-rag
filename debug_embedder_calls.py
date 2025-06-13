#!/usr/bin/env python3
"""
Debug embedder to see if Graphiti is calling it
"""

import asyncio
import requests
from datetime import datetime
from typing import List
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMClient, LLMConfig
from graphiti_core.embedder import EmbedderClient

class DebugOllamaLLMClient(LLMClient):
    """Debug LLM client that logs calls"""
    
    def __init__(self, model_name="mistral-small3.1:latest", base_url="http://localhost:11434"):
        config = LLMConfig(
            model=model_name,
            base_url=base_url,
            max_tokens=4000,
            temperature=0.7
        )
        super().__init__(config)
        self.model_name = model_name
        self.base_url = base_url
        print(f"🤖 DEBUG: LLM Client initialized with {model_name}")
    
    async def _generate_response(self, messages: list, response_model=None, max_tokens: int = 4000, model_size=None) -> dict:
        print(f"🤖 DEBUG: LLM called with {len(messages)} messages")
        try:
            prompt = ""
            for message in messages:
                if hasattr(message, 'content'):
                    prompt += f"{message.role}: {message.content}\n"
                elif isinstance(message, dict):
                    prompt += f"{message.get('role', 'user')}: {message.get('content', '')}\n"
                else:
                    prompt += str(message) + "\n"
            
            print(f"🤖 DEBUG: Prompt preview: {prompt[:100]}...")
            
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
                print(f"🤖 DEBUG: LLM response length: {len(content)}")
                return {"content": content}
            else:
                print(f"🤖 DEBUG: LLM failed with status {response.status_code}")
                return {"content": ""}
                
        except Exception as e:
            print(f"🤖 DEBUG: LLM error: {e}")
            return {"content": ""}

class DebugOllamaEmbedder(EmbedderClient):
    """Debug embedder that logs all calls"""
    
    def __init__(self, model_name="nomic-embed-text:latest", base_url="http://localhost:11434"):
        super().__init__()
        self.model_name = model_name
        self.base_url = base_url
        self.call_count = 0
        print(f"🔢 DEBUG: Embedder initialized with {model_name}")
    
    async def create(self, input_data) -> List[float]:
        self.call_count += 1
        print(f"🔢 DEBUG: Embedder call #{self.call_count}")
        
        try:
            if isinstance(input_data, list):
                text = " ".join(str(item) for item in input_data)
            else:
                text = str(input_data)
            
            print(f"🔢 DEBUG: Embedding text: {text[:100]}...")
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                embedding = response.json().get("embedding", [])
                print(f"🔢 DEBUG: Generated embedding with {len(embedding)} dimensions")
                return embedding
            else:
                print(f"🔢 DEBUG: Embedding failed with status {response.status_code}")
                return [0.0] * 768
                
        except Exception as e:
            print(f"🔢 DEBUG: Embedding error: {e}")
            return [0.0] * 768
    
    async def create_batch(self, texts: List[str]) -> List[List[float]]:
        print(f"🔢 DEBUG: Batch embedding called with {len(texts)} texts")
        embeddings = []
        for text in texts:
            embedding = await self.create(text)
            embeddings.append(embedding)
        return embeddings

async def test_debug_embedder():
    """Test with debug embedder to see what's being called"""
    
    print("🐛 TESTING WITH DEBUG EMBEDDER")
    print("=" * 60)
    
    llm_client = DebugOllamaLLMClient()
    embedder = DebugOllamaEmbedder()
    
    graphiti = Graphiti(
        uri="bolt://localhost:7687/graphiti-clean",
        user="neo4j",
        password="Sk1pper(())",
        llm_client=llm_client,
        embedder=embedder
    )
    
    print("✅ Debug Graphiti initialized")
    
    print("\n🔄 Adding test episode...")
    
    try:
        await graphiti.add_episode(
            name="DEBUG TEST EPISODE",
            episode_body="This is a debug test episode to see if embeddings are being called properly.",
            source_description="Debug Test",
            reference_time=datetime(1922, 9, 15)
        )
        
        print("✅ Episode added")
        print(f"📊 Total embedder calls: {embedder.call_count}")
        
    except Exception as e:
        print(f"❌ Episode add failed: {e}")
    
    print(f"\n🐛 DEBUG TEST COMPLETE!")
    print(f"📊 Final embedder call count: {embedder.call_count}")

if __name__ == "__main__":
    asyncio.run(test_debug_embedder())