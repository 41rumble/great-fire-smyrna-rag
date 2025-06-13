#!/usr/bin/env python3
"""
Set up Graphiti with local Ollama embeddings instead of OpenAI
"""

import os
import asyncio
from datetime import datetime
from neo4j import GraphDatabase
import requests
import numpy as np

class OllamaEmbeddingProvider:
    """Custom embedding provider using local Ollama"""
    
    def __init__(self, model_name="nomic-embed-text", ollama_url="http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        
    def get_embeddings(self, texts):
        """Get embeddings from Ollama"""
        embeddings = []
        
        for text in texts:
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": self.model_name,
                        "prompt": text
                    }
                )
                
                if response.status_code == 200:
                    embedding = response.json().get("embedding", [])
                    embeddings.append(embedding)
                else:
                    print(f"❌ Embedding failed for text: {text[:50]}...")
                    embeddings.append([0.0] * 768)  # Fallback empty embedding
                    
            except Exception as e:
                print(f"❌ Embedding error: {e}")
                embeddings.append([0.0] * 768)  # Fallback empty embedding
        
        return embeddings

async def setup_graphiti_with_ollama():
    """Set up Graphiti using Ollama embeddings"""
    
    print("🦙 SETTING UP GRAPHITI WITH OLLAMA EMBEDDINGS")
    print("=" * 60)
    
    # First, ensure the embedding model is available
    print("📥 Checking if embedding model is available...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json().get("models", [])
        model_names = [model["name"] for model in models]
        
        if "nomic-embed-text:latest" not in model_names:
            print("📥 Downloading nomic-embed-text model...")
            pull_response = requests.post(
                "http://localhost:11434/api/pull",
                json={"name": "nomic-embed-text"}
            )
            if pull_response.status_code == 200:
                print("✅ Model downloaded successfully")
            else:
                print("❌ Failed to download model")
                return
        else:
            print("✅ Model already available")
            
    except Exception as e:
        print(f"❌ Could not connect to Ollama: {e}")
        return
    
    # Initialize embedding provider
    embedder = OllamaEmbeddingProvider()
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "Sk1pper(())")
    )
    
    # Get episodes from all sources
    with driver.session(database="the-great-fire-db") as session:
        query = """
        MATCH (e:Episode)-[:FROM_SOURCE]->(s:Source)
        WHERE e.content IS NOT NULL AND size(e.content) > 100
        RETURN e.name as name, e.content as content, 
               s.title as source_title, s.author as source_author, s.sourceId as sourceId
        ORDER BY s.sourceId
        """
        
        result = session.run(query)
        episodes = []
        
        for record in result:
            episodes.append({
                "name": record["name"],
                "content": record["content"],
                "source_title": record["source_title"],
                "source_author": record["source_author"],
                "sourceId": record["sourceId"]
            })
    
    if not episodes:
        print("❌ No episodes found")
        return
    
    print(f"📖 Found {len(episodes)} episodes to embed")
    
    # Process episodes in batches
    batch_size = 10
    embedded_count = 0
    
    for i in range(0, len(episodes), batch_size):
        batch = episodes[i:i+batch_size]
        
        print(f"🔄 Processing batch {i//batch_size + 1}/{(len(episodes)-1)//batch_size + 1}")
        
        # Prepare texts for embedding
        texts = []
        for episode in batch:
            # Create clean text for embedding
            text = f"{episode['source_title']} by {episode['source_author']}: {episode['content']}"
            texts.append(text[:2000])  # Limit text length
        
        # Get embeddings
        embeddings = embedder.get_embeddings(texts)
        
        # Store embeddings in Neo4j
        with driver.session(database="the-great-fire-db") as session:
            for episode, embedding in zip(batch, embeddings):
                if len(embedding) > 0:
                    session.run("""
                    MATCH (e:Episode {name: $name})
                    WHERE EXISTS {
                        MATCH (e)-[:FROM_SOURCE]->(s:Source {sourceId: $sourceId})
                    }
                    SET e.embedding = $embedding,
                        e.embedding_model = 'nomic-embed-text',
                        e.embedded_at = datetime()
                    """, 
                        name=episode['name'],
                        sourceId=episode['sourceId'],
                        embedding=embedding
                    )
                    embedded_count += 1
                    print(f"  ✅ Embedded: {episode['name'][:50]}...")
        
        # Small delay to avoid overwhelming Ollama
        await asyncio.sleep(2)
    
    driver.close()
    
    print(f"\n🎉 OLLAMA EMBEDDINGS COMPLETE!")
    print(f"📊 Successfully embedded {embedded_count} episodes")
    print("🧠 Your local semantic search is now ready!")

if __name__ == "__main__":
    asyncio.run(setup_graphiti_with_ollama())