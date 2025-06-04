import os
import asyncio
import glob
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
import re

load_dotenv()

# Override models before importing Graphiti
os.environ["OPENAI_EMBEDDING_MODEL"] = "nomic-embed-text:latest"
os.environ["OPENAI_MODEL"] = "mistral-small3.1:latest"
os.environ["OPENAI_API_KEY"] = "sk-fake-key-for-ollama"
os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"

from graphiti_core import Graphiti
from graphiti_core.llm_client import OpenAIClient
from graphiti_core.llm_client.config import LLMConfig

# Custom entity types for historical events
class HistoricalPerson(BaseModel):
    name: str = Field(description="Full name of the person")
    role: Optional[str] = Field(description="Their role or title (e.g., 'American missionary', 'Turkish commander')")
    nationality: Optional[str] = Field(description="Their nationality")

class HistoricalPlace(BaseModel):
    name: str = Field(description="Name of the place")
    type: str = Field(description="Type of place (city, district, building, ship, etc.)")
    location: Optional[str] = Field(description="Broader geographic context")

class HistoricalEvent(BaseModel):
    name: str = Field(description="Name or description of the event")
    date: Optional[str] = Field(description="When it occurred")
    type: str = Field(description="Type of event (fire, evacuation, military action, etc.)")

class Organization(BaseModel):
    name: str = Field(description="Name of the organization")
    type: str = Field(description="Type (military unit, relief agency, government, etc.)")

class ComprehensiveHistoricalIngest:
    def __init__(self, text_directory="./text_files"):
        self.text_directory = text_directory
        
        # Create custom LLM client with Ollama configuration
        llm_config = LLMConfig(
            api_key="sk-fake-key-for-ollama",
            base_url="http://localhost:11434/v1",
            model="mistral-small3.1:latest"
        )
        llm_client = OpenAIClient(config=llm_config)
        
        self.graphiti = Graphiti(
            uri=os.getenv("NEO4J_URI"),
            user=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD"),
            llm_client=llm_client
        )
        self.processed_episodes = []
    
    def extract_chapter_metadata(self, filename, content):
        """Extract metadata from chapter content"""
        # Extract chapter number and title
        chapter_match = re.search(r'CHAPTER\s+(\d+)\s*\n(.+)', content)
        if chapter_match:
            chapter_num = int(chapter_match.group(1))
            title = chapter_match.group(2).strip()
        else:
            chapter_num = 0
            title = filename.replace('.txt', '').replace('TheGreatFire_', '')
        
        # Extract approximate dates mentioned
        date_patterns = [
            r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
            r'(\d{4})',
            r'(spring|summer|fall|autumn|winter)\s+(\d{4})',
            r'(early|mid|late)\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})'
        ]
        
        dates_mentioned = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                dates_mentioned.append(match.group(0))
        
        return {
            "chapter_number": chapter_num,
            "title": title,
            "dates_mentioned": dates_mentioned[:5],  # First 5 dates found
            "word_count": len(content.split())
        }
    
    def split_into_episodes(self, content, filename, metadata):
        """Split long chapters into smaller episodes for better processing"""
        # Split by paragraphs, but group them into episodes of ~800-1200 words
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        episodes = []
        current_episode = []
        current_word_count = 0
        target_words = 1000
        
        for para in paragraphs:
            para_words = len(para.split())
            
            if current_word_count + para_words > target_words and current_episode:
                # Create episode from current paragraphs
                episode_text = '\n\n'.join(current_episode)
                episodes.append({
                    "content": episode_text,
                    "word_count": current_word_count,
                    "source_file": filename,
                    "chapter_info": metadata
                })
                current_episode = [para]
                current_word_count = para_words
            else:
                current_episode.append(para)
                current_word_count += para_words
        
        # Add remaining content as final episode
        if current_episode:
            episode_text = '\n\n'.join(current_episode)
            episodes.append({
                "content": episode_text,
                "word_count": current_word_count,
                "source_file": filename,
                "chapter_info": metadata
            })
        
        return episodes
    
    async def process_episode_comprehensive(self, episode_data, episode_index):
        """Process a single episode with comprehensive entity and relationship extraction"""
        content = episode_data["content"]
        metadata = episode_data["chapter_info"]
        filename = episode_data["source_file"]
        
        # Create detailed episode name
        episode_name = f"The Great Fire - {metadata['title']} (Part {episode_index + 1})"
        
        # Add rich context for better extraction
        context_description = f"""
        Chapter {metadata['chapter_number']}: {metadata['title']}
        Source: {filename}
        Historical Context: The Great Fire of Smyrna, September 1922
        Key dates in this section: {', '.join(metadata['dates_mentioned'])}
        This episode contains {episode_data['word_count']} words covering events during the Great Fire crisis.
        """
        
        # Estimate reference time based on content
        reference_time = datetime(1922, 9, 13)  # Default to middle of Great Fire period
        
        # Try to extract more specific date if possible
        for date_str in metadata['dates_mentioned']:
            if '1922' in date_str:
                try:
                    # Try to parse the date
                    if 'September' in date_str:
                        reference_time = datetime(1922, 9, 13)
                    elif 'August' in date_str:
                        reference_time = datetime(1922, 8, 15)
                    break
                except:
                    pass
        
        print(f"  📄 Processing episode: {episode_name}")
        print(f"     Words: {episode_data['word_count']}, Context: {len(context_description)} chars")
        
        try:
            result = await self.graphiti.add_episode(
                name=episode_name,
                episode_body=content,
                source_description=context_description.strip(),
                reference_time=reference_time
            )
            
            self.processed_episodes.append({
                "name": episode_name,
                "result": result,
                "metadata": metadata,
                "filename": filename
            })
            
            return result
        except Exception as e:
            print(f"     ❌ Error processing episode: {e}")
            return None
    
    async def process_all_chapters_comprehensive(self):
        """Process all chapters with maximum entity/relationship extraction"""
        txt_files = glob.glob(os.path.join(self.text_directory, "*.txt"))
        
        if not txt_files:
            print(f"No .txt files found in {self.text_directory}")
            return
            
        print(f"🔥 COMPREHENSIVE GREAT FIRE INGESTION")
        print(f"Found {len(txt_files)} text files to process comprehensively...")
        print("=" * 60)
        
        total_episodes = 0
        
        for file_path in sorted(txt_files):
            filename = Path(file_path).name
            print(f"\n📚 Processing: {filename}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                if len(content.strip()) < 100:
                    print(f"   ⏭️  Skipping {filename} - too short")
                    continue
                
                # Extract metadata
                metadata = self.extract_chapter_metadata(filename, content)
                print(f"   📋 Chapter {metadata['chapter_number']}: {metadata['title']}")
                print(f"   📅 Dates mentioned: {metadata['dates_mentioned'][:3]}")
                
                # Split into optimal episodes
                episodes = self.split_into_episodes(content, filename, metadata)
                print(f"   📑 Split into {len(episodes)} episodes")
                
                # Process each episode
                for i, episode_data in enumerate(episodes):
                    result = await self.process_episode_comprehensive(episode_data, i)
                    if result:
                        total_episodes += 1
                        print(f"     ✅ Episode {i+1} processed successfully")
                    else:
                        print(f"     ❌ Episode {i+1} failed")
                    
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error processing {filename}: {e}")
        
        print(f"\n" + "=" * 60)
        print(f"🎉 COMPREHENSIVE INGESTION COMPLETE!")
        print(f"📊 Total episodes processed: {total_episodes}")
        print(f"📁 Files processed: {len([ep for ep in self.processed_episodes])}")
        print("=" * 60)
        
        return total_episodes
    
    async def search_comprehensive(self, query):
        """Use Graphiti's built-in search with full context"""
        try:
            print(f"🔍 Searching knowledge graph for: '{query}'")
            results = await self.graphiti.search(query, limit=5)
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return None
    
    def close(self):
        """Close database connections"""
        # Graphiti handles its own connection management
        pass

async def main():
    # Get text directory
    text_dir = input("Enter path to your text files directory (or press Enter for '~/Downloads/chapters'): ").strip()
    if not text_dir:
        text_dir = "~/Downloads/chapters"
    
    # Expand user path
    text_dir = os.path.expanduser(text_dir)
    
    processor = ComprehensiveHistoricalIngest(text_dir)
    
    print("🚀 Starting comprehensive historical knowledge graph ingestion...")
    print("This will create rich entity relationships and temporal connections.")
    
    # Process all chapters
    total_episodes = await processor.process_all_chapters_comprehensive()
    
    if total_episodes > 0:
        print(f"\n🎯 Testing the comprehensive knowledge graph...")
        
        # Test queries
        test_queries = [
            "Who was Asa Jennings?",
            "What happened in September 1922?",
            "relationship between Atatürk and American relief efforts",
            "evacuation of Smyrna refugees"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing: {query}")
            results = await processor.search_comprehensive(query)
            if results:
                print(f"   ✅ Found {len(results) if isinstance(results, list) else 1} results")
            else:
                print(f"   ❌ No results found")
    
    processor.close()

if __name__ == "__main__":
    asyncio.run(main())