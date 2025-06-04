from neo4j import GraphDatabase

def clear_database():
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "Sk1pper(())")
    )
    
    with driver.session(database="the-great-fire-db") as session:
        # Delete all nodes and relationships
        session.run("MATCH (n) DETACH DELETE n")
        print("🧹 Database cleared!")
    
    driver.close()

if __name__ == "__main__":
    clear_database()