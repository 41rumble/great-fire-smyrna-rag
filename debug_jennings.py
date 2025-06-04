#!/usr/bin/env python3
"""
Debug script to check what data we actually have about Asa Jennings
"""

import os
import sys

try:
    from neo4j import GraphDatabase
except ImportError:
    print("Installing neo4j driver...")
    os.system("pip install neo4j")
    from neo4j import GraphDatabase

def debug_jennings_data():
    """Check all data about Asa Jennings in the database"""
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    
    with driver.session(database="the-great-fire-db") as session:
        print("🔍 DEBUGGING ASA JENNINGS DATA")
        print("=" * 60)
        
        # 1. Check Character nodes
        print("\n1. CHARACTER NODES:")
        char_query = """
        MATCH (c:Character)
        WHERE toLower(c.name) CONTAINS 'jennings'
        RETURN c
        """
        result = session.run(char_query)
        for record in result:
            char = record["c"]
            print(f"\nCharacter Node Found:")
            for key, value in char.items():
                print(f"  {key}: {value}")
        
        # 2. Check Episodes mentioning Jennings
        print("\n\n2. EPISODES MENTIONING JENNINGS:")
        episode_query = """
        MATCH (e:Episode)
        WHERE toLower(e.content) CONTAINS 'jennings'
        RETURN e.name, substring(e.content, 0, 500) as content_preview
        LIMIT 5
        """
        result = session.run(episode_query)
        for record in result:
            print(f"\nEpisode: {record['name']}")
            print(f"Content preview: {record['content_preview']}...")
            
        # 3. Check relationships
        print("\n\n3. JENNINGS RELATIONSHIPS:")
        rel_query = """
        MATCH (c:Character)-[r]-(other)
        WHERE toLower(c.name) CONTAINS 'jennings'
        RETURN c.name as jennings_name, type(r) as relationship_type, 
               other.name as other_name, r.narrative_context as context
        LIMIT 10
        """
        result = session.run(rel_query)
        for record in result:
            print(f"\n{record['jennings_name']} --[{record['relationship_type']}]--> {record['other_name']}")
            if record['context']:
                print(f"  Context: {record['context']}")
        
        # 4. Check if there are multiple Jennings characters
        print("\n\n4. ALL JENNINGS MENTIONS:")
        all_jennings_query = """
        MATCH (n)
        WHERE toLower(n.name) CONTAINS 'jennings'
        RETURN labels(n) as node_type, n.name as name, n.role as role
        """
        result = session.run(all_jennings_query)
        for record in result:
            print(f"{record['node_type']}: {record['name']} - Role: {record['role']}")
        
        # 5. Search for "naval" or "officer" in content
        print("\n\n5. NAVAL/OFFICER MENTIONS:")
        naval_query = """
        MATCH (e:Episode)
        WHERE toLower(e.content) CONTAINS 'jennings' 
        AND (toLower(e.content) CONTAINS 'naval' OR toLower(e.content) CONTAINS 'officer')
        RETURN e.name, substring(e.content, 0, 300) as snippet
        LIMIT 3
        """
        result = session.run(naval_query)
        for record in result:
            print(f"\nEpisode: {record['name']}")
            print(f"Snippet: {record['snippet']}...")
    
    driver.close()
    print("\n" + "=" * 60)
    print("Debug complete!")

if __name__ == "__main__":
    debug_jennings_data()