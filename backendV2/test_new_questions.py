#!/usr/bin/env python3
"""Test new business intelligence questions with Groq AI enhancement"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

BASE_URL = "http://localhost:8001"
QUESTIONS_FILE = Path("../backend/new_questions.txt")
LOG_FILE = Path(f"new_questions_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

def load_questions() -> List[Dict[str, str]]:
    """Load questions from JSON file."""
    with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = []
    for category_name, category_data in data.items():
        for question in category_data.get('questions', []):
            questions.append({
                'category': category_name,
                'question': question
            })
    
    return questions

def evaluate_response_quality(question: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate if the response makes sense for the question."""
    makes_sense = False
    quality_score = 0.0
    issues = []
    
    # Extract response components
    match_info = response_data.get('match_info', {})
    response_message = match_info.get('description', '') or response_data.get('message', '')
    
    # Handle different data structures
    data_obj = response_data.get('data', {})
    if isinstance(data_obj, dict):
        data_points = data_obj.get('raw', [])
    elif isinstance(data_obj, list):
        data_points = data_obj
    else:
        data_points = []
    
    # Check if we have a meaningful response
    if response_message and len(response_message.strip()) > 10:
        quality_score += 0.3
    else:
        issues.append("Response message is too short or missing")
    
    # Check if message is human-readable (not just raw data dump)
    if response_message and len(response_message) > 50:
        # Check for conversational language
        conversational_keywords = ['based on', 'analysis', 'shows', 'indicates', 'primarily', 
                                   'due to', 'because', 'according', 'summary', 'trends']
        if any(keyword in response_message.lower() for keyword in conversational_keywords):
            quality_score += 0.3
        else:
            issues.append("Response lacks conversational/human-readable language")
    else:
        issues.append("Response message is too brief")
    
    # Check if we have data
    if data_points and len(data_points) > 0:
        quality_score += 0.2
    else:
        issues.append("No data points in response")
    
    # Check if data seems relevant (basic keyword matching)
    question_lower = question.lower()
    if data_points:
        # Check if data keys match question intent
        first_item = data_points[0] if isinstance(data_points[0], dict) else {}
        data_keys = ' '.join(str(first_item).lower())
        if any(word in data_keys or word in response_message.lower() 
               for word in question_lower.split() if len(word) > 3):
            quality_score += 0.2
        else:
            issues.append("Data may not be relevant to question")
    
    # Determine if it makes sense
    makes_sense = quality_score >= 0.6
    
    return {
        "makes_sense": makes_sense,
        "quality_score": round(quality_score, 2),
        "issues": issues
    }

def test_question(question: str, category: str, question_num: int, total: int) -> Dict[str, Any]:
    """Test a single question against the API."""
    print(f"\n🔍 Question {question_num}/{total}: '{question}'")
    print(f"   Category: {category}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={"query": question},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        response_time = (time.time() - start_time) * 1000
        
        # Extract metrics
        success = data.get("success", False)
        metadata = data.get("metadata", {})
        tokens_used = metadata.get("tokens_used", 0)
        cache_hit = metadata.get("cache_hit", False)
        
        # Extract data
        data_obj = data.get("data", {})
        if isinstance(data_obj, dict):
            data_points = data_obj.get("raw", [])
        elif isinstance(data_obj, list):
            data_points = data_obj
        else:
            data_points = []
        
        chart_config = data.get("chart_config")
        charts = 1 if chart_config else 0
        
        # Evaluate quality
        quality = evaluate_response_quality(question, data)
        
        # Extract response message
        match_info = data.get("match_info", {})
        response_message = match_info.get("description", "") or data.get("message", "")
        
        result = {
            "question_num": question_num,
            "question": question,
            "category": category,
            "success": success,
            "response_time_ms": round(response_time, 1),
            "tokens_used": tokens_used,
            "cache_hit": cache_hit,
            "data_points": len(data_points),
            "charts": charts,
            "quality": quality,
            "response_message": response_message,
            "sample_data": data_points[:3] if data_points else []
        }
        
        # Print summary
        status = "✅ SUCCESS" if success else "❌ FAILED"
        cache_status = "(cached)" if cache_hit else "(groq-enhanced)"
        print(f"   {status} {cache_status}")
        print(f"   Response time: {response_time:.1f}ms")
        print(f"   Tokens used: {tokens_used}")
        print(f"   Data points: {len(data_points)}")
        print(f"   Charts: {charts}")
        
        quality_status = "✅ MAKES SENSE" if quality["makes_sense"] else "⚠️  NEEDS REVIEW"
        print(f"   {quality_status} (Score: {quality['quality_score']:.2f})")
        
        if response_message:
            print(f"   📝 Response: {response_message[:150]}...")
        
        if data_points:
            print(f"   📊 Sample Data: {json.dumps(data_points[0] if data_points else {}, indent=2)[:200]}...")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API Error: {e}")
        return {
            "question_num": question_num,
            "question": question,
            "category": category,
            "success": False,
            "error": str(e),
            "response_time_ms": (time.time() - start_time) * 1000
        }
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "question_num": question_num,
            "question": question,
            "category": category,
            "success": False,
            "error": str(e),
            "response_time_ms": (time.time() - start_time) * 1000
        }

def main():
    """Run tests for all questions."""
    print("=" * 60)
    print("🧪 TESTING NEW QUESTIONS WITH GROQ AI ENHANCEMENT")
    print("=" * 60)
    
    # Load questions
    try:
        questions = load_questions()
        print(f"\n📋 Loaded {len(questions)} questions from {QUESTIONS_FILE}")
    except FileNotFoundError:
        print(f"❌ Error: Questions file not found: {QUESTIONS_FILE}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in questions file: {e}")
        return
    
    # Test each question
    results = []
    total_questions = len(questions)
    
    for idx, q in enumerate(questions, 1):
        result = test_question(
            question=q["question"],
            category=q["category"],
            question_num=idx,
            total=total_questions
        )
        results.append(result)
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
    
    # Calculate statistics
    successful = sum(1 for r in results if r.get("success", False))
    total_tokens = sum(r.get("tokens_used", 0) for r in results)
    cache_hits = sum(1 for r in results if r.get("cache_hit", False))
    avg_response_time = sum(r.get("response_time_ms", 0) for r in results) / len(results) if results else 0
    
    quality_results = [r.get("quality", {}) for r in results if r.get("success", False)]
    makes_sense_count = sum(1 for q in quality_results if q.get("makes_sense", False))
    avg_quality_score = sum(q.get("quality_score", 0) for q in quality_results) / len(quality_results) if quality_results else 0
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎉 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Success Rate: {(successful/total_questions*100):.1f}% ({successful}/{total_questions})")
    print(f"💰 Total Tokens: {total_tokens}")
    print(f"📊 Cache Hit Rate: {(cache_hits/total_questions*100):.1f}%")
    print(f"⏱️  Avg Response Time: {avg_response_time:.1f}ms")
    print(f"\n🎯 RESPONSE QUALITY:")
    print(f"   Quality Rate: {(makes_sense_count/len(quality_results)*100):.1f}% ({makes_sense_count}/{len(quality_results)} make sense)")
    print(f"   Avg Quality Score: {avg_quality_score:.2f}/1.0")
    if makes_sense_count < len(quality_results):
        print(f"   ⚠️  Needs Review: {len(quality_results) - makes_sense_count} responses")
    
    # Write detailed log
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("NEW QUESTIONS TEST RESULTS - GROQ AI ENHANCEMENT\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Questions: {total_questions}\n")
        f.write("=" * 80 + "\n\n")
        
        for result in results:
            f.write(f"\n🔍 Question {result['question_num']}: '{result['question']}'\n")
            f.write(f"   Category: {result['category']}\n")
            f.write(f"   ✅ SUCCESS: {result.get('success', False)}\n")
            f.write(f"   Response time: {result.get('response_time_ms', 0):.1f}ms\n")
            f.write(f"   Tokens used: {result.get('tokens_used', 0)}\n")
            f.write(f"   Cache hit: {result.get('cache_hit', False)}\n")
            f.write(f"   Data points: {result.get('data_points', 0)}\n")
            f.write(f"   Charts: {result.get('charts', 0)}\n")
            
            quality = result.get('quality', {})
            quality_status = "✅ MAKES SENSE" if quality.get('makes_sense', False) else "⚠️  NEEDS REVIEW"
            f.write(f"   {quality_status} (Score: {quality.get('quality_score', 0):.2f})\n")
            
            if quality.get('issues'):
                f.write(f"   Issues: {', '.join(quality['issues'])}\n")
            
            response_message = result.get('response_message', '')
            if response_message:
                f.write(f"   📝 Response Message:\n      {response_message}\n")
            
            sample_data = result.get('sample_data', [])
            if sample_data:
                f.write(f"   📊 Sample Data (first 3 rows):\n")
                for i, row in enumerate(sample_data[:3], 1):
                    f.write(f"      Row {i}: {json.dumps(row, indent=2)}\n")
            
            if result.get('error'):
                f.write(f"   ❌ Error: {result['error']}\n")
            
            f.write("\n" + "-" * 80 + "\n")
        
        f.write(f"\n📊 SUMMARY STATISTICS:\n")
        f.write(f"   Success Rate: {(successful/total_questions*100):.1f}%\n")
        f.write(f"   Total Tokens: {total_tokens}\n")
        f.write(f"   Cache Hit Rate: {(cache_hits/total_questions*100):.1f}%\n")
        f.write(f"   Avg Response Time: {avg_response_time:.1f}ms\n")
        f.write(f"   Quality Rate: {(makes_sense_count/len(quality_results)*100):.1f}%\n")
        f.write(f"   Avg Quality Score: {avg_quality_score:.2f}/1.0\n")
    
    print(f"\n📄 Full results logged to: {LOG_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()

