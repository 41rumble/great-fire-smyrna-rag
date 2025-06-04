from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import uvicorn
from hybrid_qa_system import HybridQASystem

app = FastAPI(
    title="Great Fire of Smyrna QA Server",
    description="Historical analysis server for The Great Fire of Smyrna with deep narrative insights",
    version="1.0.0"
)

# Initialize the QA system
qa_system = None

class QueryRequest(BaseModel):
    query: str
    analysis_type: str = "comprehensive"

class QueryResponse(BaseModel):
    answer: str
    analysis_type: str
    entities_found: int
    processing_time: float
    query_type_detected: str

@app.on_event("startup")
async def startup_event():
    """Initialize the QA system on startup"""
    global qa_system
    try:
        qa_system = HybridQASystem()
        print("✅ Great Fire QA System initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize QA system: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    global qa_system
    if qa_system:
        qa_system.close()
        print("🔄 QA System closed")

def detect_query_type(query: str) -> str:
    """Detect the type of query based on keywords"""
    query_lower = query.lower()
    
    # Factual questions (prioritize these over character analysis)
    factual_keywords = ["was", "did", "were", "where", "when", "what", "who", "how many", "which"]
    if any(word in query_lower for word in factual_keywords):
        return "general"  # Use general comprehensive query for factual questions
    
    # Character analysis keywords (only if explicitly asking about development/arcs)
    if any(word in query_lower for word in ["character", "arc", "development", "change", "growth", "motivations", "emotional"]):
        return "character_analysis"
    
    # Story progression keywords  
    story_keywords = ["story", "plot", "narrative", "structure", "progression", "timeline"]
    if any(word in query_lower for word in story_keywords):
        return "story_progression"
    
    # Relationship keywords
    relationship_keywords = ["relationship", "between", "and", "connection", "interaction"]
    if any(word in query_lower for word in relationship_keywords):
        return "relationships"
    
    # Thematic keywords
    theme_keywords = ["theme", "meaning", "significance", "symbol", "represents"]
    if any(word in query_lower for word in theme_keywords):
        return "themes"
    
    # Temporal keywords
    temporal_keywords = ["when", "time", "chronology", "timeline", "sequence", "before", "after"]
    if any(word in query_lower for word in temporal_keywords):
        return "temporal"
    
    return "general"

def extract_character_name(query: str) -> Optional[str]:
    """Extract character name from query"""
    query_lower = query.lower()
    characters = ["jennings", "atatürk", "bristol", "horton", "kemal", "roosevelt"]
    
    for char in characters:
        if char in query_lower:
            return char.title()
    return None

def extract_entities_from_query(query: str) -> tuple:
    """Extract entity names for relationship queries"""
    query_lower = query.lower()
    entities = ["jennings", "atatürk", "bristol", "horton", "kemal", "smyrna", "turkey", "greece"]
    
    found_entities = [entity.title() for entity in entities if entity in query_lower]
    
    if len(found_entities) >= 2:
        return found_entities[0], found_entities[1]
    elif len(found_entities) == 1:
        return found_entities[0], None
    else:
        return None, None

@app.post("/api/analyze", response_model=QueryResponse)
async def analyze_query(request: QueryRequest):
    """Analyze a query about The Great Fire of Smyrna"""
    global qa_system
    
    if not qa_system:
        raise HTTPException(status_code=500, detail="QA system not initialized")
    
    import time
    start_time = time.time()
    
    try:
        query_type_detected = detect_query_type(request.query)
        answer = ""
        entities_count = 0
        
        # Use the hybrid QA system - just answers questions directly
        answer = await qa_system.answer_question(request.query)
        entities_count = getattr(qa_system, 'last_entities_found', 0)  # Get actual count from QA system
        analysis_type = query_type_detected  # Use the detected query type
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            answer=answer,
            analysis_type=analysis_type,
            entities_found=entities_count,
            processing_time=round(processing_time, 2),
            query_type_detected=query_type_detected
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed after {processing_time:.2f}s: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    global qa_system
    return {
        "status": "healthy" if qa_system else "unhealthy",
        "service": "Great Fire QA Server",
        "version": "1.0.0"
    }

@app.get("/api/capabilities")
async def get_capabilities():
    """Get available analysis capabilities"""
    return {
        "analysis_types": [
            "comprehensive",
            "character_analysis", 
            "story_progression",
            "relationships",
            "themes",
            "temporal"
        ],
        "supported_characters": [
            "Jennings", "Atatürk", "Bristol", "Horton", "Kemal", "Roosevelt"
        ],
        "supported_themes": [
            "humanitarian crisis", "cultural conflict", "international relations"
        ],
        "description": "Deep narrative analysis of The Great Fire of Smyrna (1922)"
    }

if __name__ == "__main__":
    print("🔥 Starting Great Fire of Smyrna QA Server...")
    print("📚 Specialized in deep historical narrative analysis")
    print("🎭 Character arcs, story progression, relationships, and themes")
    print("=" * 60)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8002,
        log_level="info"
    )