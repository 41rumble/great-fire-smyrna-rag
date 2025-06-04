#!/usr/bin/env python3
"""
Test conservative limit increases - avoid the repetition disaster
"""

import asyncio
from hybrid_qa_system import HybridQASystem

async def test_conservative():
    print("🔧 TESTING CONSERVATIVE LIMIT INCREASES")
    print("=" * 60)
    print("📊 CONSERVATIVE CHANGES:")
    print("   • 15 total entities (was 10) - 50% increase")
    print("   • 4 episodes per word (was 3) - 33% increase") 
    print("   • 1500 chars per episode (was 1200) - 25% increase")
    print("   • Everything else stays the same")
    print("=" * 60)
    
    qa_system = HybridQASystem()
    
    test_questions = [
        "What was Asa Jennings' role in the evacuation?",
        "How did Atatürk and American officials interact?",
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\\n{i}. CONSERVATIVE TEST")
        print(f"Question: {question}")
        print("-" * 50)
        
        try:
            answer = await qa_system.answer_question(question)
            
            # Check for repetition issues
            lines = answer.split('\\n')
            repeated_lines = 0
            for j in range(1, len(lines)):
                if lines[j] == lines[j-1] and len(lines[j].strip()) > 10:
                    repeated_lines += 1
            
            # Quality assessment
            quality_score = 0
            if len(answer) > 500: quality_score += 1  # Good length
            if repeated_lines < 3: quality_score += 1  # No major repetition
            if 'jennings' in answer.lower() or 'atatürk' in answer.lower(): quality_score += 1  # Relevant
            if not answer.startswith("I couldn't find"): quality_score += 1  # Found results
            
            print(f"\\n💡 Conservative Answer:")
            print(answer[:600] + "..." if len(answer) > 600 else answer)
            
            print(f"\\n📊 QUALITY CHECK:")
            print(f"   📏 Length: {len(answer)} chars, {len(answer.split())} words")
            print(f"   🔄 Repeated lines: {repeated_lines}")
            print(f"   🎯 Quality score: {quality_score}/4")
            
            if quality_score >= 3:
                print("   ✅ GOOD QUALITY - Conservative limits working!")
            else:
                print("   ⚠️ Quality issues detected")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
    qa_system.close()
    print("\\n🏁 Conservative testing complete!")

if __name__ == "__main__":
    asyncio.run(test_conservative())