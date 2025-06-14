#!/usr/bin/env python3
"""
Show people entities from the knowledge graph
"""

from neo4j import GraphDatabase

def show_people():
    """Find and display likely people entities"""
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
    
    with driver.session() as session:
        # Query for entities that look like people names
        query = """
        MATCH (n:Entity)
        WHERE 
            // Names with titles
            n.name =~ '(?i).*(Admiral|Captain|General|Colonel|Dr|President|Secretary|Ambassador|Minister|Commander|Lieutenant|Major|Reverend|Father|Sister|Pope|King|Queen|Prince|Princess|Duke|Earl|Lord|Lady|Sir|Dame).*'
            OR 
            // First + Last name patterns
            (n.name =~ '.*[A-Z][a-z]+ [A-Z][a-z]+.*' 
             AND NOT n.name =~ '.*(Street|Avenue|Road|Company|Co\\.|Inc|Ltd|Hotel|Hospital|School|University|Theater|Theatre|Church|Mosque|Bank|Store|Market|Station|Port|Harbor|Bay|Sea|River|Mountain|Hill|Valley|Island|Bridge|Building|Palace|Castle|House|Office|Department|Ministry|Embassy|Consulate|Committee|Commission|Association|Organization|Society|League|Union|Party|Government|Army|Navy|Air Force|Regiment|Battalion|Division|Corps).*')
        RETURN n.name
        ORDER BY n.name
        """
        
        result = session.run(query)
        people = [record["n.name"] for record in result]
        
        print(f"🧑 PEOPLE ENTITIES ({len(people)} found)")
        print("=" * 50)
        
        # Group by first letter for easier browsing
        current_letter = ""
        for person in people:
            first_letter = person[0].upper()
            if first_letter != current_letter:
                current_letter = first_letter
                print(f"\n{current_letter}:")
            print(f"  - {person}")
        
        # Show some relationships for a few key people
        print(f"\n🔗 SAMPLE RELATIONSHIPS")
        print("=" * 30)
        
        key_people = ["Admiral Bristol", "Asa Jennings", "Mustafa Kemal", "Constantine"]
        
        for person in key_people:
            query = """
            MATCH (p:Entity {name: $person})-[r]-(other:Entity)
            WHERE r.fact IS NOT NULL
            RETURN r.fact
            LIMIT 3
            """
            result = session.run(query, person=person)
            facts = [record["r.fact"] for record in result]
            
            if facts:
                print(f"\n{person}:")
                for fact in facts:
                    print(f"  • {fact}")
    
    driver.close()

if __name__ == "__main__":
    show_people()