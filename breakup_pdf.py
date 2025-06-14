import pdfplumber
import os
import re
import json
from datetime import datetime
from pathlib import Path

def clean_filename(title):
    """Clean title for safe filename"""
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in title).strip()

def extract_book_metadata(pdf, pdf_path):
    """Extract book metadata from PDF"""
    metadata = pdf.metadata or {}
    
    # Get first few pages to extract additional info
    first_pages_text = ""
    for i, page in enumerate(pdf.pages[:5]):
        text = page.extract_text()
        if text:
            first_pages_text += text + "\n"
    
    # Try to extract title and author from metadata or text
    title = metadata.get('Title', '') or metadata.get('title', '')
    author = metadata.get('Author', '') or metadata.get('author', '')
    
    # If no metadata, try to parse from filename or first pages
    if not title:
        # Try filename first
        filename = os.path.basename(pdf_path)
        title_from_file = re.sub(r'\.pdf$', '', filename, flags=re.IGNORECASE)
        title = title_from_file.replace('_', ' ').replace('-', ' ').strip()
    
    if not author or not title:
        # Try to parse from text patterns
        title_patterns = [
            r'(?i)(?:title|book):\s*(.+?)(?:\n|by)',
            r'(?i)^(.+?)(?:\n.*?by\s+(.+?)(?:\n|$))',
            r'(?i)^([A-Z][A-Za-z\s,.:!?-]{10,}?)(?:\n.*?by\s+(.+?))?(?:\n|$)',
        ]
        
        author_patterns = [
            r'(?i)(?:by|author):\s*(.+?)(?:\n|$)',
            r'(?i)by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, first_pages_text[:1500])
            if match and not title:
                potential_title = match.group(1).strip()
                if len(potential_title) > 3 and len(potential_title) < 200:
                    title = potential_title
                    break
        
        for pattern in author_patterns:
            match = re.search(pattern, first_pages_text[:1500])
            if match and not author:
                potential_author = match.group(1).strip()
                if len(potential_author) > 3 and len(potential_author) < 100:
                    author = potential_author
                    break
    
    # Try to extract publication year
    year_match = re.search(r'(?:copyright|published|©)\s*(\d{4})', first_pages_text[:2000], re.IGNORECASE)
    year = int(year_match.group(1)) if year_match else None
    
    # Look for ISBN
    isbn_match = re.search(r'ISBN(?:-1[03])?:?\s*([0-9\-X]+)', first_pages_text, re.IGNORECASE)
    isbn = isbn_match.group(1) if isbn_match else ''
    
    return {
        'title': title or 'Unknown Title',
        'author': author or 'Unknown Author', 
        'year': year,
        'isbn': isbn,
        'pages': len(pdf.pages),
        'extracted_at': datetime.now().isoformat()
    }

def extract_toc_from_pdf(pdf):
    """Extract Table of Contents from PDF text"""
    toc_entries = []
    
    # Find the TOC page(s)
    toc_text = ""
    toc_found = False
    
    for page_num, page in enumerate(pdf.pages[:10]):  # Check first 10 pages for TOC
        text = page.extract_text()
        if not text:
            continue
            
        # Look for TOC indicators
        if re.search(r'(?i)\b(contents|table of contents)\b', text):
            toc_found = True
            toc_text += text + "\n"
            print(f"📋 Found TOC on page {page_num + 1}")
            
            # Also check next few pages for continuation
            for next_page_num in range(page_num + 1, min(page_num + 4, len(pdf.pages))):
                next_text = pdf.pages[next_page_num].extract_text()
                if next_text:
                    # Simple heuristic: if page has numbered entries, likely TOC continuation
                    if re.search(r'^\d+\.', next_text, re.MULTILINE):
                        toc_text += next_text + "\n"
                        print(f"📋 TOC continues on page {next_page_num + 1}")
                    else:
                        break
            break
    
    if not toc_found:
        print("⚠️  No TOC found, will try to detect structure from content")
        return []
    
    # Parse TOC entries
    lines = toc_text.split('\n')
    
    entry_counter = 1  # For unnumbered entries
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for numbered entries first (most common TOC format)
        # Patterns: "1. Title", "1 Title", "Chapter 1. Title", etc.
        numbered_patterns = [
            r'^(\d+)\.\s*(.+?)(?:\s+\.{2,}|\s+\d+\s*$|$)',  # "1. Title ... 25" or "1. Title"
            r'^(\d+)\s+(.+?)(?:\s+\.{2,}|\s+\d+\s*$|$)',    # "1 Title ... 25" or "1 Title"
            r'^Chapter\s+(\d+)\.?\s*(.+?)(?:\s+\.{2,}|\s+\d+\s*$|$)',  # "Chapter 1. Title"
            r'^Part\s+(\d+)\.?\s*(.+?)(?:\s+\.{2,}|\s+\d+\s*$|$)',     # "Part 1. Title"
        ]
        
        # Try numbered patterns first
        found_numbered = False
        for pattern in numbered_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                
                # Clean up title (remove page numbers, dots, etc.)
                title = re.sub(r'\s+\.{2,}.*$', '', title)  # Remove "... 25"
                title = re.sub(r'\s+\d+\s*$', '', title)   # Remove trailing page number
                title = title.strip()
                
                # Skip if title is too short or looks like metadata
                if len(title) < 3:
                    continue
                    
                # Skip common non-content entries
                skip_patterns = [
                    r'(?i)^(copyright|dedication|acknowledgment|about|bibliography|index)s?$',
                    r'(?i)^(contents|table of contents)$',
                    r'(?i)^(family tree|map|appendix)s?$'
                ]
                
                if any(re.search(skip_pattern, title) for skip_pattern in skip_patterns):
                    continue
                
                toc_entries.append({
                    'number': int(number),
                    'title': title,
                    'original_line': line
                })
                found_numbered = True
                break
        
        # If no numbered pattern found, try unnumbered chapter titles
        if not found_numbered:
            # Patterns for unnumbered chapters
            unnumbered_patterns = [
                r'^([A-Z][A-Za-z\s,\':!?\-&]+?)(?:\s+\.{2,}|\s+\d+\s*$|$)',  # "Chapter Title ... 25"
                r'^(Chapter\s+[A-Za-z\s,\':!?\-&]+?)(?:\s+\.{2,}|\s+\d+\s*$|$)',  # "Chapter Name"
                r'^(Part\s+[A-Za-z\s,\':!?\-&]+?)(?:\s+\.{2,}|\s+\d+\s*$|$)',     # "Part Name"
            ]
            
            for pattern in unnumbered_patterns:
                match = re.search(pattern, line)
                if match:
                    title = match.group(1).strip()
                    
                    # Clean up title
                    title = re.sub(r'\s+\.{2,}.*$', '', title)  # Remove "... 25"
                    title = re.sub(r'\s+\d+\s*$', '', title)   # Remove trailing page number
                    title = title.strip()
                    
                    # Skip if title is too short or looks like metadata
                    if len(title) < 5 or len(title) > 100:  # Reasonable title length
                        continue
                    
                    # Skip common non-content entries
                    skip_patterns = [
                        r'(?i)^(copyright|dedication|acknowledgment|about|bibliography|index)s?$',
                        r'(?i)^(contents|table of contents)$',
                        r'(?i)^(family tree|map|appendix)s?$',
                        r'(?i)^(preface|foreword|introduction|prologue|epilogue)$',
                        r'(?i)^(notes|references|sources)$'
                    ]
                    
                    if any(re.search(skip_pattern, title) for skip_pattern in skip_patterns):
                        continue
                    
                    # Check if this looks like a real chapter title (has some complexity)
                    if len(title.split()) >= 2:  # At least 2 words
                        toc_entries.append({
                            'number': entry_counter,
                            'title': title,
                            'original_line': line
                        })
                        entry_counter += 1
                        break
    
    # Sort by number to ensure correct order
    toc_entries.sort(key=lambda x: x['number'])
    
    print(f"📖 Extracted {len(toc_entries)} TOC entries")
    for entry in toc_entries[:5]:  # Show first 5
        print(f"   {entry['number']}. {entry['title']}")
    if len(toc_entries) > 5:
        print(f"   ... and {len(toc_entries) - 5} more")
    
    return toc_entries

def split_pdf_by_chapters(pdf_path, output_dir="./text_files", book_prefix=None, pages_per_chunk=15):
    """Split PDF by detecting chapters or using intelligent page chunks"""
    
    print(f"📚 Processing PDF: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        # Extract book metadata
        book_metadata = extract_book_metadata(pdf, pdf_path)
        print(f"📖 Detected: '{book_metadata['title']}' by {book_metadata['author']}")
        
        # Generate book prefix from title if not provided
        if not book_prefix:
            book_prefix = book_metadata['title'].lower().replace(' ', '_').replace("'", "")
            book_prefix = re.sub(r'[^a-z0-9_]', '', book_prefix)[:20]  # Max 20 chars
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save book metadata
        metadata_file = os.path.join(output_dir, f"{book_prefix}_metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(book_metadata, f, indent=2)
        
        # Extract TOC from PDF
        print("🔍 Extracting Table of Contents...")
        toc_entries = extract_toc_from_pdf(pdf)
        
        chunks = []
        
        if len(toc_entries) >= 3:  # Found reasonable number of TOC entries
            print(f"✅ Creating one file per TOC entry ({len(toc_entries)} entries)")
            
            # Find where each TOC entry appears in the PDF
            toc_with_pages = []
            
            for entry in toc_entries:
                # Search for this entry's content in the PDF (skip TOC pages)
                entry_title = entry['title']
                found_page = None
                
                # Look for the entry text in the PDF pages (start after page 10 to skip TOC)
                for page_num, page in enumerate(pdf.pages[10:], 10):  # Skip first 10 pages (TOC area)
                    page_text = page.extract_text()
                    if not page_text:
                        continue
                    
                    # Try to find this entry on the page - look for the title at start of content
                    search_patterns = [
                        entry_title,
                        entry_title[:25],  # First part of title
                        entry_title.split(' - ')[0] if ' - ' in entry_title else entry_title,  # Location part
                        entry_title.split(',')[0] if ',' in entry_title else entry_title,  # First part before comma
                    ]
                    
                    for pattern in search_patterns:
                        # Look for pattern near the beginning of the page (more likely to be a heading)
                        first_lines = '\n'.join(page_text.split('\n')[:10]).lower()
                        if len(pattern) > 5 and pattern.lower() in first_lines:
                            found_page = page_num
                            break
                    
                    if found_page is not None:
                        break
                
                # If still not found, estimate based on entry number
                if found_page is None:
                    # Rough estimate: each entry might be ~2-3 pages, starting after page 15
                    estimated_page = 15 + (entry['number'] - 1) * 2
                    if estimated_page < len(pdf.pages):
                        found_page = estimated_page
                        print(f"  📍 Estimated page {estimated_page} for section {entry['number']}")
                
                if found_page is not None:
                    toc_with_pages.append({
                        'number': entry['number'],
                        'title': entry['title'],
                        'page': found_page
                    })
                    
            print(f"📍 Located {len(toc_with_pages)} entries in PDF content")
            
            # Create one file per TOC entry
            for i, entry in enumerate(toc_with_pages):
                start_page = entry['page']
                
                # Calculate end page more conservatively
                if i + 1 < len(toc_with_pages):
                    next_page = toc_with_pages[i + 1]['page']
                    # Give each section at least 1 page, but stop before next section
                    end_page = max(start_page, next_page - 1)
                else:
                    # Last entry gets remaining pages
                    end_page = len(pdf.pages) - 1
                
                # Ensure minimum page range
                if end_page < start_page:
                    end_page = start_page
                
                # Extract text for this entry
                text = ""
                actual_pages = 0
                for page_num in range(start_page, end_page + 1):
                    if page_num < len(pdf.pages):
                        page_text = pdf.pages[page_num].extract_text()
                        if page_text and len(page_text.strip()) > 50:  # Only count pages with substantial text
                            text += page_text + "\n"
                            actual_pages += 1
                
                # If no text found, try to get at least the current page
                if not text.strip() and start_page < len(pdf.pages):
                    page_text = pdf.pages[start_page].extract_text()
                    if page_text:
                        text = page_text
                        actual_pages = 1
                
                # Create filename
                clean_title = clean_filename(entry['title'])
                filename = f"{book_prefix}_section_{entry['number']:03d}_{clean_title}.txt"
                filepath = os.path.join(output_dir, filename)
                
                # Create file content
                section_text = f"{entry['number']}. {entry['title']}\n\n{text.strip()}"
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(section_text)
                
                chunks.append({
                    "section_number": entry['number'],
                    "title": entry['title'],
                    "start_page": start_page + 1,
                    "end_page": end_page + 1,
                    "text_file": filename,
                    "word_count": len(section_text.split())
                })
                
                word_count = len(text.split())
                print(f"  📄 Section {entry['number']}: {entry['title'][:60]}... ({actual_pages} pages, {word_count} words)")
                
        else:
            print(f"⚠️  No clear chapters found. Splitting into {pages_per_chunk}-page sections...")
            chunks = split_pdf_by_pages_pdfplumber(pdf, output_dir, book_prefix, book_metadata, pages_per_chunk)
        
        print(f"\n✅ Extracted {len(chunks)} sections to {output_dir}")
        print(f"📋 Metadata saved to: {metadata_file}")
        
        # Create ingestion summary
        summary = {
            "book_metadata": book_metadata,
            "chapters": chunks,
            "total_chapters": len(chunks),
            "processing_date": datetime.now().isoformat(),
            "detection_method": "toc_based" if len(toc_entries) >= 3 else "page_chunks"
        }
        
        summary_file = os.path.join(output_dir, f"{book_prefix}_ingestion_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        # Print ingestion instructions
        print(f"\n🚀 READY FOR INGESTION:")
        print(f"   Book Pattern: {book_prefix}_chapter_*.txt")
        print(f"   Total Files: {len(chunks)} chapters")
        print(f"\n💡 To ingest this book:")
        print(f"   python multi_book_ingest.py")
        print(f"   # Then use: ingester.ingest_book(book_info, '{book_prefix}_chapter_*.txt')")
        
        return book_metadata, chunks

def split_pdf_by_pages_pdfplumber(pdf, output_dir, book_prefix, book_metadata, pages_per_chunk=15):
    """Fallback method: split PDF by page ranges using pdfplumber"""
    
    print(f"📄 Splitting {len(pdf.pages)} pages into chunks of {pages_per_chunk} pages each")
    
    chunks = []
    chunk_count = 0
    
    for start_page in range(0, len(pdf.pages), pages_per_chunk):
        chunk_count += 1
        end_page = min(start_page + pages_per_chunk - 1, len(pdf.pages) - 1)
        
        # Extract text
        text = ""
        for page_num in range(start_page, end_page + 1):
            if page_num < len(pdf.pages):
                page_text = pdf.pages[page_num].extract_text()
                if page_text:
                    # Clean up text
                    page_text = re.sub(r'\n\s*\n', '\n\n', page_text)
                    text += page_text + "\n"
        
        # Skip empty chunks
        if len(text.strip()) < 200:
            continue
        
        # Create chunk file
        filename = f"{book_prefix}_chapter_{chunk_count:02d}_pages_{start_page+1}-{end_page+1}.txt"
        filepath = os.path.join(output_dir, filename)
        
        chunk_text = f"CHAPTER {chunk_count}\nPages {start_page+1}-{end_page+1}\n\n{text.strip()}"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(chunk_text)
        
        chunks.append({
            "chapter_number": chunk_count,
            "title": f"Section {chunk_count} (Pages {start_page+1}-{end_page+1})",
            "start_page": start_page + 1,
            "end_page": end_page + 1,
            "text_file": filename,
            "word_count": len(chunk_text.split())
        })
        
        print(f"  📄 Chapter {chunk_count}: Pages {start_page+1}-{end_page+1} ({len(text.split())} words)")
    
    return chunks

def main():
    """Main function with command line argument support"""
    import sys
    
    # Get PDF file from command line argument or use default
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    else:
        pdf_file = "Waking the Lion - Roger L. Jennings.pdf"
        print("💡 No PDF file specified, using default")
    
    output_folder = "./text_files"
    
    # Check if PDF exists
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file not found: {pdf_file}")
        if len(sys.argv) <= 1:
            print("💡 Usage: python breakup_pdf.py 'path/to/your/book.pdf'")
        print("📁 Make sure the PDF file exists and the path is correct")
        return
    
    try:
        # Split the PDF using pdfplumber
        book_metadata, chapters = split_pdf_by_chapters(pdf_file, output_folder)
        
        print(f"\n📚 BOOK READY FOR INGESTION")
        print(f"Title: {book_metadata['title']}")
        print(f"Author: {book_metadata['author']}")
        print(f"Year: {book_metadata['year']}")
        print(f"Pages: {book_metadata['pages']}")
        print(f"Chapters/Sections: {len(chapters)}")
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. Install pdfplumber if needed: pip install pdfplumber")
        print(f"2. Check the generated files in {output_folder}/")
        print(f"3. Use multi_book_ingest.py to add this book to your database")
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        print(f"💡 Make sure pdfplumber is installed: pip install pdfplumber")

if __name__ == "__main__":
    main()
