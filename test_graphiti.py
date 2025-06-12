#!/usr/bin/env python3
"""
Quick test of Graphiti semantic search
"""

import asyncio
import os

# Set OpenAI key from environment for test
from dotenv import load_dotenv
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
if OPENAI_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_KEY
else:
    print("❌ No OpenAI API key found in .env file")
    exit(1)

from graphiti_core import Graphiti

async def test_semantic_search():
    print("🧠 Testing Graphiti semantic search...")
    
    try:
        graphiti = Graphiti(
            uri="bolt://localhost:7687",
            user="neo4j", 
            password="Sk1pper(())"
        )
        
        # Test semantic search
        query = "What were the underlying tensions between American and Turkish perspectives?"
        print(f"🔍 Query: {query}")
        
        results = await graphiti.search(query, num_results=5)
        
        if results and hasattr(results, 'results') and len(results.results) > 0:
            print(f"✅ Found {len(results.results)} semantic matches!")
            
            for i, result in enumerate(results.results[:3]):
                if hasattr(result, 'episode'):
                    name = getattr(result.episode, 'name', f'Episode {i+1}')
                    content = getattr(result.episode, 'content', 'No content')
                    
                    print(f"\n📄 Match {i+1}: {name}")
                    print(f"Content: {content[:300]}...")
                    
                    if hasattr(result, 'score'):
                        print(f"Relevance: {result.score}")
        else:
            print("❌ No semantic matches found")
            
    except Exception as e:
        print(f"❌ Graphiti test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_semantic_search())