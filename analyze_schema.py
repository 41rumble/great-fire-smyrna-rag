#!/usr/bin/env python3
"""
Analyze current Neo4j schema to determine migration needs
"""

from neo4j import GraphDatabase
import json

def analyze_current_schema():
    """Analyze current data structure"""
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    
    with driver.session(database="the-great-fire-db") as session:
        print("=== CURRENT NODE COUNTS ===")
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
        for record in result:
            print(f"{record['labels']}: {record['count']}")
        
        print("\n=== SAMPLE EPISODE PROPERTIES ===")
        result = session.run("MATCH (e:Episode) RETURN e LIMIT 1")
        for record in result:
            episode = dict(record['e'])
            for key, value in episode.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"{key}: {value[:100]}...")
                else:
                    print(f"{key}: {value}")
        
        print("\n=== RELATIONSHIP TYPES ===")
        result = session.run("MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count")
        for record in result:
            print(f"{record['rel_type']}: {record['count']}")
            
        print("\n=== SAMPLE RELATES_TO RELATIONSHIP ===")
        result = session.run("MATCH ()-[r:RELATES_TO]->() RETURN r LIMIT 1")
        for record in result:
            rel = dict(record['r'])
            for key, value in rel.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"{key}: {value[:100]}...")
                else:
                    print(f"{key}: {value}")
                    
        print("\n=== CHECKING FOR SOURCE INFORMATION ===")
        result = session.run("""
        MATCH (e:Episode) 
        WHERE e.filename IS NOT NULL 
        RETURN DISTINCT e.filename as filename
        LIMIT 10
        """)
        filenames = [record['filename'] for record in result]
        print("Current source files:", filenames)
        
        print("\n=== CHECKING FOR CHAPTER INFO ===")
        result = session.run("""
        MATCH (e:Episode) 
        WHERE e.chapter_title IS NOT NULL 
        RETURN DISTINCT e.chapter_title as chapter
        LIMIT 10
        """)
        chapters = [record['chapter'] for record in result]
        print("Current chapters:", chapters)
    
    driver.close()

if __name__ == "__main__":
    analyze_current_schema()