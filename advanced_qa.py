import os
import requests
import json
from neo4j import GraphDatabase

class AdvancedHistoricalQA:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
    
    def find_related_content(self, entities):
        """Find all content related to specific entities and their relationships"""
        with self.driver.session(database="the-great-fire-db") as session:
            all_content = []
            
            for entity in entities:
                # Find episodes that mention this entity
                entity_query = """
                MATCH (ent:Entity {name: $entity})<-[:MENTIONS]-(ep:Episode)
                RETURN ep.content AS content, ep.name AS episode_name
                """
                result = session.run(entity_query, {"entity": entity})
                for record in result:
                    all_content.append({
                        "content": record["content"],
                        "episode": record["episode_name"],
                        "entity": entity
                    })
            
            return all_content
    
    def extract_key_entities(self, question):
        """Extract key entities from the question using LLM"""
        url = "http://localhost:11434/v1/chat/completions"
        
        prompt = f"""From this question about the Great Fire of Smyrna, extract the key people, places, and concepts that I should search for:

Question: {question}

Return only a JSON list of the most important search terms/entities. Focus on proper names, places, and key concepts.
Example: ["Atatürk", "Jennings", "Smyrna", "relationship"]"""
        
        data = {
            "model": "mistral-small3.1:latest", 
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                # Extract JSON
                if '[' in content and ']' in content:
                    start = content.find('[')
                    end = content.rfind(']') + 1
                    json_str = content[start:end]
                    return json.loads(json_str)
            return []
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return []
    
    def comprehensive_search(self, question):
        """Do a comprehensive search for all relevant content"""
        # Extract entities from question
        entities = self.extract_key_entities(question)
        print(f"Searching for: {entities}")
        
        all_relevant_content = []
        
        with self.driver.session(database="the-great-fire-db") as session:
            # Search by entities
            for entity in entities:
                entity_query = """
                MATCH (ent:Entity)<-[:MENTIONS]-(ep:Episode)
                WHERE toLower(ent.name) CONTAINS toLower($entity)
                RETURN ep.content AS content, ep.name AS episode_name, ent.name AS entity_name
                """
                result = session.run(entity_query, {"entity": entity})
                for record in result:
                    all_relevant_content.append({
                        "content": record["content"],
                        "episode": record["episode_name"],
                        "relevance": f"Mentions {record['entity_name']}"
                    })
            
            # Also do keyword search in content
            for entity in entities:
                content_query = """
                MATCH (ep:Episode)
                WHERE toLower(ep.content) CONTAINS toLower($term)
                RETURN ep.content AS content, ep.name AS episode_name
                """
                result = session.run(content_query, {"term": entity})
                for record in result:
                    content = record["content"]
                    # Avoid duplicates
                    if not any(existing["content"] == content for existing in all_relevant_content):
                        all_relevant_content.append({
                            "content": content,
                            "episode": record["episode_name"],
                            "relevance": f"Contains '{entity}'"
                        })
        
        return all_relevant_content
    
    def answer_question(self, question):
        """Provide a comprehensive, conversational answer"""
        print("🔍 Searching knowledge base...")
        relevant_content = self.comprehensive_search(question)
        
        if not relevant_content:
            return "I couldn't find relevant information in the knowledge base to answer your question."
        
        print(f"📚 Found {len(relevant_content)} relevant sources")
        
        # Prepare comprehensive context
        context_parts = []
        for i, item in enumerate(relevant_content[:6]):  # Use top 6 most relevant
            context_parts.append(f"Source {i+1} ({item['episode']}):\n{item['content']}\n")
        
        full_context = "\n---\n".join(context_parts)
        
        # Enhanced prompt for better answers
        prompt = f"""You are having a conversation with someone interested in the Great Fire of Smyrna. They asked: "{question}"

Here's what you know from historical documents:

{full_context}

Answer their question in a natural, conversational way. Don't use bullet points or say "the narrative shows" or "the sources indicate." Just tell them what happened as if you're sharing a fascinating historical story. Focus on the human relationships, motivations, and drama of the events. Be specific about names, dates, and details when you have them.

If the question asks about relationships between people, explain how they met, what they thought of each other, how they worked together or against each other, and what the consequences were."""
        
        url = "http://localhost:11434/v1/chat/completions"
        data = {
            "model": "mistral-small3.1:latest",
            "messages": [
                {"role": "system", "content": "You are a knowledgeable historian who speaks naturally and conversationally. You never use formal academic language, bullet points, or phrases like 'the narrative indicates.' You tell historical stories as if you're talking to a friend over coffee."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1200,
            "temperature": 0.8
        }
        
        try:
            print("🤔 Analyzing and synthesizing information...")
            response = requests.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                
                # Add source information
                sources_used = [item['episode'] for item in relevant_content[:6]]
                answer += f"\n\n📖 Sources consulted: {', '.join(set(sources_used))}"
                
                return answer
            else:
                return f"Error generating answer: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    def close(self):
        self.driver.close()

def main():
    qa_system = AdvancedHistoricalQA()
    
    print("🔥 Advanced Great Fire of Smyrna Q&A System")
    print("=" * 50)
    print("Ask detailed questions about relationships, motivations, and historical context.")
    print("\nExample questions:")
    print("• What was the nature of Atatürk and Jennings' relationship?")
    print("• How did the international community respond to the crisis?")
    print("• What were the long-term consequences of the Great Fire?")
    print("• What role did American missionaries play in the events?")
    
    while True:
        question = input("\n❓ Your question (or 'quit' to exit): ").strip()
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if len(question) < 10:
            print("Please ask a more detailed question for better results.")
            continue
            
        print()
        answer = qa_system.answer_question(question)
        print("💡 Answer:")
        print("-" * 50)
        print(answer)
        print("-" * 50)
    
    qa_system.close()

if __name__ == "__main__":
    main()