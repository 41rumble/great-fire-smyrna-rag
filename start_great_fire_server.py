#!/usr/bin/env python3
"""
Startup script for the Great Fire of Smyrna QA Server
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import neo4j
        print("✅ Dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install: pip install fastapi uvicorn neo4j")
        return False

def check_neo4j_connection():
    """Check if Neo4j is running and accessible"""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Sk1pper(())"))
        with driver.session(database="the-great-fire-db") as session:
            result = session.run("RETURN count(*) as count")
            count = result.single()["count"]
            print(f"✅ Neo4j connection successful ({count} nodes)")
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("Please ensure Neo4j is running and the database 'the-great-fire-db' exists")
        return False

def start_server():
    """Start the Great Fire QA server"""
    print("🔥 Starting Great Fire of Smyrna QA Server...")
    print("=" * 60)
    
    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check Neo4j connection
    if not check_neo4j_connection():
        return False
    
    print("🚀 Launching server on http://localhost:8002")
    print("📚 Specialized in The Great Fire of Smyrna historical analysis")
    print("🎭 Available analysis types:")
    print("   • Character Arc Analysis")
    print("   • Story Progression")  
    print("   • Relationship Exploration")
    print("   • Thematic Analysis")
    print("   • Temporal Flow Analysis")
    print("=" * 60)
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "great_fire_server:app",
            "--host", "0.0.0.0",
            "--port", "8002",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🔄 Server shutdown requested")
        return True
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False

def test_server():
    """Test if the server is responding"""
    print("🧪 Testing server health...")
    try:
        response = requests.get("http://localhost:8002/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Server health check: {health_data}")
            
            # Test capabilities
            cap_response = requests.get("http://localhost:8002/api/capabilities", timeout=5)
            if cap_response.status_code == 200:
                capabilities = cap_response.json()
                print(f"✅ Server capabilities loaded: {len(capabilities['analysis_types'])} analysis types")
                return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_server()
    else:
        start_server()