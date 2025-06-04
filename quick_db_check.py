from neo4j import GraphDatabase

def quick_check():
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "Sk1pper(())")
    )
    
    with driver.session(database="the-great-fire-db") as session:
        # Check for Graphiti data
        result = session.run("MATCH (e:Episodic) RETURN count(e) as count")
        episodic_count = result.single()["count"]
        
        result = session.run("MATCH (e:Entity) RETURN count(e) as count")
        entity_count = result.single()["count"]
        
        result = session.run("MATCH (e:Episode) RETURN count(e) as count")
        episode_count = result.single()["count"]
        
        print(f"Current database content:")
        print(f"  Episodic nodes: {episodic_count}")
        print(f"  Entity nodes: {entity_count}")
        print(f"  Episode nodes: {episode_count}")
        
        if episodic_count == 0 and entity_count == 0:
            print("✅ Database is clean and ready for fresh Graphiti ingestion")
        else:
            print("⚠️  Database contains existing data")
    
    driver.close()

if __name__ == "__main__":
    quick_check()