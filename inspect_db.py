import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def inspect_database():
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    
    with driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:
        # Get all labels
        print("=== DATABASE LABELS ===")
        result = session.run("CALL db.labels()")
        labels = [record["label"] for record in result]
        print(f"Labels: {labels}")
        
        # Count nodes by label
        print("\n=== NODE COUNTS ===")
        for label in labels:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"{label}: {count} nodes")
        
        # Sample Episode nodes
        print("\n=== SAMPLE EPISODE NODES ===")
        result = session.run("MATCH (e:Episode) RETURN e LIMIT 3")
        for i, record in enumerate(result):
            episode = dict(record["e"])
            print(f"Episode {i+1}:")
            for key, value in episode.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: {value[:100]}...")
                else:
                    print(f"  {key}: {value}")
            print()
        
        # Sample Entity nodes
        print("\n=== SAMPLE ENTITY NODES ===")
        result = session.run("MATCH (e:Entity) RETURN e LIMIT 5")
        for i, record in enumerate(result):
            entity = dict(record["e"])
            print(f"Entity {i+1}: {entity}")
        
        # Check relationships
        print("\n=== RELATIONSHIPS ===")
        result = session.run("MATCH ()-[r]->() RETURN type(r) as rel_type, count(*) as count")
        total_rels = 0
        for record in result:
            print(f"{record['rel_type']}: {record['count']} relationships")
            total_rels += record['count']
        print(f"Total relationships: {total_rels}")
        
        # Show some example relationships
        print("\n=== SAMPLE RELATIONSHIPS ===")
        result = session.run("MATCH (ep:Episode)-[r:MENTIONS]->(ent:Entity) RETURN ep.name, ent.name, ent.type LIMIT 5")
        for record in result:
            print(f"'{record['ep.name']}' mentions {record['ent.type']}: '{record['ent.name']}')")
    
    driver.close()

if __name__ == "__main__":
    inspect_database()