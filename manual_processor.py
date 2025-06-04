import os
import glob
import requests
import json
from pathlib import Path
from neo4j import GraphDatabase
from datetime import datetime

class ManualTextProcessor:
    def __init__(self, text_directory="./text_files"):
        self.text_directory = text_directory
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
    
    def extract_entities_with_ollama(self, text):
        """Use Ollama to extract entities from text"""
        url = "http://localhost:11434/v1/chat/completions"
        
        prompt = f"""Extract the key people, places, dates, and events from this historical text. 
Return a JSON list of entities with name and type (person, place, date, event).

Text: {text[:1000]}"""
        
        data = {
            "model": "mistral-small3.1:latest",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                # Try to extract JSON from the response
                if '[' in content and ']' in content:
                    start = content.find('[')
                    end = content.rfind(']') + 1
                    json_str = content[start:end]
                    return json.loads(json_str)
            return []
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return []
    
    def store_episode(self, filename, content, entities):
        """Store episode and entities in Neo4j"""
        with self.driver.session(database="the-great-fire-db") as session:
            # Create episode node
            episode_query = """
            CREATE (e:Episode {
                name: $name,
                content: $content,
                filename: $filename,
                created_at: datetime()
            })
            RETURN e
            """
            
            session.run(episode_query, {
                "name": f"Chapter: {filename}",
                "content": content,
                "filename": filename
            })
            
            # Create entity nodes and relationships
            for entity in entities:
                if isinstance(entity, dict) and 'name' in entity:
                    entity_query = """
                    MERGE (ent:Entity {name: $name})
                    SET ent.type = $type
                    WITH ent
                    MATCH (ep:Episode {filename: $filename})
                    MERGE (ep)-[:MENTIONS]->(ent)
                    """
                    
                    session.run(entity_query, {
                        "name": entity.get('name', ''),
                        "type": entity.get('type', 'unknown'),
                        "filename": filename
                    })
    
    def process_all_chapters(self):
        """Process all text files"""
        txt_files = glob.glob(os.path.join(self.text_directory, "*.txt"))
        
        if not txt_files:
            print(f"No .txt files found in {self.text_directory}")
            return
            
        print(f"Found {len(txt_files)} text files to process...")
        
        for file_path in sorted(txt_files):
            filename = Path(file_path).name
            print(f"\nProcessing: {filename}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                if len(content.strip()) < 50:
                    print(f"Skipping {filename} - too short")
                    continue
                
                # Extract entities
                print("  Extracting entities...")
                entities = self.extract_entities_with_ollama(content)
                print(f"  Found {len(entities)} entities")
                
                # Store in Neo4j
                print("  Storing in database...")
                self.store_episode(filename, content, entities)
                print(f"  ✓ Successfully processed {filename}")
                
            except Exception as e:
                print(f"  ✗ Error processing {filename}: {e}")
    
    def search(self, query):
        """Search the stored content"""
        with self.driver.session(database="the-great-fire-db") as session:
            # Search in episode content
            search_query = """
            MATCH (e:Episode)
            WHERE toLower(e.content) CONTAINS toLower($query)
            RETURN e.name AS name, e.content AS content
            LIMIT 3
            """
            
            result = session.run(search_query, {"query": query})
            episodes = []
            for record in result:
                content = record["content"]
                episodes.append({
                    "name": record["name"],
                    "content": content[:1500] + "..." if len(content) > 1500 else content
                })
            
            # Search entities
            entity_query = """
            MATCH (ent:Entity)
            WHERE toLower(ent.name) CONTAINS toLower($query)
            RETURN ent.name AS name, ent.type AS type
            LIMIT 5
            """
            
            result = session.run(entity_query, {"query": query})
            entities = [{"name": record["name"], "type": record["type"]} for record in result]
            
            return {"episodes": episodes, "entities": entities}
    
    def answer_question(self, question):
        """Use LLM to answer questions based on retrieved content"""
        # First, do a broad search for relevant content
        search_terms = question.lower().split()
        all_content = []
        
        with self.driver.session(database="the-great-fire-db") as session:
            for term in search_terms:
                if len(term) > 3:  # Skip short words
                    search_query = """
                    MATCH (e:Episode)
                    WHERE toLower(e.content) CONTAINS toLower($term)
                    RETURN e.content AS content
                    LIMIT 2
                    """
                    result = session.run(search_query, {"term": term})
                    for record in result:
                        content = record["content"]
                        if content not in all_content:
                            all_content.append(content[:1000])
        
        if not all_content:
            return "I couldn't find relevant information to answer your question."
        
        # Combine relevant content
        context = "\n\n".join(all_content[:3])  # Use top 3 most relevant pieces
        
        # Use Ollama to answer the question
        url = "http://localhost:11434/v1/chat/completions"
        
        prompt = f"""Based on the following historical text about the Great Fire of Smyrna, please answer this question: {question}

Historical Context:
{context}

Please provide a detailed answer based only on the information provided above. If the information is not sufficient to answer the question, say so."""
        
        data = {
            "model": "mistral-small3.1:latest",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error getting answer: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    def close(self):
        self.driver.close()

if __name__ == "__main__":
    text_dir = input("Enter path to your text files directory (or press Enter for './text_files'): ").strip()
    if not text_dir:
        text_dir = "./text_files"
    
    processor = ManualTextProcessor(text_dir)
    
    print("Starting manual processing...")
    processor.process_all_chapters()
    
    print("\n" + "="*50)
    print("Processing complete! You can now query your knowledge base.")
    
    # Interactive querying
    print("\nYou can now ask questions about the Great Fire of Smyrna!")
    print("Examples:")
    print("- Who was Asa Jennings?")
    print("- What caused the Great Fire?")
    print("- When did the fire happen?")
    print("- What role did Turkey play?")
    
    while True:
        query = input("\nAsk a question (or 'quit' to exit): ").strip()
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if '?' in query or query.lower().startswith(('who', 'what', 'when', 'where', 'why', 'how')):
            # This looks like a question - use LLM to answer
            print("\nThinking...")
            answer = processor.answer_question(query)
            print(f"\nAnswer: {answer}")
        else:
            # This looks like a keyword search
            result = processor.search(query)
            print(f"\nEntities found: {result['entities']}")
            print(f"\nEpisodes found: {len(result['episodes'])}")
            for episode in result['episodes']:
                print(f"- {episode['name']}: {episode['content']}")
    
    processor.close()