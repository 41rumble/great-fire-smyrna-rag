#!/usr/bin/env python3
"""
Check what embeddings are actually stored in the database
"""

from neo4j import GraphDatabase

def check_stored_embeddings():
    """Check embedding dimensions in Neo4j"""
    
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "Sk1pper(())")
    )
    
    with driver.session(database="the-great-fire-db") as session:
        # Check for any nodes with embeddings
        result = session.run("""
        MATCH (n)
        WHERE n.embedding IS NOT NULL
        RETURN labels(n) as labels, n.name as name, size(n.embedding) as embedding_size
        LIMIT 10
        """)
        
        print("🔍 CHECKING STORED EMBEDDINGS")
        print("=" * 50)
        
        for record in result:
            print(f"Labels: {record['labels']}")
            print(f"Name: {record['name']}")
            print(f"Embedding size: {record['embedding_size']}")
            print("-" * 30)
    
    driver.close()

if __name__ == "__main__":
    check_stored_embeddings()