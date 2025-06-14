#!/usr/bin/env python3
"""
Basic Graphiti test - no complications, just see what it actually does
"""

import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from graphiti_core import Graphiti

# Load environment variables
load_dotenv()

async def basic_test():
    """Most basic Graphiti test possible"""
    
    print("📚 BASIC GRAPHITI TEST")
    print("=" * 40)
    
    # Check OpenAI key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"✅ OpenAI key loaded: {openai_key[:10]}...")
    else:
        print("❌ No OpenAI key found")
    
    # Simplest possible initialization
    graphiti = Graphiti(
        uri="bolt://localhost:7687",
        user="neo4j", 
        password="Sk1pper(())"
    )
    
    print("✅ Graphiti initialized (basic)")
    
    # Build indices (as shown in examples)
    await graphiti.build_indices_and_constraints()
    print("✅ Indices built")
    
    # Add ONE simple episode
    simple_text = """
    Captain Ioannis Theofanides was a Greek naval officer during the Smyrna crisis of 1922. 
    He worked closely with Asa Jennings to evacuate refugees from the burning city. 
    The cooperation between Greek and American forces was crucial during this humanitarian crisis.
    """
    
    print("📝 Adding simple episode...")
    
    await graphiti.add_episode(
        name="Greek Naval Officer", 
        episode_body=simple_text,
        source_description="Historical text",
        reference_time=datetime(1922, 9, 15, tzinfo=timezone.utc)
    )
    
    print("✅ Episode added")
    
    # Try simple search
    print("🔍 Searching for 'Theofanides'...")
    
    results = await graphiti.search("Theofanides", num_results=3)
    
    if results and hasattr(results, 'results'):
        print(f"✅ Found {len(results.results)} results")
        for i, result in enumerate(results.results):
            print(f"  {i+1}. {result}")
    else:
        print("❌ No results")
    
    print("\n📊 Done")

if __name__ == "__main__":
    asyncio.run(basic_test())