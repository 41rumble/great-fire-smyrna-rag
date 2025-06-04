# Historical Research with Graphiti & Neo4j

A system for building a knowledge graph from historical texts using Graphiti with local Ollama models.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
   - Set your Neo4j credentials
   - Ensure Ollama is running locally
   - Optionally add web search API key

3. Set up Neo4j database:
```bash
python setup_neo4j.py
```

4. Run the historical researcher:
```bash
python historical_researcher.py
```

## Usage

The system can:
- Process historical texts and extract entities/relationships
- Build a knowledge graph over time
- Query the accumulated knowledge
- Integrate web search results for enrichment

Example workflow:
1. Feed historical documents into `process_historical_text()`
2. Use `search_and_enrich()` to add web research
3. Query with `query_knowledge_base()` 
4. Explore relationships with `get_relationships()`