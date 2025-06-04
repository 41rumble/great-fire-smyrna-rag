# Great Fire of Smyrna QA Server

A specialized FastAPI server providing deep narrative analysis of "The Great Fire of Smyrna" (1922) with integration for Open WebUI.

## Features

🎭 **Deep Narrative Analysis**
- Character arc development and emotional journeys
- Story progression through different acts
- Complex relationship exploration
- Thematic analysis and symbolic meaning
- Temporal flow and chronological analysis

📚 **Specialized Knowledge**
- Rich historical context from custom knowledge graph
- 36 chapters of detailed narrative analysis
- Character relationships and motivations
- Political, military, and humanitarian perspectives

🔌 **Easy Integration**
- FastAPI server with REST endpoints
- Open WebUI pipeline for seamless chat integration
- Automatic query type detection
- Configurable trigger keywords

## Quick Start

### 1. Start the Server

```bash
# Simple start
python start_great_fire_server.py

# Or manually
python great_fire_server.py
```

### 2. Test the Server

```bash
# Health check
python start_great_fire_server.py test

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

**Response:**
```json
{
  "answer": "Detailed narrative analysis...",
  "analysis_type": "character_analysis",
  "entities_found": 5,
  "processing_time": 2.3,
  "query_type_detected": "character_analysis"
}
```

### `GET /api/capabilities`
Returns available analysis types and supported entities.

### `GET /api/health`
Server health check.

## Analysis Types

| Type | Description | Example Query |
|------|-------------|---------------|
| `comprehensive` | General analysis with auto-detection | "What role did Atatürk play?" |
| `character_analysis` | Character arc and development | "How did Jennings change throughout the story?" |
| `story_progression` | Narrative structure and pacing | "How does the story build tension?" |
| `relationships` | Connections between entities | "What was the relationship between Jennings and Atatürk?" |
| `themes` | Thematic and symbolic analysis | "What themes of humanitarian crisis emerge?" |
| `temporal` | Chronological and timeline analysis | "How do events unfold in September 1922?" |

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
- **Port**: `8002` (configurable in server code)

## Example Queries

**Character Analysis:**
- "How did Jennings' motivations change throughout the evacuation?"
- "What was Atatürk's emotional journey during the crisis?"
- "Analyze Bristol's character development"

**Story Progression:**
- "How does the narrative build to the climax?"
- "What are the key turning points in the story?"
- "How does tension develop throughout the chapters?"

**Relationships:**
- "What was the dynamic between Jennings and Atatürk?"
- "How did American-Turkish relations evolve?"
- "Explore the connection between military and humanitarian efforts"

**Themes:**
- "What themes of cultural conflict emerge?"
- "How is the humanitarian crisis portrayed?"
- "What symbolic meaning does Smyrna represent?"

**Temporal Analysis:**
- "How do events unfold chronologically in September 1922?"
- "What is the pacing of the evacuation sequence?"
- "How do past events influence present actions?"

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Open WebUI    │───▶│  Pipeline Logic  │───▶│  FastAPI Server │
│                 │    │  (Trigger Check) │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Narrative QA    │
                                                │ System          │
                                                └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Neo4j Database  │
                                                │ (Knowledge      │
                                                │  Graph)         │
                                                └─────────────────┘
```

## Troubleshooting

**Server won't start:**
- Check Neo4j is running: `systemctl status neo4j`
- Verify database exists: Use Neo4j Browser to check `the-great-fire-db`
- Install dependencies: `pip install fastapi uvicorn neo4j`

**Pipeline not triggering:**
- Check trigger keywords in pipeline settings
- Lower the confidence threshold
- Verify server URL is correct

**Empty/error responses:**
- Check server logs for errors
- Verify knowledge graph has data
- Test with simple queries first

## Development

**Running in development mode:**
```bash
uvicorn great_fire_server:app --reload --port 8002
```

**Adding new analysis types:**
1. Add detection logic in `detect_query_type()`
2. Add handler in `/api/analyze` endpoint
3. Update capabilities endpoint
4. Test with example queries

**Extending the knowledge graph:**
- Use `enhanced_narrative_ingest.py` to add more chapters
- Modify entity extraction for additional data types
- Update QA system methods for new query patterns