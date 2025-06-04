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
            description="Comma-separated keywords that trigger specialized analysis"
        )

    def __init__(self):
        self.type = "manifold"
        self.id = "great_fire_qa"
        self.name = "Great Fire of Smyrna QA"
        self.valves = self.Valves()

    def pipelines(self) -> List[dict]:
        return [
            {
                "id": "great_fire_qa",
                "name": "Great Fire of Smyrna QA",
            }
        ]

    def should_trigger_specialized_analysis(self, message: str) -> bool:
        """Check if query should trigger specialized Great Fire analysis"""
        keywords = [k.strip().lower() for k in self.valves.trigger_keywords.split(",")]
        message_lower = message.lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword in message_lower)
        return matches > 0

    def pipe(
        self, 
        user_message: str, 
        model_id: str, 
        messages: List[dict], 
        body: dict
    ) -> Union[str, Generator, Iterator]:
        
        print(f"\n=== GREAT FIRE QA PIPELINE ===")
        print(f"User message: {user_message[:100]}...")
        print(f"Model ID: {model_id}")
        print(f"==============================\n")
        
        # Quick response for title/tag generation requests
        if any(keyword in user_message.lower() for keyword in ["generate", "tags", "categorizing", "themes", "task:"]):
            print("DETECTED TITLE GENERATION REQUEST - RETURNING QUICK RESPONSE")
            return '{"tags": ["History", "Great Fire", "Smyrna", "1922", "Ottoman Empire"]}'
        
        # Check if this should trigger specialized analysis
        use_specialized = self.should_trigger_specialized_analysis(user_message)
        
        if not use_specialized:
            print("No Great Fire keywords detected - using general analysis")
        else:
            print("🔥 Great Fire keywords detected - using specialized analysis")
        
        try:
            # Call the Great Fire QA server
            response = requests.post(
                f"{self.valves.server_url}/api/analyze",
                json={
                    "query": user_message,
                    "analysis_type": self.valves.analysis_type
                },
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                qa_response = response.json()
                answer = qa_response.get("answer", "No answer generated")
                analysis_type = qa_response.get("analysis_type", "unknown")
                entities_found = qa_response.get("entities_found", 0)
                processing_time = qa_response.get("processing_time", 0)
                query_type = qa_response.get("query_type_detected", "general")
                
                # Format the response with rich metadata if specialized analysis was used
                if use_specialized:
                    formatted_response = f"""📚 **The Great Fire of Smyrna - Historical Analysis**

{answer}

---
*🎭 Analysis: {analysis_type.replace('_', ' ').title()} | 🔍 Query Type: {query_type.replace('_', ' ').title()} | ⚡ {processing_time}s | 📊 {entities_found} entities*
*🔥 Specialized historical knowledge from deep narrative analysis*"""
                else:
                    # For non-specialized queries, just return the answer
                    formatted_response = answer
                
                print(f"\n=== RESPONSE GENERATED ===")
                print(f"Answer length: {len(formatted_response)}")
                print(f"Analysis type: {analysis_type}")
                print(f"Entities found: {entities_found}")
                print(f"Specialized: {use_specialized}")
                print(f"Answer preview: {formatted_response[:200]}...")
                print(f"========================\n")
                
                return formatted_response
                
            elif response.status_code == 404:
                return "❌ Great Fire QA server not found. Please ensure the server is running."
            elif response.status_code == 500:
                error_detail = response.json().get("detail", "Internal server error") if response.headers.get('content-type') == 'application/json' else "Internal server error"
                return f"⚠️ Great Fire QA server error: {error_detail}"
            else:
                return f"❌ Great Fire QA server returned status {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "🔌 Cannot connect to Great Fire QA server. Please check if the server is running on the configured URL."
        except requests.exceptions.Timeout:
            return "⏱️ Great Fire QA server request timed out. Complex analysis may take longer."
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return f"❌ Great Fire QA error: {str(e)}"