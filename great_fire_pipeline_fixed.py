from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field
import requests
import json


class Pipeline:
    class Valves(BaseModel):
        server_url: str = Field(
            default="http://host.docker.internal:8002",
            description="Great Fire QA server URL"
        )
        analysis_type: str = Field(
            default="comprehensive",
            description="Analysis type: comprehensive, character_analysis, story_progression, relationships, themes, temporal"
        )
        trigger_keywords: str = Field(
            default="great fire,smyrna,jennings,atatürk,bristol,1922,evacuation,humanitarian,turkish,greek,armenian,horton,kemal",
            description="Comma-separated keywords that trigger this pipeline"
        )
        min_confidence: float = Field(
            default=0.7,
            description="Minimum confidence threshold for triggering (0.0-1.0)"
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "great_fire_qa"
        self.name = "Great Fire of Smyrna QA"
        self.valves = self.Valves()

    def should_trigger(self, message: str) -> float:
        """Calculate confidence score for whether this query should trigger Great Fire analysis"""
        keywords = [k.strip().lower() for k in self.valves.trigger_keywords.split(",")]
        message_lower = message.lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword in message_lower)
        
        if matches == 0:
            return 0.0
        
        # Base confidence from keyword density
        keyword_density = matches / len(keywords)
        
        # Boost for specific high-value terms
        high_value_terms = ["great fire", "smyrna", "jennings", "atatürk", "1922"]
        high_value_matches = sum(1 for term in high_value_terms if term in message_lower)
        
        # Calculate final confidence
        confidence = min(1.0, keyword_density + (high_value_matches * 0.2))
        
        return confidence

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        
        # Check if query should trigger Great Fire analysis
        confidence = self.should_trigger(user_message)
        
        if confidence < self.valves.min_confidence:
            # Not confident this is a Great Fire query, pass through
            return None
            
        print(f"🔥 Great Fire QA triggered (confidence: {confidence:.2f}): {user_message[:50]}...")
        
        try:
            # Prepare request payload
            payload = {
                "query": user_message,
                "analysis_type": self.valves.analysis_type
            }
            
            response = requests.post(
                f"{self.valves.server_url}/api/analyze",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                qa_response = response.json()
                answer = qa_response.get("answer", "No answer generated")
                analysis_type = qa_response.get("analysis_type", "unknown")
                entities_found = qa_response.get("entities_found", 0)
                processing_time = qa_response.get("processing_time", 0)
                
                # Format the response with rich metadata
                formatted_response = f"""📚 **The Great Fire of Smyrna - Historical Analysis**

{answer}

---
*🎭 Analysis: {analysis_type.replace('_', ' ').title()} | ⚡ {processing_time}s | 📊 {entities_found} entities*
*🔥 Specialized historical knowledge from deep narrative analysis*"""
                
                return formatted_response
                
            else:
                return f"❌ Great Fire QA server error: {response.status_code}"
                
        except Exception as e:
            return f"❌ Great Fire QA error: {str(e)}"