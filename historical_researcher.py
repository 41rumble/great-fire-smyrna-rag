import os
from dotenv import load_dotenv

load_dotenv()

# Override embedding model before importing Graphiti
os.environ["OPENAI_EMBEDDING_MODEL"] = "nomic-embed-text:latest"

from graphiti_core import Graphiti
import requests
import json

class HistoricalResearcher:
    def __init__(self):        
        # Initialize Graphiti with basic Neo4j connection
        self.graphiti = Graphiti(
            uri=os.getenv("NEO4J_URI"),
            user=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD")
        )
    
    async def process_historical_text(self, text, context=""):
        """Process historical text and extract relationships"""
        try:
            from datetime import datetime
            result = await self.graphiti.add_episode(
                name=f"Historical Text Analysis",
                episode_body=text,
                source_description=context,
                reference_time=datetime.now()
            )
            return result
        except Exception as e:
            print(f"Error processing text: {e}")
            return None
    
    def search_and_enrich(self, topic, historical_context=""):
        """Search for additional information and add to knowledge base"""
        # This would integrate with web search APIs
        # For now, just process the topic as additional context
        enrichment_text = f"Research topic: {topic} in historical context: {historical_context}"
        return self.process_historical_text(enrichment_text, f"Web search enrichment for {topic}")
    
    async def query_knowledge_base(self, query):
        """Query the built knowledge base using manual Neo4j query"""
        try:
            # For now, let's do a simple Neo4j query to see what's in the database
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI"),
                auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
            )
            
            with driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:
                # Check Episode nodes first (these likely contain the text content)
                episode_query = """
                MATCH (e:Episode)
                RETURN keys(e) AS properties, e
                LIMIT 1
                """
                result = session.run(episode_query)
                episode_properties = []
                for record in result:
                    episode_properties = record['properties']
                    print(f"Episode properties: {episode_properties}")
                    break
                
                # Check Entity nodes
                entity_query = """
                MATCH (e:Entity)
                RETURN keys(e) AS properties, e
                LIMIT 1
                """
                result = session.run(entity_query)
                entity_properties = []
                for record in result:
                    entity_properties = record['properties']
                    print(f"Entity properties: {entity_properties}")
                    break
                
                # Search in Episode content (most likely to contain the text)
                if episode_properties:
                    # Try different possible content properties
                    content_props = ['episode_body', 'content', 'body', 'text']
                    for prop in content_props:
                        if prop in episode_properties:
                            print(f"Searching in Episode.{prop}")
                            search_query = f"""
                            MATCH (e:Episode)
                            WHERE toLower(e.{prop}) CONTAINS toLower($query)
                            RETURN e.{prop} AS content, e.name AS name
                            LIMIT 3
                            """
                            result = session.run(search_query, {"query": query})
                            records = []
                            for record in result:
                                content = record["content"]
                                records.append({
                                    "content": content[:500] + "..." if len(str(content)) > 500 else str(content),
                                    "name": record["name"]
                                })
                            if records:
                                driver.close()
                                return records
                
                # Search in Entity names if no Episode content found
                if entity_properties and 'name' in entity_properties:
                    entity_search_query = """
                    MATCH (e:Entity)
                    WHERE toLower(e.name) CONTAINS toLower($query)
                    RETURN e.name AS entity_name, e
                    LIMIT 5
                    """
                    result = session.run(entity_search_query, {"query": query})
                    records = []
                    for record in result:
                        records.append({
                            "entity_name": record["entity_name"],
                            "properties": dict(record["e"])
                        })
                    if records:
                        driver.close()
                        return records
                
                driver.close()
                return "No relevant information found. Try a different search term."
                
        except Exception as e:
            print(f"Error querying knowledge base: {e}")
            return None
    
    def get_relationships(self, entity_name):
        """Get relationships for a specific historical entity"""
        try:
            result = self.graphiti.get_entity_relationships(entity_name)
            return result
        except Exception as e:
            print(f"Error getting relationships: {e}")
            return None

if __name__ == "__main__":
    researcher = HistoricalResearcher()
    
    # Example historical text
    sample_text = """
    In 1066, William the Conqueror invaded England, defeating King Harold II at the Battle of Hastings.
    This Norman Conquest fundamentally changed English society, introducing Norman administrative systems
    and French cultural influences that would shape England for centuries.
    """
    
    print("Processing historical text...")
    result = researcher.process_historical_text(sample_text, "Norman Conquest of England")
    print(f"Processing result: {result}")
    
    # Query the knowledge base
    print("\nQuerying knowledge base...")
    query_result = researcher.query_knowledge_base("What happened in 1066?")
    print(f"Query result: {query_result}")