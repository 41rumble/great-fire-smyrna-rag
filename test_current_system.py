#!/usr/bin/env python3
"""
Quick test of the current hybrid QA system to establish baseline performance
"""

import asyncio
from hybrid_qa_system import HybridQASystem

async def test_current_system():
    print("🔥 TESTING CURRENT HYBRID QA SYSTEM")
    print("=" * 50)
    
    qa_system = HybridQASystem()
    
    # Test a few representative questions
    test_questions = [
        "What was Asa Jennings' role in the evacuation?",
        "How did Atatürk and American officials interact?",
        "What humanitarian organizations were involved?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 30)
        
        try:
            answer = await qa_system.answer_question(question)
            print(f"Answer: {answer[:300]}...")
            print(f"Length: {len(answer)} characters")
        except Exception as e:
            print(f"Error: {e}")
    
    qa_system.close()
    print("\n✅ Current system test complete")

if __name__ == "__main__":
    asyncio.run(test_current_system())