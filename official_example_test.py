#!/usr/bin/env python3
"""
Test using the EXACT official example approach
"""

import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Import exactly like the official example
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF

load_dotenv()

async def official_example_test():
    """Test using the exact official example approach"""
    
    print("📋 OFFICIAL EXAMPLE TEST")
    print("=" * 40)
    
    # Clean database first
    print("🧹 Cleaning database...")
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()
    print("✅ Database cleaned")
    
    # Initialize EXACTLY like official example
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'Sk1pper(())')
    
    # Initialize Graphiti with Neo4j connection (exact same way)
    graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
    
    print("✅ Graphiti initialized (official way)")
    
    # Build indices and constraints
    await graphiti.build_indices_and_constraints()
    print("✅ Indices built")
    
    # Create episodes EXACTLY like the example
    episodes = [
        {
            'content': 'Asa Jennings was an American YMCA worker in Smyrna during the 1922 crisis.',
            'type': EpisodeType.text,
            'description': 'historical text'
        },
        {
            'content': {
                'name': 'Mustafa Kemal Ataturk',
                'position': 'Turkish leader',
                'location': 'Turkey'
            },
            'type': EpisodeType.json,
            'description': 'historical metadata'
        }
    ]
    
    print("📝 Adding episodes (official format)...")
    
    # Add episodes to the graph EXACTLY like the example
    for i, episode in enumerate(episodes):
        # Convert content to string if it's JSON
        content = episode['content']
        if episode['type'] == EpisodeType.json:
            import json
            content = json.dumps(content)
            
        await graphiti.add_episode(
            name=f'Historical Episode {i}',
            episode_body=content,
            source=episode['type'],  # This parameter was missing!
            source_description=episode['description'],
            reference_time=datetime.now(timezone.utc)
        )
        print(f"   ✅ Episode {i} added")
    
    print("✅ All episodes added")
    
    # Wait for processing
    print("⏳ Waiting for processing...")
    await asyncio.sleep(3)
    
    # Test search EXACTLY like the example
    print("\n🔍 Testing search (official example style)...")
    
    try:
        # Basic hybrid search like the example
        results = await graphiti.search('Who was Asa Jennings?')
        
        if results and len(results) > 0:
            print(f"✅ Search successful! Found {len(results)} results")
            for i, result in enumerate(results):
                print(f"   {i+1}. {result}")
                
            # Try center node search like the example
            if hasattr(results[0], 'source_node_uuid'):
                center_node_uuid = results[0].source_node_uuid
                reranked_results = await graphiti.search(
                    'Who was Asa Jennings?', 
                    center_node_uuid=center_node_uuid
                )
                print(f"✅ Reranked search found {len(reranked_results)} results")
        else:
            print("❌ No results from official example approach")
            
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    print(f"\n📋 OFFICIAL EXAMPLE TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(official_example_test())