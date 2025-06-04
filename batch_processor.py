import os
import glob
import asyncio
from pathlib import Path
from historical_researcher import HistoricalResearcher

class BookProcessor:
    def __init__(self, text_directory="./text_files"):
        self.researcher = HistoricalResearcher()
        self.text_directory = text_directory
        
    async def process_all_chapters(self):
        """Process all text files in the directory"""
        txt_files = glob.glob(os.path.join(self.text_directory, "*.txt"))
        
        if not txt_files:
            print(f"No .txt files found in {self.text_directory}")
            return
            
        print(f"Found {len(txt_files)} text files to process...")
        
        for file_path in sorted(txt_files):
            await self.process_chapter(file_path)
    
    async def process_chapter(self, file_path):
        """Process a single chapter file"""
        filename = Path(file_path).name
        print(f"\nProcessing: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Skip if file is empty or too short
            if len(content.strip()) < 50:
                print(f"Skipping {filename} - too short")
                return
                
            # Use filename as context
            context = f"Chapter: {filename.replace('.txt', '')}"
            
            # Process with Graphiti
            result = await self.researcher.process_historical_text(content, context)
            
            if result:
                print(f"✓ Successfully processed {filename}")
                print(f"  Result: {result}")
            else:
                print(f"✗ Failed to process {filename}")
                
        except Exception as e:
            print(f"✗ Error processing {filename}: {e}")
    
    async def query_processed_content(self, query):
        """Query the processed content"""
        return await self.researcher.query_knowledge_base(query)

async def main():
    # Change this path to where your txt files are located
    text_dir = input("Enter path to your text files directory (or press Enter for './text_files'): ").strip()
    if not text_dir:
        text_dir = "./text_files"
    
    processor = BookProcessor(text_dir)
    
    print("Starting batch processing...")
    await processor.process_all_chapters()
    
    print("\n" + "="*50)
    print("Processing complete! You can now query your knowledge base.")
    
    # Interactive querying
    while True:
        query = input("\nEnter a query (or 'quit' to exit): ").strip()
        if query.lower() in ['quit', 'exit', 'q']:
            break
            
        result = await processor.query_processed_content(query)
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())