import os
import asyncio
import glob
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Set OpenAI configuration for Graphiti
os.environ["OPENAI_API_KEY"] = input("Enter your OpenAI API key: ").strip()
os.environ["OPENAI_MODEL"] = "gpt-4o-mini"  # Cost-effective but high quality
os.environ["OPENAI_EMBEDDING_MODEL"] = "text-embedding-3-small"

from graphiti_core import Graphiti

class HybridOpenAIIngest:
    def __init__(self, text_directory="./text_files"):
        self.text_directory = text_directory
        
        # Use Graphiti with OpenAI for maximum quality
        self.graphiti = Graphiti(
            uri=os.getenv("NEO4J_URI"),
            user=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD")
        )
        self.processed_episodes = []
    
    def extract_chapter_metadata(self, filename: str, content: str) -> dict:
        """Extract chapter metadata"""
        import re
        
        # Extract chapter number and title
        chapter_match = re.search(r'CHAPTER\s+(\d+)\s*\n(.+)', content)
        if chapter_match:
            chapter_num = int(chapter_match.group(1))
            title = chapter_match.group(2).strip()
        else:
            chapter_num = 0
            title = filename.replace('.txt', '').replace('TheGreatFire_', '')
        
        # Extract dates mentioned
        dates = re.findall(r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', content)
        
        return {
            "chapter_number": chapter_num,
            "title": title,
            "dates": dates[:3],
            "word_count": len(content.split()),
            "filename": filename
        }
    
    def split_into_optimal_episodes(self, content: str, metadata: dict) -> list:
        """Split content into optimal episodes for Graphiti processing"""
        # Split by paragraphs but aim for 800-1200 word episodes
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        episodes = []
        current_episode = []
        current_word_count = 0
        target_words = 1000
        
        for para in paragraphs:
            para_words = len(para.split())
            
            if current_word_count + para_words > target_words and current_episode:
                # Create episode
                episode_text = '\n\n'.join(current_episode)
                episodes.append({
                    "content": episode_text,
                    "word_count": current_word_count,
                    "metadata": metadata
                })
                current_episode = [para]
                current_word_count = para_words
            else:
                current_episode.append(para)
                current_word_count += para_words
        
        # Add final episode
        if current_episode:
            episode_text = '\n\n'.join(current_episode)
            episodes.append({
                "content": episode_text,
                "word_count": current_word_count,
                "metadata": metadata
            })
        
        return episodes
    
    async def process_episode_with_graphiti(self, episode_data: dict, episode_index: int):
        """Process episode using Graphiti's full capabilities"""
        content = episode_data["content"]
        metadata = episode_data["metadata"]
        
        # Create rich episode name
        episode_name = f"Great Fire of Smyrna - {metadata['title']} (Episode {episode_index + 1})"
        
        # Create comprehensive source description for better context
        source_description = f"""
        Historical Document Analysis: The Great Fire of Smyrna, September 1922
        
        Chapter {metadata['chapter_number']}: {metadata['title']}
        Source File: {metadata['filename']}
        Episode {episode_index + 1} of chapter
        Word Count: {episode_data['word_count']} words
        
        Historical Context: This episode covers events during the Great Fire of Smyrna crisis in September 1922, 
        a pivotal moment in the aftermath of World War I and the collapse of the Ottoman Empire. 
        The events involved complex relationships between American relief workers, Turkish military forces, 
        Greek and Armenian civilians, and international diplomatic efforts.
        
        Key Historical Themes: Refugee evacuation, international humanitarian response, military operations, 
        civilian displacement, diplomatic negotiations, and cross-cultural interactions during crisis.
        
        Time Period: Primarily September 1922, with references to preceding events from 1919-1922.
        Geographic Focus: Smyrna (modern Izmir), Constantinople (Istanbul), and surrounding regions.
        """
        
        # Set reference time based on historical context
        reference_time = datetime(1922, 9, 13)  # Peak of the Great Fire crisis
        
        # Try to extract more specific date if available
        if metadata['dates']:
            for date_str in metadata['dates']:
                if '1922' in date_str:
                    if 'September' in date_str:
                        reference_time = datetime(1922, 9, 13)
                    elif 'August' in date_str:
                        reference_time = datetime(1922, 8, 20)
                    break
        
        print(f"      📄 Processing: {episode_name}")
        print(f"         Words: {episode_data['word_count']}")
        print(f"         Reference time: {reference_time.strftime('%B %d, %Y')}")
        
        try:
            # Use Graphiti's full power with OpenAI
            result = await self.graphiti.add_episode(
                name=episode_name,
                episode_body=content,
                source_description=source_description.strip(),
                reference_time=reference_time
            )
            
            self.processed_episodes.append({
                "name": episode_name,
                "result": str(result),  # Convert to string for logging
                "metadata": metadata,
                "episode_index": episode_index
            })
            
            print(f"         ✅ Successfully processed with Graphiti")
            return True
            
        except Exception as e:
            print(f"         ❌ Error processing episode: {e}")
            return False
    
    async def process_file_comprehensive(self, file_path: str):
        """Process a single file with full Graphiti capabilities"""
        filename = Path(file_path).name
        print(f"\n📚 Processing: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            print(f"   📄 File size: {len(content)} characters")
            
            if len(content.strip()) < 100:
                print(f"   ⏭️  Skipping - too short")
                return 0
            
            # Extract metadata
            metadata = self.extract_chapter_metadata(filename, content)
            print(f"   📖 Chapter {metadata['chapter_number']}: {metadata['title']}")
            print(f"   📅 Historical dates mentioned: {metadata['dates']}")
            
            # Split into optimal episodes
            episodes = self.split_into_optimal_episodes(content, metadata)
            print(f"   📑 Split into {len(episodes)} episodes for processing")
            
            success_count = 0
            for i, episode_data in enumerate(episodes):
                print(f"   🔄 Processing episode {i+1}/{len(episodes)}...")
                success = await self.process_episode_with_graphiti(episode_data, i)
                if success:
                    success_count += 1
                    print(f"      ✅ Episode {i+1} successful")
                else:
                    print(f"      ❌ Episode {i+1} failed")
                
                # Brief pause to respect API rate limits
                await asyncio.sleep(2)
            
            print(f"   📊 Final result: {success_count}/{len(episodes)} episodes processed")
            return success_count
            
        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            return 0
    
    async def process_all_files(self):
        """Process all files using OpenAI-powered Graphiti"""
        txt_files = glob.glob(os.path.join(self.text_directory, "*.txt"))
        
        if not txt_files:
            print(f"No .txt files found in {self.text_directory}")
            return
        
        print(f"🔥 HYBRID OPENAI INGESTION - GREAT FIRE OF SMYRNA")
        print(f"📊 Found {len(txt_files)} files to process")
        print(f"🤖 Using OpenAI GPT-4o-mini for high-quality entity extraction")
        print(f"🔍 Using OpenAI embeddings for semantic search capabilities")
        print("=" * 80)
        
        total_episodes = 0
        total_files = 0
        
        for file_path in sorted(txt_files):
            episode_count = await self.process_file_comprehensive(file_path)
            total_episodes += episode_count
            if episode_count > 0:
                total_files += 1
        
        print(f"\n" + "=" * 80)
        print(f"🎉 HYBRID INGESTION COMPLETE!")
        print(f"📊 Statistics:")
        print(f"   📁 Files successfully processed: {total_files}/{len(txt_files)}")
        print(f"   📄 Total episodes created: {total_episodes}")
        print(f"   🧠 Knowledge graph built with OpenAI-quality extraction")
        print(f"   🔍 Ready for local Ollama-powered querying!")
        print("=" * 80)
        
        return total_episodes
    
    async def test_graphiti_search(self):
        """Test Graphiti's built-in search capabilities"""
        print(f"\n🔍 Testing Graphiti's semantic search capabilities...")
        
        test_queries = [
            "Asa Jennings",
            "American relief efforts",
            "Turkish military evacuation",
            "Smyrna refugees"
        ]
        
        for query in test_queries:
            try:
                print(f"\n   Testing: '{query}'")
                results = await self.graphiti.search(query, limit=3)
                print(f"   ✅ Found {len(results) if isinstance(results, list) else 1} semantic matches")
            except Exception as e:
                print(f"   ❌ Search error: {e}")
    
    def close(self):
        """Clean up resources"""
        # Graphiti handles its own connection management
        pass

async def main():
    print("🚀 HYBRID OPENAI + LOCAL OLLAMA SYSTEM")
    print("=" * 60)
    print("Phase 1: Use OpenAI for high-quality knowledge graph ingestion")
    print("Phase 2: Use local Ollama for private, conversational Q&A")
    print("=" * 60)
    
    # Test OpenAI API key
    print("🔑 Testing OpenAI API key...")
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "sk-fake-key-for-ollama":
        print("❌ No valid OpenAI API key found!")
        print("Please set OPENAI_API_KEY in your .env file")
        return
    
    print(f"✅ OpenAI API key found: {api_key[:20]}...")
    
    # Test basic OpenAI call
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        print(f"✅ OpenAI API test: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return
    
    # Get text directory
    text_dir = input("Enter path to text files (or press Enter for '~/Downloads/chapters'): ").strip()
    if not text_dir:
        text_dir = "~/Downloads/chapters"
    
    text_dir = os.path.expanduser(text_dir)
    
    # Confirm OpenAI usage
    print(f"\n⚠️  This will use OpenAI API for ingestion (estimated cost: $2-5 for 36 chapters)")
    confirm = input("Continue? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Cancelled.")
        return
    
    processor = HybridOpenAIIngest(text_dir)
    
    # Phase 1: OpenAI-powered ingestion
    total_episodes = await processor.process_all_files()
    
    if total_episodes > 0:
        # Test the semantic search
        await processor.test_graphiti_search()
        
        print(f"\n✨ SUCCESS! Your knowledge graph is now built with OpenAI-quality extraction.")
        print(f"🔄 Next step: Use 'python advanced_qa_v2.py' for local Ollama-powered Q&A")
        print(f"💡 You'll get the best of both worlds: OpenAI quality + local privacy!")
    
    processor.close()

if __name__ == "__main__":
    asyncio.run(main())