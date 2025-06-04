import os
import requests
import json
from neo4j import GraphDatabase

class AdvancedHistoricalQAv2:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        self.ollama_url = "http://localhost:11434/v1/chat/completions"
        self.model = "mistral-small3.1:latest"
    
    def call_ollama(self, prompt: str, max_tokens: int = 1200) -> str:
        """Call Ollama with a prompt"""
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a knowledgeable historian providing detailed analysis of the Great Fire of Smyrna. Write comprehensive, insightful responses that synthesize information from multiple sources. Avoid repetitive phrases and focus on substantive historical insights."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.4,
            "top_p": 0.95,
            "frequency_penalty": 1.0,  # Higher to prevent repetition
            "presence_penalty": 0.6,   # Higher to encourage new topics
            "repeat_penalty": 1.1      # Additional repetition prevention
        }
        
        try:
            response = requests.post(self.ollama_url, json=data)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    def find_relevant_entities(self, question: str):
        """Find entities relevant to the question"""
        with self.driver.session(database="the-great-fire-db") as session:
            # Extract key terms from question
            words = [w.lower().strip('.,?!') for w in question.split() if len(w) > 3]
            
            relevant_entities = []
            
            for word in words:
                # Search entity names
                entity_query = """
                MATCH (e:Entity)
                WHERE toLower(e.name) CONTAINS $word
                RETURN e.name AS name, e.category AS category, e.significance AS significance
                LIMIT 3
                """
                result = session.run(entity_query, {"word": word})
                for record in result:
                    relevant_entities.append({
                        "name": record["name"],
                        "category": record["category"],
                        "significance": record["significance"]
                    })
            
            return relevant_entities
    
    def get_entity_relationships(self, entity_names: list):
        """Get relationships for specific entities"""
        with self.driver.session(database="the-great-fire-db") as session:
            relationships = []
            
            for entity_name in entity_names:
                # Find outgoing relationships
                out_query = """
                MATCH (a:Entity {name: $name})-[r:RELATES_TO]->(b:Entity)
                RETURN a.name AS from_entity, b.name AS to_entity, r.type AS relationship, r.context AS context
                LIMIT 5
                """
                result = session.run(out_query, {"name": entity_name})
                for record in result:
                    relationships.append({
                        "from": record["from_entity"],
                        "to": record["to_entity"],
                        "relationship": record["relationship"],
                        "context": record["context"]
                    })
                
                # Find incoming relationships
                in_query = """
                MATCH (a:Entity)-[r:RELATES_TO]->(b:Entity {name: $name})
                RETURN a.name AS from_entity, b.name AS to_entity, r.type AS relationship, r.context AS context
                LIMIT 5
                """
                result = session.run(in_query, {"name": entity_name})
                for record in result:
                    relationships.append({
                        "from": record["from_entity"],
                        "to": record["to_entity"],
                        "relationship": record["relationship"],
                        "context": record["context"]
                    })
            
            return relationships
    
    def get_episodes_mentioning_entities(self, entity_names: list):
        """Get episodes that mention specific entities"""
        with self.driver.session(database="the-great-fire-db") as session:
            episodes = []
            
            for entity_name in entity_names:
                episode_query = """
                MATCH (ep:Episode)-[:MENTIONS]->(e:Entity {name: $name})
                RETURN ep.name AS episode_name, ep.content AS content, ep.chapter_title AS chapter
                LIMIT 3
                """
                result = session.run(episode_query, {"name": entity_name})
                for record in result:
                    episodes.append({
                        "name": record["episode_name"],
                        "content": record["content"][:1000],  # Truncate for context
                        "chapter": record["chapter"]
                    })
            
            return episodes
    
    def comprehensive_search(self, question: str):
        """Do comprehensive search across entities, relationships, and episodes"""
        print(f"🔍 Analyzing question: '{question}'")
        
        # Find relevant entities
        entities = self.find_relevant_entities(question)
        entity_names = [e["name"] for e in entities[:5]]  # Top 5 entities
        
        if not entity_names:
            # Fallback to content search
            with self.driver.session(database="the-great-fire-db") as session:
                words = [w.lower() for w in question.split() if len(w) > 3]
                episodes = []
                
                for word in words[:3]:  # Search top 3 keywords
                    content_query = """
                    MATCH (ep:Episode)
                    WHERE toLower(ep.content) CONTAINS $word
                    RETURN ep.name AS name, ep.content AS content, ep.chapter_title AS chapter
                    LIMIT 2
                    """
                    result = session.run(content_query, {"word": word})
                    for record in result:
                        episodes.append({
                            "name": record["name"],
                            "content": record["content"][:1000],
                            "chapter": record["chapter"]
                        })
                
                return {"entities": [], "relationships": [], "episodes": episodes}
        
        print(f"📍 Found relevant entities: {[e['name'] for e in entities]}")
        
        # Get relationships between entities
        relationships = self.get_entity_relationships(entity_names)
        print(f"🔗 Found {len(relationships)} relationships")
        
        # Get episodes mentioning these entities
        episodes = self.get_episodes_mentioning_entities(entity_names)
        print(f"📚 Found {len(episodes)} relevant episodes")
        
        return {
            "entities": entities,
            "relationships": relationships,
            "episodes": episodes
        }
    
    def answer_question(self, question: str):
        """Answer question using comprehensive knowledge graph"""
        search_results = self.comprehensive_search(question)
        
        if not any(search_results.values()):
            return "I couldn't find relevant information in the knowledge base to answer your question."
        
        # Build comprehensive context for deep insights
        context_parts = []
        
        # Add detailed entity information
        if search_results["entities"]:
            entities_info = []
            for entity in search_results["entities"][:8]:  # More entities
                significance = entity.get('significance', 'Historical figure/location')
                entities_info.append(f"• {entity['name']} ({entity['category']}): {significance}")
            context_parts.append("KEY PEOPLE AND PLACES:\n" + "\n".join(entities_info))
        
        # Add relationship information for deep analysis
        if search_results["relationships"]:
            relationships_info = []
            for rel in search_results["relationships"][:12]:  # More relationships
                context_detail = rel.get('context', 'Connected in historical events')
                relationships_info.append(f"• {rel['from']} → {rel['relationship']} → {rel['to']}: {context_detail}")
            context_parts.append("RELATIONSHIPS AND CONNECTIONS:\n" + "\n".join(relationships_info))
        
        # Add full episode content for rich context
        if search_results["episodes"]:
            episode_info = []
            for i, ep in enumerate(search_results["episodes"][:5]):  # More episodes
                chapter = ep.get('chapter', 'Historical Account')
                content = ep['content'][:1200] if len(ep['content']) > 1200 else ep['content']  # Longer content
                episode_info.append(f"SOURCE {i+1} - {chapter}:\n{content}")
            context_parts.append("HISTORICAL ACCOUNTS:\n" + "\n\n".join(episode_info))
        
        full_context = "\n\n" + "="*60 + "\n\n".join(context_parts) + "\n" + "="*60
        
        # Create comprehensive prompt for deep analysis
        prompt = f"""You are analyzing historical documents about the Great Fire of Smyrna (1922). A researcher has asked: "{question}"

{full_context}

Based on this comprehensive historical information, provide a detailed, insightful answer that:

1. Synthesizes information from multiple sources
2. Explains the relationships and connections between people, events, and places
3. Provides historical context and significance
4. Uses specific names, dates, and details
5. Addresses the researcher's question thoroughly

Write 3-4 well-developed paragraphs that demonstrate deep historical understanding. Focus on the human stories, motivations, and broader implications of the events."""
        
        print("🤔 Generating comprehensive answer...")
        answer = self.call_ollama(prompt, 1000)  # Back to longer responses
        
        # Add source information
        sources = list(set([ep["chapter"] for ep in search_results["episodes"] if ep.get("chapter")]))
        if sources:
            answer += f"\n\n📖 Based on information from: {', '.join(sources[:5])}"
        
        return answer
    
    def close(self):
        self.driver.close()

def main():
    qa_system = AdvancedHistoricalQAv2()
    
    print("🔥 Advanced Great Fire of Smyrna Knowledge Graph Q&A")
    print("=" * 60)
    print("Ask detailed questions about relationships, events, and historical context.")
    print("\nExample questions:")
    print("• What was the nature of Atatürk and Jennings' relationship?")
    print("• How did the international community respond to the crisis?")
    print("• What role did American missionaries play?")
    print("• Who were the key military commanders involved?")
    print("• How did refugees escape from Smyrna?")
    
    while True:
        question = input("\n❓ Your question (or 'quit' to exit): ").strip()
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if len(question) < 5:
            print("Please ask a more detailed question.")
            continue
            
        print()
        answer = qa_system.answer_question(question)
        print("💡 Answer:")
        print("-" * 60)
        print(answer)
        print("-" * 60)
    
    qa_system.close()

if __name__ == "__main__":
    main()