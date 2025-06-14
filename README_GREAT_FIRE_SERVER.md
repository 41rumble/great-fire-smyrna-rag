# Great Fire of Smyrna Multi-Book QA Server

A sophisticated FastAPI server providing deep narrative analysis of the Great Fire of Smyrna crisis (1922) using **multiple historical sources** with hybrid semantic search capabilities and integration for Open WebUI.

## Features

🧠 **Multi-Book Semantic Search**
- **Graphiti integration** with OpenAI embeddings across 3 historical books
- **Cross-book entity resolution** connecting same people/events across sources
- **Source provenance tracking** showing which book provides each fact
- **Neo4j fallback** for precise manual queries and character profiles
- **Intelligent compression** of large content with query-specific relevance

🎭 **Cross-Source Historical Analysis**
- Compare different perspectives on the same events
- Character development across multiple accounts
- Cross-reference historical facts between sources
- Thematic analysis drawing from multiple narratives
- Source-aware answers showing book origins

📚 **Multi-Book Knowledge Graph**
- **3 Historical Books**: "Flames on the Water", "Waking the Lion", "The Great Fire"
- **500+ entities** extracted (people, places, events, organizations)
- **Cross-book relationships** linking shared historical figures
- **Source tracking** for each fact and relationship
- **Semantic search** across all content simultaneously

🔌 **Advanced Integration**
- FastAPI server with comprehensive metadata tracking
- Open WebUI pipeline for seamless chat integration
- Automatic query type detection with semantic understanding
- Configurable trigger keywords and analysis modes

## Quick Start

### 1. Setup (Choose Your Mode)

#### Neo4j Only Mode (Fast Setup)
```bash
python start_great_fire_server.py
```

#### Hybrid Mode with Semantic Search (Advanced)
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

### 2. Test the Server

```bash
# Health check with system diagnostics
python start_great_fire_server.py test

# Test semantic search (if Graphiti enabled)
python test_graphiti.py

# Or direct HTTP
curl http://localhost:8002/api/health
```

### 3. Add to Open WebUI

1. Copy the contents of `great_fire_pipeline.py`
2. In Open WebUI, go to **Admin > Pipelines**
3. Click **Add Pipeline** and paste the content
4. Configure the server URL (default: `http://localhost:8002`)
5. Enable the pipeline

## API Endpoints

### `POST /api/analyze`
Main analysis endpoint for questions about The Great Fire of Smyrna.

**Request:**
```json
{
  "query": "How did Jennings' character develop throughout the story?",
  "analysis_type": "comprehensive"
}
```

**Response (Enhanced with Multi-Book Metadata):**
```json
{
  "answer": "Detailed cross-book narrative analysis...",
  "analysis_type": "character_analysis",
  "entities_found": 12,
  "processing_time": 4.2,
  "query_type_detected": "character_analysis",
  "search_method": "graphiti_semantic",
  "books_referenced": {
    "Flames on the Water": 3,
    "Waking the Lion": 2,
    "The Great Fire": 1
  },
  "graphiti_enabled": true
}
```

### `GET /api/capabilities`
Returns available analysis types and supported entities.

### `GET /api/health`
Server health check.

## Analysis Types

| Type | Description | Search Method | Example Query |
|------|-------------|---------------|---------------|
| `comprehensive` | General analysis with auto-detection | Hybrid semantic | "What role did Atatürk play?" |
| `character_analysis` | Character arc and development | Profile + semantic | "How did Jennings change throughout the story?" |
| `story_progression` | Narrative structure and pacing | Semantic temporal | "How does the story build tension?" |
| `relationships` | Connections between entities | Graph + semantic | "What was the relationship between Jennings and Atatürk?" |
| `themes` | Thematic and symbolic analysis | Pure semantic | "What themes of humanitarian crisis emerge?" |
| `temporal` | Chronological and timeline analysis | Temporal semantic | "How do events unfold in September 1922?" |

## Supported Characters

- **Asa Jennings** - American humanitarian leader
- **Mustafa Kemal (Atatürk)** - Turkish military/political leader  
- **Mark Bristol** - American naval officer and diplomat
- **Halsey Powell** - American naval officer
- **Franklin Roosevelt** - US President
- And many more historical figures...

## Configuration

### Pipeline Settings (Open WebUI)

- **Server URL**: Default `http://localhost:8002`
- **Analysis Type**: `comprehensive` (auto-detect) or specific type
- **Trigger Keywords**: Comma-separated list of keywords that activate the pipeline
- **Min Confidence**: Threshold for triggering (0.0-1.0)
- **Auto Detection**: Enable intelligent query type detection

### Server Settings

The server automatically connects to:
- **Neo4j**: `bolt://localhost:7687` with database `the-great-fire-db`
- **Ollama**: `http://localhost:11434` with model `mistral-small3.1:latest`
- **OpenAI**: For semantic search and compression (optional)
- **Port**: `8002` (configurable in server code)

### Search Behavior
- **With OpenAI key**: Hybrid semantic search → Neo4j fallback → compression
- **Without OpenAI key**: Enhanced Neo4j manual search only

## Example Multi-Book Queries

**Cross-Book Character Analysis:**
- "How does Asa Jennings appear differently in 'Waking the Lion' vs 'Flames on the Water'?"
- "Which book provides the most detail on Admiral Bristol's personality?"
- "Compare how different sources portray Mustafa Kemal Atatürk"

**Source Comparison:**
- "Which book has the most information about the Armenian evacuation?"
- "How do the three books differ in their coverage of American involvement?"
- "What perspectives on Turkish nationalism emerge across the sources?"

**Cross-Reference Queries:**
- "What do all three books say about the September 1922 fire?"
- "How do different authors describe the refugee crisis?"
- "Which source provides the most detail on Greek military actions?"

**Thematic Cross-Analysis:**
- "How do humanitarian themes develop across different accounts?"
- "What contrasting views of American foreign policy emerge?"
- "How does the portrayal of Ottoman collapse vary between sources?"

**Source-Aware Research:**
- "Find facts about Jennings that appear in multiple books"
- "Which book covers the naval evacuation in most detail?"
- "Compare different accounts of the final days in Smyrna"

## Architecture

### Basic Mode (Neo4j Only)
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Open WebUI    │───▶│  Pipeline Logic  │───▶│  FastAPI Server │
│                 │    │  (Trigger Check) │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Hybrid QA       │
                                                │ System          │
                                                └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Neo4j Database  │
                                                │ (Manual Search) │
                                                └─────────────────┘
```

### Hybrid Mode (With Graphiti)
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Open WebUI    │───▶│  Pipeline Logic  │───▶│  FastAPI Server │
│                 │    │  (Enhanced)      │    │  (Metadata)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Hybrid QA       │
                                                │ System          │
                                                └─────────────────┘
                                                         │
                                    ┌────────────────────┼────────────────────┐
                                    ▼                    ▼                    ▼
                          ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
                          │ Graphiti        │  │ Neo4j Manual    │  │ Batch           │
                          │ Semantic Search │  │ Search Fallback │  │ Compression     │
                          │ (Primary)       │  │                 │  │ (OpenAI)        │
                          └─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Troubleshooting

**Server won't start:**
- Check Neo4j is running: `systemctl status neo4j`
- Verify database exists: Use Neo4j Browser to check `the-great-fire-db`
- Install dependencies: `pip install fastapi uvicorn neo4j graphiti-core`
- Check Ollama is running: `ollama list` should show `mistral-small3.1:latest`

**Graphiti semantic search issues:**
- Run `python setup_graphiti_indexes.py` to create required indexes
- Verify OpenAI API key is valid in `.env` file
- Test with `python test_graphiti.py` for troubleshooting
- Check Neo4j fulltext indexes: `SHOW INDEXES`

**Pipeline not triggering:**
- Check trigger keywords in pipeline settings
- Lower the confidence threshold
- Verify server URL is correct
- Test server health: `python start_great_fire_server.py test`

**Empty/error responses:**
- Check server logs for errors and metadata tracking
- Verify knowledge graph has data: Check both Neo4j and Graphiti
- Test with simple queries first, then complex thematic ones
- Monitor processing times and compression indicators

## Development

**Running in development mode:**
```bash
uvicorn great_fire_server:app --reload --port 8002
```

**Adding new analysis types:**
1. Add detection logic in `detect_query_type()` in `hybrid_qa_system.py`
2. Add semantic search patterns for Graphiti integration
3. Update `/api/analyze` endpoint handlers
4. Update capabilities endpoint and metadata tracking
5. Test with both semantic and manual search examples

**Extending the knowledge graph:**
- **Neo4j data**: Use `enhanced_narrative_ingest.py` to add more chapters
- **Graphiti migration**: Run `ingest_to_graphiti.py` after Neo4j updates
- **Semantic enhancement**: Modify entity extraction for embeddings
- **Query patterns**: Update QA system for new semantic search patterns

**Performance optimization:**
- Monitor compression effectiveness with metadata tracking
- Adjust batch sizes in compression logic if needed
- Profile search method selection (semantic vs manual)
- Optimize Ollama parameters for response quality