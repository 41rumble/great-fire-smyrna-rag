#!/usr/bin/env python3
"""
Test Graphiti with OpenAI to see if embedding works as expected
"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from graphiti_core import Graphiti

async def test_with_openai():
    """Test the exact same process but with OpenAI"""
    
    print("🤖 TESTING GRAPHITI WITH OPENAI")
    print("=" * 50)
    
    # Check if OpenAI key is available
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("💡 Set your OpenAI key: export OPENAI_API_KEY='your_key_here'")
        return
    
    print("✅ OpenAI API key found")
    
    # Initialize Graphiti with default OpenAI (no custom clients)
    print("🔧 Initializing Graphiti with default OpenAI...")
    
    graphiti = Graphiti(
        uri="bolt://localhost:7687/graphiti-openai-test",
        user="neo4j",
        password="Sk1pper(())"
        # No custom llm_client or embedder - let it use OpenAI defaults
    )
    
    print("✅ Graphiti initialized with OpenAI defaults")
    
    # Build indices and constraints
    print("🔨 Building indices and constraints...")
    try:
        await graphiti.build_indices_and_constraints()
        print("✅ Indices and constraints built")
    except Exception as e:
        print(f"⚠️  Indices/constraints: {e}")
    
    # Get a text file
    text_files_dir = Path("text_files")
    text_files = list(text_files_dir.glob("*.txt"))[:1]
    
    if not text_files:
        print("❌ No text files found")
        return
    
    text_file = text_files[0]
    print(f"📄 Testing with: {text_file.name}")
    
    # Read content
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📊 Content length: {len(content)} characters")
    
    # Add episode with OpenAI
    print(f"\n📝 Adding episode with OpenAI...")
    
    try:
        await graphiti.add_episode(
            name=f'OpenAI Test - {text_file.stem}',
            episode_body=content,
            source_description='OpenAI test file',
            reference_time=datetime.now(timezone.utc)
        )
        
        print(f"✅ Episode added with OpenAI")
        
    except Exception as e:
        print(f"❌ Failed to add episode with OpenAI: {e}")
        return
    
    # Test search with OpenAI
    print(f"\n🔍 Testing search with OpenAI...")
    
    try:
        results = await graphiti.search(
            query="Captain Theofanides",
            num_results=2
        )
        
        if results and hasattr(results, 'results') and len(results.results) > 0:
            print(f"✅ OpenAI search successful! Found {len(results.results)} results")
            for i, result in enumerate(results.results):
                if hasattr(result, 'episode') and hasattr(result.episode, 'name'):
                    print(f"   {i+1}. {result.episode.name}")
                elif hasattr(result, 'name'):
                    print(f"   {i+1}. {result.name}")
                else:
                    print(f"   {i+1}. {str(result)[:100]}...")
        else:
            print("❌ OpenAI search found no results")
            
    except Exception as e:
        print(f"❌ OpenAI search error: {e}")
    
    # Check what was actually created in the database
    print(f"\n🔍 Checking database contents...")
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    
    try:
        with driver.session(database="neo4j") as session:  # OpenAI probably uses default DB
            # Check recent nodes
            result = session.run("""
            MATCH (n) 
            WHERE n.created_at > datetime() - duration({minutes: 5})
            RETURN DISTINCT labels(n) as labels, count(*) as count 
            ORDER BY count DESC
            """)
            
            print("Recent nodes created by OpenAI:")
            for record in result:
                print(f"   {record['labels']} - {record['count']} nodes")
            
            # Check for embeddings
            result = session.run("""
            MATCH (n) 
            WHERE n.created_at > datetime() - duration({minutes: 5}) 
            AND n.embedding IS NOT NULL
            RETURN labels(n) as labels, count(*) as count, avg(size(n.embedding)) as avg_emb_size
            """)
            
            print("\nNodes with embeddings:")
            for record in result:
                print(f"   {record['labels']} - {record['count']} nodes - Avg size: {record['avg_emb_size']}")
            
    except Exception as e:
        print(f"⚠️  Database check: {e}")
    finally:
        driver.close()
    
    print(f"\n🤖 OPENAI TEST COMPLETE!")
    print("💰 Note: This test may incur small OpenAI charges")

if __name__ == "__main__":
    asyncio.run(test_with_openai())