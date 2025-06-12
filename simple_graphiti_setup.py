#!/usr/bin/env python3
"""
Simple Graphiti setup that initializes an empty Graphiti instance
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Set OpenAI key for Graphiti
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
if OPENAI_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_KEY
    from graphiti_core import Graphiti
else:
    print("❌ OpenAI API key required")
    exit(1)

async def initialize_graphiti():
    """Initialize Graphiti with required schema"""
    print("🚀 Initializing Graphiti schema...")
    
    try:
        # Initialize Graphiti - this should create required indexes
        graphiti = Graphiti(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD")
        )
        
        print("✅ Graphiti initialized successfully")
        
        # Add a simple test episode to ensure schema is set up
        print("📝 Adding test episode to establish schema...")
        
        from datetime import datetime
        await graphiti.add_episode(
            name="Graphiti Test Episode",
            episode_body="This is a test episode to initialize the Graphiti schema and indexes.",
            source_description="Test initialization",
            reference_time=datetime(2024, 1, 1)
        )
        
        print("✅ Test episode added - schema established")
        
        # Test search to verify everything works
        print("🔍 Testing search functionality...")
        results = await graphiti.search("test", num_results=1)
        
        if results and hasattr(results, 'results'):
            print(f"✅ Search working - found {len(results.results)} results")
        else:
            print("⚠️  Search returned no results (may be normal)")
            
        print("\n🎉 Graphiti setup complete!")
        print("💡 Your system is ready for semantic search")
        
    except Exception as e:
        print(f"❌ Graphiti initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(initialize_graphiti())