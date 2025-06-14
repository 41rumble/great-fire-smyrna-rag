#!/usr/bin/env python3
"""
Source-aware search across multiple books
"""

import asyncio
from neo4j import GraphDatabase
from graphiti_core import Graphiti

async def search_with_sources(query, num_results=10):
    """Search with source book tracking"""
    
    print(f"🔍 SEARCHING: '{query}'")
    print("=" * 60)
    
    # Initialize Graphiti
    graphiti = Graphiti("bolt://localhost:7687", "neo4j", "Sk1pper(())")
    
    # Get search results
    results = await graphiti.search(query, num_results=num_results)
    
    if not results:
        print("❌ No results found")
        return
    
    print(f"✅ Found {len(results)} results:")
    print()
    
    # Connect to Neo4j to get episode details
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    
    book_sources = {}
    
    for i, result in enumerate(results):
        print(f"{i+1}. FACT: {result.fact}")
        
        # Get the episode UUID(s) for this result
        episode_ids = getattr(result, 'episodes', [])
        
        if episode_ids:
            with driver.session() as session:
                # Look up episode details
                for episode_id in episode_ids:
                    ep_result = session.run("""
                    MATCH (e:Episodic) 
                    WHERE e.uuid = $episode_id
                    RETURN e.name, e.source_description
                    """, episode_id=episode_id)
                    
                    for record in ep_result:
                        episode_name = record['e.name']
                        source_desc = record.get('e.source_description', '')
                        
                        # Extract book name from episode name
                        if episode_name:
                            if episode_name.startswith('Flames On The Water'):
                                book = 'Flames on the Water'
                            elif episode_name.startswith('Waking The Lion'):
                                book = 'Waking the Lion'
                            elif 'great' in episode_name.lower() and 'fire' in episode_name.lower():
                                book = 'The Great Fire (other book)'
                            else:
                                book = 'Unknown Book'
                            
                            print(f"   📚 SOURCE: {book}")
                            print(f"   📄 CHAPTER: {episode_name}")
                            if source_desc:
                                print(f"   📝 FILE: {source_desc}")
                            
                            # Track book usage
                            if book not in book_sources:
                                book_sources[book] = 0
                            book_sources[book] += 1
        
        print()
    
    # Summary by book
    if book_sources:
        print("📊 RESULTS BY BOOK:")
        print("-" * 30)
        for book, count in sorted(book_sources.items(), key=lambda x: x[1], reverse=True):
            print(f"   {book}: {count} facts")
    
    driver.close()

async def main():
    """Test various historical queries with source tracking"""
    
    queries = [
        "Ataturk Armenian population popularity",
        "Mustafa Kemal Armenian relations", 
        "Armenian evacuation Smyrna",
        "Asa Jennings Armenian refugees",
        "American relief Armenian population"
    ]
    
    for query in queries:
        await search_with_sources(query, 3)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())