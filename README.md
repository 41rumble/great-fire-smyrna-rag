# Great Fire of Smyrna RAG System

A specialized historical research system for analyzing "The Great Fire of Smyrna" (1922) using Neo4j knowledge graph and local Ollama LLM.

## Features

🎭 **Deep Historical Analysis**
- Character arc development and relationships
- Story progression and narrative structure
- Thematic analysis and historical context
- Natural conversational responses

📚 **Knowledge Graph**
- Neo4j database with rich historical entities
- Character profiles, events, and relationships
- Episode content with narrative metadata

🔌 **Local Privacy**
- Local Ollama LLM (mistral-small3.1)
- No external API calls for generation
- FastAPI server for easy integration

## Quick Start

### Prerequisites
- Neo4j running on localhost:7687
- Ollama with mistral-small3.1:latest model
- Python 3.8+

### Installation

1. Clone and install dependencies:
```bash
git clone https://github.com/41rumble/great-fire-smyrna-rag.git
cd great-fire-smyrna-rag
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Neo4j credentials
```

3. Start the server:
```bash
python start_great_fire_server.py
```

### Usage

**Web Interface**: http://localhost:8002
**API Endpoint**: `POST /api/analyze`

Example queries:
- "What was Asa Jennings' role in the evacuation?"
- "How did Atatürk and American officials interact?"
- "What were the key relationships during the crisis?"

## Core Files

- `start_great_fire_server.py` - Main entry point and server launcher
- `great_fire_server.py` - FastAPI web server and endpoints
- `hybrid_qa_system.py` - Core QA logic and Neo4j search
- `enhanced_narrative_ingest.py` - Data ingestion system
- `PROJECT_STATUS.md` - Current state and development notes

## Configuration

See `.env.example` for required environment variables:
- Neo4j connection details
- Ollama model configuration
- Optional API keys for extended features

## Architecture

```
Question → FastAPI Server → QA System → Neo4j Search → Ollama LLM → Response
```

For detailed setup and API documentation, see `README_GREAT_FIRE_SERVER.md`.