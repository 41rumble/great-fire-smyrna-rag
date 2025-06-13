#!/usr/bin/env python3
"""
Simple test to verify source tracking system
"""

from neo4j import GraphDatabase

def test_source_system():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    
    with driver.session(database="the-great-fire-db") as session:
        
        print("🔍 TESTING SOURCE TRACKING SYSTEM")
        print("=" * 40)
        
        # Test 1: Check Source nodes
        print("\n1. SOURCE NODES:")
        result = session.run("MATCH (s:Source) RETURN s.title, s.author, s.sourceId LIMIT 5")
        for record in result:
            print(f"   📚 {record['s.title']} by {record['s.author']} (ID: {record['s.sourceId']})")
        
        # Test 2: Check Chapter linkage
        print("\n2. CHAPTER LINKAGE:")
        result = session.run("""
        MATCH (s:Source)-[:HAS_CHAPTER]->(c:Chapter) 
        RETURN s.sourceId, count(c) as chapters 
        """)
        for record in result:
            print(f"   📖 {record['s.sourceId']}: {record['chapters']} chapters")
        
        # Test 3: Check Episode linkage  
        print("\n3. EPISODE LINKAGE:")
        result = session.run("""
        MATCH (e:Episode)-[:FROM_SOURCE]->(s:Source)
        RETURN s.sourceId, count(e) as episodes
        """)
        for record in result:
            print(f"   📄 {record['s.sourceId']}: {record['episodes']} episodes")
        
        # Test 4: Check Entity source tagging
        print("\n4. ENTITY SOURCE TAGGING:")
        result = session.run("""
        MATCH (e:Entity) 
        WHERE e.sourceId IS NOT NULL
        RETURN e.sourceId, count(e) as entities
        """)
        for record in result:
            print(f"   🏷️  {record['e.sourceId']}: {record['entities']} entities tagged")
        
        # Test 5: Sample entity with source
        print("\n5. SAMPLE ENTITY WITH SOURCE:")
        result = session.run("""
        MATCH (e:Entity) 
        WHERE e.sourceId IS NOT NULL 
        RETURN e.name, e.sourceId 
        LIMIT 3
        """)
        for record in result:
            print(f"   👤 {record['e.name']} (from: {record['e.sourceId']})")
        
        # Test 6: Relationship source tracking
        print("\n6. RELATIONSHIP SOURCE TRACKING:")
        result = session.run("""
        MATCH ()-[r:RELATES_TO]->()
        WHERE r.sourceId IS NOT NULL
        RETURN r.sourceId, count(r) as relationships
        """)
        for record in result:
            print(f"   🔗 {record['r.sourceId']}: {record['relationships']} relationships tagged")
    
    driver.close()
    print("\n✅ Source tracking system verification complete!")

if __name__ == "__main__":
    test_source_system()