#!/usr/bin/env python3
"""
Analyze the knowledge graph for "The Great Fire" to understand connectivity and information richness
"""

import requests

def test_neo4j_connectivity():
    """Test complex queries about The Great Fire to see how well connected the knowledge graph is"""
    
    # Use the hybrid QA system to test various types of queries
    server_url = "http://localhost:8002"
    
    print("🔥 KNOWLEDGE GRAPH ANALYSIS - THE GREAT FIRE OF SMYRNA")
    print("=" * 70)
    
    # Test queries of increasing complexity
    test_queries = [
        {
            "query": "Who is Asa Jennings?",
            "type": "Character Profile",
            "purpose": "Test basic character retrieval"
        },
        {
            "query": "What was the relationship between Atatürk and American officials?",
            "type": "Relationship Analysis", 
            "purpose": "Test relationship traversal"
        },
        {
            "query": "How did the evacuation efforts unfold chronologically?",
            "type": "Temporal Analysis",
            "purpose": "Test event sequencing and temporal connections"
        },
        {
            "query": "What were the humanitarian organizations involved and how did they coordinate?",
            "type": "Organizational Network",
            "purpose": "Test organizational relationships and coordination"
        },
        {
            "query": "How did personal relationships affect diplomatic decisions during the crisis?",
            "type": "Complex Synthesis",
            "purpose": "Test multi-layer reasoning across personal/political domains"
        },
        {
            "query": "What role did naval forces play in both military operations and humanitarian rescue?",
            "type": "Dual-Role Analysis", 
            "purpose": "Test understanding of conflicting/complementary roles"
        },
        {
            "query": "How did the events in Smyrna reflect broader patterns of post-WWI geopolitics?",
            "type": "Historical Context",
            "purpose": "Test broader historical understanding and synthesis"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i}. TESTING: {test['type']}")
        print(f"Query: {test['query']}")
        print(f"Purpose: {test['purpose']}")
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{server_url}/api/analyze",
                json={"query": test['query'], "analysis_type": "comprehensive"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', 'No answer')
                entities = result.get('entities_found', 0)
                time_taken = result.get('processing_time', 0)
                
                # Analyze answer quality
                answer_length = len(answer.split())
                has_specifics = any(term in answer.lower() for term in ['september', '1922', 'smyrna', 'bristol', 'jennings'])
                has_relationships = any(term in answer.lower() for term in ['between', 'worked with', 'coordinated', 'relationship'])
                
                quality_score = 0
                if answer_length > 50: quality_score += 1
                if has_specifics: quality_score += 1  
                if has_relationships: quality_score += 1
                if entities > 5: quality_score += 1
                
                print(f"✅ SUCCESS")
                print(f"Answer length: {answer_length} words")
                print(f"Entities found: {entities}")
                print(f"Processing time: {time_taken}s")
                print(f"Quality indicators: Specifics={has_specifics}, Relationships={has_relationships}")
                print(f"Quality score: {quality_score}/4")
                print(f"\nAnswer preview: {answer[:200]}...")
                
                results.append({
                    'query_type': test['type'],
                    'success': True,
                    'quality_score': quality_score,
                    'answer_length': answer_length,
                    'entities': entities,
                    'time': time_taken
                })
                
            else:
                print(f"❌ FAILED: HTTP {response.status_code}")
                results.append({
                    'query_type': test['type'],
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append({
                'query_type': test['type'],
                'success': False,
                'error': str(e)
            })
    
    # Summary analysis
    print("\n" + "=" * 70)
    print("📊 KNOWLEDGE GRAPH ANALYSIS SUMMARY")
    print("=" * 70)
    
    successful_queries = [r for r in results if r.get('success')]
    
    if successful_queries:
        avg_quality = sum(r.get('quality_score', 0) for r in successful_queries) / len(successful_queries)
        avg_entities = sum(r.get('entities', 0) for r in successful_queries) / len(successful_queries)
        avg_time = sum(r.get('time', 0) for r in successful_queries) / len(successful_queries)
        
        print(f"✅ Successful queries: {len(successful_queries)}/{len(test_queries)}")
        print(f"📊 Average quality score: {avg_quality:.1f}/4")
        print(f"🎭 Average entities found: {avg_entities:.1f}")
        print(f"⚡ Average response time: {avg_time:.1f}s")
        
        print(f"\n🔍 QUERY TYPE PERFORMANCE:")
        for result in successful_queries:
            status = "🟢 STRONG" if result.get('quality_score', 0) >= 3 else "🟡 MODERATE" if result.get('quality_score', 0) >= 2 else "🔴 WEAK"
            print(f"  {status} {result['query_type']}: {result.get('quality_score', 0)}/4")
        
        print(f"\n💡 KNOWLEDGE GRAPH ASSESSMENT:")
        if avg_quality >= 3:
            print("🟢 EXCELLENT: Knowledge graph has rich, well-connected information")
        elif avg_quality >= 2:
            print("🟡 GOOD: Knowledge graph has solid information with some gaps")
        else:
            print("🔴 NEEDS IMPROVEMENT: Knowledge graph may be missing key connections")
            
        print(f"\n🎯 RECOMMENDATIONS:")
        if avg_entities < 5:
            print("  - Consider ingesting more chapters to increase entity coverage")
        if avg_time > 5:
            print("  - Search performance could be optimized")
        if avg_quality < 3:
            print("  - Relationship extraction may need enhancement")
            print("  - Consider improving entity linking between episodes")
    
    else:
        print("❌ No successful queries - check if server is running on port 8002")
    
    return results

def test_server_connectivity():
    """Quick test to see if the server is accessible"""
    try:
        response = requests.get("http://localhost:8002/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Great Fire QA Server is running and accessible")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("💡 Make sure to start the server with: python great_fire_server.py")
        return False

if __name__ == "__main__":
    print("🔥 Starting Knowledge Graph Analysis...")
    
    if test_server_connectivity():
        print("🚀 Running comprehensive analysis...\n")
        results = test_neo4j_connectivity()
    else:
        print("🛑 Cannot proceed without server connectivity")