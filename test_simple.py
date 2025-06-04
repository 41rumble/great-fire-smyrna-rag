import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Override embedding model before importing Graphiti
os.environ["OPENAI_EMBEDDING_MODEL"] = "nomic-embed-text:latest"

from graphiti_core import Graphiti
from datetime import datetime

async def test_simple_add():
    """Test adding a simple episode"""
    
    print("Creating Graphiti instance...")
    graphiti = Graphiti(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD")
    )
    
    print("Adding test episode...")
    try:
        result = await graphiti.add_episode(
            name="Test Episode",
            episode_body="This is a simple test. John Smith was born in 1800 in London.",
            source_description="Test data",
            reference_time=datetime.now()
        )
        print(f"Success! Result: {result}")
        return True
    except Exception as e:
        print(f"Failed to add episode: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_simple_add())