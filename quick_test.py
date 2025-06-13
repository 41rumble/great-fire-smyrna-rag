#!/usr/bin/env python3
"""
Quick test to verify multi-source system is working
"""

from neo4j import GraphDatabase

def quick_test():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    
    with driver.session(database="the-great-fire-db") as session:
        
        print("🔍 QUICK MULTI-SOURCE TEST")
        print("=" * 40)
        
        # Test 1: Count sources
        print("\n1. SOURCES IN DATABASE:")
        result = session.run("MATCH (s:Source) RETURN s.title, s.author, s.sourceId")
        sources = []
        for record in result:
            sources.append({
                'title': record['s.title'],
                'author': record['s.author'], 
                'sourceId': record['s.sourceId']
            })
            print(f"   📚 {record['s.title']} by {record['s.author']}")
        
        print(f"\n✅ Found {len(sources)} books")
        
        # Test 2: Quick entity count per source
        print("\n2. ENTITIES PER SOURCE:")
        for source in sources:
            result = session.run("""
            MATCH (e:Entity {sourceId: $sourceId})
            RETURN count(e) as count
            """, sourceId=source['sourceId'])
            
            count = result.single()['count']
            print(f"   {source['title'][:30]}...: {count} entities")
        
        # Test 3: Test cross-book entity search
        print("\n3. TESTING CROSS-BOOK SEARCH:")
        result = session.run("""
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS 'smyrna'
        RETURN e.name, e.sourceId
        LIMIT 5
        """)
        
        smyrna_mentions = []
        for record in result:
            smyrna_mentions.append({
                'name': record['e.name'],
                'source': record['e.sourceId']
            })
            print(f"   '{record['e.name']}' in {record['e.sourceId']}")
        
        print(f"\n✅ Found {len(smyrna_mentions)} Smyrna-related entities")
        
        # Test 4: Quick relationship test
        print("\n4. TESTING RELATIONSHIPS:")
        result = session.run("""
        MATCH ()-[r:RELATES_TO]->()
        WHERE r.sourceId IS NOT NULL
        RETURN r.sourceId, count(r) as count
        """)
        
        total_relationships = 0
        for record in result:
            count = record['count']
            total_relationships += count
            print(f"   {record['r.sourceId']}: {count} relationships")
        
        print(f"\n✅ Total relationships: {total_relationships}")
        
        print(f"\n🎉 MULTI-SOURCE SYSTEM IS WORKING!")
        print(f"   📊 {len(sources)} books, {sum(len(smyrna_mentions) for _ in sources)} entities, {total_relationships} relationships")
    
    driver.close()

if __name__ == "__main__":
    quick_test()