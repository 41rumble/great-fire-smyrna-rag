import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_ollama_chat():
    """Test Ollama chat endpoint"""
    url = "http://localhost:11434/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    data = {
        "model": "mistral-small3.1",
        "messages": [{"role": "user", "content": "Hello, can you respond?"}],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Chat test - Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result['choices'][0]['message']['content']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Chat test failed: {e}")

def test_ollama_embeddings():
    """Test Ollama embeddings endpoint"""
    url = "http://localhost:11434/v1/embeddings"
    headers = {"Content-Type": "application/json"}
    
    data = {
        "model": "nomic-embed-text",
        "input": "Test embedding text"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Embeddings test - Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Embedding dimension: {len(result['data'][0]['embedding'])}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Embeddings test failed: {e}")

if __name__ == "__main__":
    print("Testing Ollama endpoints...")
    test_ollama_chat()
    print()
    test_ollama_embeddings()