import requests
from neo4j import GraphDatabase

def test_ollama():
    """Test basic Ollama functionality"""
    url = "http://localhost:11434/v1/chat/completions"
    
    data = {
        "model": "mistral-small3.1:latest",
        "messages": [
            {"role": "user", "content": "What is 2 + 2? Answer in one sentence."}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print(f"✅ Ollama test: {answer}")
            return True
        else:
            print(f"❌ Ollama error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama connection error: {e}")
        return False

def test_database():
    """Test basic database connectivity"""
    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        
        with driver.session(database="the-great-fire-db") as session:
            result = session.run("MATCH (e:Episode) RETURN count(e) as count")
            episode_count = result.single()["count"]
            
            result = session.run("MATCH (e:Entity) RETURN count(e) as count")  
            entity_count = result.single()["count"]
            
            print(f"✅ Database test: {episode_count} episodes, {entity_count} entities")
            
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def simple_search_test():
    """Test simple database search"""
    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        
        with driver.session(database="the-great-fire-db") as session:
            # Simple content search
            result = session.run("""
                MATCH (e:Episode) 
                WHERE toLower(e.content) CONTAINS 'jennings'
                RETURN e.name AS name, substring(e.content, 0, 200) AS excerpt
                LIMIT 2
            """)
            
            print("📚 Sample episodes mentioning 'Jennings':")
            for record in result:
                print(f"  - {record['name']}")
                print(f"    {record['excerpt']}...")
                print()
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False

def simple_qa_test():
    """Test simple Q&A without complex processing"""
    if not test_ollama():
        return
    
    if not test_database():
        return
        
    if not simple_search_test():
        return
    
    # Simple Q&A test
    question = "Who was Jennings?"
    
    # Get simple context
    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Sk1pper(())")
        )
        
        with driver.session(database="the-great-fire-db") as session:
            result = session.run("""
                MATCH (e:Episode) 
                WHERE toLower(e.content) CONTAINS 'jennings'
                RETURN substring(e.content, 0, 800) AS content
                LIMIT 1
            """)
            
            context = ""
            for record in result:
                context = record["content"]
                break
        
        driver.close()
        
        if not context:
            print("❌ No context found for Jennings")
            return
        
        # Simple prompt
        prompt = f"""Question: {question}

Context: {context}

Answer the question in 2-3 clear sentences using the context above."""
        
        url = "http://localhost:11434/v1/chat/completions"
        data = {
            "model": "mistral-small3.1:latest",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print(f"🎯 Simple Q&A Test Result:")
            print(f"Question: {question}")
            print(f"Answer: {answer}")
        else:
            print(f"❌ Q&A failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Q&A test error: {e}")

if __name__ == "__main__":
    print("🧪 Running Simple Q&A Tests")
    print("=" * 50)
    simple_qa_test()