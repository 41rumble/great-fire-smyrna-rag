# Great Fire of Smyrna RAG System

A sophisticated historical research system for analyzing "The Great Fire of Smyrna" (1922) using hybrid semantic search with Neo4j knowledge graph, Graphiti embeddings, and local Ollama LLM.

## Features

🧠 **Hybrid Semantic Search**
- **Graphiti integration** with OpenAI embeddings for semantic understanding
- **Neo4j fallback** for precise manual queries and character profiles
- **Intelligent compression** of large content with query-specific relevance
- **Dynamic analysis types** based on query patterns

🎭 **Deep Historical Analysis**
- Character arc development and relationship networks
- Story progression and narrative structure analysis
- Thematic exploration and implicit pattern discovery
- Cross-temporal relationship evolution tracking

📚 **Advanced Knowledge Graph**
- Neo4j database with rich historical entities and relationships
- Semantic embeddings for conceptual understanding
- Episode content with narrative metadata and story positioning
- Character profiles with motivations and development arcs

🔌 **Local Privacy & Performance**
- Local Ollama LLM (mistral-small3.1) for answer generation
- Optional OpenAI integration for semantic search only
- Streamlined batch processing for fast response times
- FastAPI server with comprehensive metadata tracking

## Quick Start

### Prerequisites
- Neo4j running on localhost:7687 with "the-great-fire-db" database
- Ollama with mistral-small3.1:latest model
- Python 3.8+ with required dependencies
- Optional: OpenAI API key for semantic search

### Installation

1. **Clone and install dependencies:**
```bash
git clone https://github.com/41rumble/great-fire-smyrna-rag.git
cd great-fire-smyrna-rag
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your Neo4j credentials and optionally OpenAI API key
```

3. **Choose your setup:**

#### Option A: Neo4j Only (Fast Setup)
```bash
python start_great_fire_server.py
```

#### Option B: Hybrid with Semantic Search (Advanced)
```bash
# Set up Graphiti indexes
python setup_graphiti_indexes.py

# Initialize Graphiti schema  
python simple_graphiti_setup.py

# Ingest data with semantic embeddings
python ingest_to_graphiti.py

# Start server
python start_great_fire_server.py
```

### Usage

**Web Interface**: http://localhost:8002  
**API Endpoint**: `POST /api/analyze`  
**Health Check**: `GET /api/health`

#### Example Queries

**Factual Research:**
- "What was Asa Jennings' role in the evacuation?"
- "How did Atatürk and American officials interact?"
- "What were the key relationships during the crisis?"

**Thematic Analysis (Semantic Search):**
- "What underlying tensions existed between different cultural perspectives?"
- "How did concepts of leadership evolve throughout the crisis?"
- "What implicit conflicts emerged between humanitarian and political goals?"

**Character Development:**
- "Describe Atatürk's character arc in the book"
- "How did Jennings' motivations change throughout the evacuation?"

## System Architecture

### Basic Mode (Neo4j Only)
```
Question → FastAPI Server → Manual Neo4j Search → Ollama LLM → Response
```

### Hybrid Mode (With Graphiti)
```
Question → FastAPI Server → Graphiti Semantic Search → Manual Neo4j Fallback → Batch Compression → Ollama LLM → Response
```

## Core Files

**Main System:**
- `start_great_fire_server.py` - Server launcher with health checks
- `great_fire_server.py` - FastAPI web server and API endpoints
- `hybrid_qa_system.py` - Core QA logic with hybrid search capabilities

**Data & Setup:**
- `enhanced_narrative_ingest.py` - Neo4j data ingestion system
- `ingest_to_graphiti.py` - Semantic embedding migration to Graphiti
- `setup_graphiti_indexes.py` - Required Neo4j index creation
- `simple_graphiti_setup.py` - Graphiti schema initialization

**Documentation:**
- `PROJECT_STATUS.md` - Development progress and technical details
- `README_GREAT_FIRE_SERVER.md` - Detailed API documentation

## Configuration

### Environment Variables (`.env`)
```bash
# Neo4j Configuration (Required)
NEO4J_URI=bolt://localhost:7687
NEO4J_DATABASE=the-great-fire-db
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Ollama Configuration (Required)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral-small3.1:latest

# OpenAI Configuration (Optional - for semantic search)
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Search Behavior
- **With OpenAI key**: Semantic search first → Neo4j fallback
- **Without OpenAI key**: Enhanced Neo4j manual search only

## Advanced Features

### Intelligent Compression
- **Batch episode compression** for large content
- **Query-specific relevance filtering** 
- **Character profile preservation** (uncompressed)
- **Automatic size optimization** for response speed

### Response Metadata
All responses include comprehensive footer information:
- **Analysis Type**: Detected query category (general, character_analysis, themes, etc.)
- **Entity Count**: Actual number of sources consulted  
- **Processing Time**: Response generation duration
- **Search Method**: Semantic vs manual search indicator

### API Response Format
```json
{
  "answer": "Historical analysis...",
  "analysis_type": "character_analysis",
  "entities_found": 12,
  "processing_time": 4.2,
  "query_type_detected": "character_analysis"
}
```

## Development

### Current Branch: `graphiti-integration`
- Hybrid semantic search implementation
- Enhanced compression and metadata handling
- Comprehensive setup and migration scripts

### Testing
```bash
# Test basic functionality
python start_great_fire_server.py test

# Test Graphiti semantic search
python test_graphiti.py
```

## Use Cases

This system is designed for:
- **Historical researchers** conducting deep narrative analysis
- **Story writers** researching authentic historical details and relationships
- **Educators** exploring complex historical events and character motivations
- **Analysts** investigating thematic patterns and cultural tensions

The hybrid approach provides both precise factual lookup and sophisticated thematic discovery capabilities.

## License & Attribution

Historical content analysis system for "The Great Fire of Smyrna" research.  
Built with Neo4j, Graphiti, and Ollama for comprehensive historical intelligence.