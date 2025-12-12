#!/usr/bin/env python3
"""Test all business intelligence questions from questions.txt"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

BASE_URL = "http://localhost:8001"
QUESTIONS_FILE = Path("../backend/questions.txt")
LOG_FILE = Path("curl_test_results_20251212_144404.log")

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
    fallback_info = response_data.get('fallback_info', {})
    response_message = fallback_info.get('message', '') or response_data.get('message', '')
    
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
        issues.append("Response message is too short or empty")
    
    # Check if we have data
    if data_points and len(data_points) > 0:
        quality_score += 0.3
        # Check if data has meaningful structure
        if isinstance(data_points[0], dict) and len(data_points[0]) > 0:
            quality_score += 0.2
        else:
            issues.append("Data structure is not meaningful")
    else:
        issues.append("No data points returned")
    
    # Check if response addresses the question
    question_lower = question.lower()
    response_lower = response_message.lower()
    
    # Check for relevant keywords
    question_keywords = set(word for word in question_lower.split() if len(word) > 3)
    response_keywords = set(word for word in response_lower.split() if len(word) > 3)
    
    # Check for domain relevance
    domain_keywords = {
        'sales', 'revenue', 'dealer', 'model', 'vehicle', 'inventory', 'stock',
        'warranty', 'claim', 'repair', 'kpi', 'health', 'score', 'margin',
        'plant', 'factory', 'component', 'battery', 'ev', 'ice', 'performance'
    }
    
    question_domain = question_keywords & domain_keywords
    response_domain = response_keywords & domain_keywords
    
    if question_domain and response_domain:
        overlap = len(question_domain & response_domain)
        if overlap > 0:
            quality_score += 0.2
        else:
            issues.append("Response doesn't address question domain")
    
    # Check for generic/unhelpful responses
    generic_phrases = [
        "i couldn't find", "no data available", "try searching", 
        "not available", "cannot process", "error occurred"
    ]
    
    if any(phrase in response_lower for phrase in generic_phrases):
        quality_score -= 0.3
        issues.append("Response contains generic/unhelpful phrases")
    
    # Determine if makes sense
    makes_sense = quality_score >= 0.5
    
    return {
        'makes_sense': makes_sense,
        'quality_score': min(max(quality_score, 0.0), 1.0),
        'issues': issues,
        'response_message': response_message[:500] if response_message else '',
        'sample_data': data_points[:3] if data_points else []
    }

def test_question(question: str, question_num: int) -> Dict[str, Any]:
    """Test a single question."""
    payload = {
        "query": question,
        "options": {
            "include_charts": True
        }
    }
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json=payload,
            timeout=30
        )
        response_time_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            
            if success:
                metadata = data.get('metadata', {})
                
                # Get full response message from various possible locations
                fallback_info = data.get('fallback_info', {})
                match_info = data.get('match_info', {})
                response_message = (
                    fallback_info.get('message', '') or 
                    match_info.get('description', '') or 
                    data.get('message', '') or
                    ''
                )
                
                # Get data points
                data_obj = data.get('data', {})
                if isinstance(data_obj, dict):
                    data_points = data_obj.get('raw', [])
                elif isinstance(data_obj, list):
                    data_points = data_obj
                else:
                    data_points = []
                
                # Evaluate response quality
                quality = evaluate_response_quality(question, {
                    'message': response_message,
                    'data': {'raw': data_points},
                    'fallback_info': fallback_info,
                    'match_info': match_info
                })
                
                return {
                    'success': True,
                    'http_status': 200,
                    'response_time_ms': response_time_ms,
                    'tokens_used': metadata.get('tokens_used', 0),
                    'cache_hit': metadata.get('cache_hit', False),
                    'data_points': len(data_points),
                    'charts': len(data.get('charts', [])) if data.get('charts') else (1 if data.get('chart_config') else 0),
                    'response_message': response_message,
                    'sample_data': data_points[:3] if data_points else [],
                    'source': metadata.get('source', 'unknown'),
                    'fallback_type': metadata.get('fallback_type', 'unknown'),
                    'quality': quality
                }
            else:
                return {
                    'success': False,
                    'http_status': 200,
                    'response_time_ms': response_time_ms,
                    'error': data.get('error', 'Unknown error')
                }
        else:
            return {
                'success': False,
                'http_status': response.status_code,
                'response_time_ms': response_time_ms,
                'error': f'HTTP {response.status_code}'
            }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'http_status': 0,
            'response_time_ms': (time.time() - start_time) * 1000,
            'error': str(e)
        }

def main():
    """Main test function."""
    print("🎯 BUSINESS INTELLIGENCE API TESTING")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check server health
    print("🔍 Checking server health...")
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✅ Server is healthy and responding")
        else:
            print(f"❌ Server health check failed (HTTP {health.status_code})")
            return
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return
    
    # Load questions
    print("\n📋 Loading business intelligence questions...")
    questions = load_questions()
    print(f"Loaded {len(questions)} questions from questions.txt")
    
    # Initialize counters
    total_questions = len(questions)
    successful_queries = 0
    cache_hits = 0
    total_tokens = 0
    total_response_time = 0
    quality_responses = 0  # Responses that make sense
    quality_scores = []
    
    # Open log file
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write("🎯 BUSINESS INTELLIGENCE API TESTING WITH CURL\n")
        log.write("=\n")
        log.write(f"Testing backendV2 API server with real business questions\n")
        log.write(f"Base URL: {BASE_URL}\n")
        log.write(f"Log file: {LOG_FILE}\n")
        log.write(f"Started at: {datetime.now().strftime('%a %b %d %I:%M:%S %p %Y')}\n")
        log.write("\n")
        log.write("🔍 Checking server health...\n")
        log.write("✅ Server is healthy and responding\n")
        log.write("\n")
        log.write("📋 Loading business intelligence questions...\n")
        log.write(f"Loaded {len(questions)} questions from 3 categories\n")
        log.write("\n")
        log.write("🚀 Starting API tests...\n")
        log.write("\n")
        
        # Test each question
        for i, q_data in enumerate(questions, 1):
            question = q_data['question']
            category = q_data['category']
            
            print(f"\n🔍 Question {i}: '{question}'")
            print(f"   Category: {category}")
            
            log.write(f"🔍 Question {i}: '{question}'\n")
            log.write(f"   Category: {category}\n")
            
            result = test_question(question, i)
            
            if result['success']:
                successful_queries += 1
                total_tokens += result.get('tokens_used', 0)
                total_response_time += result.get('response_time_ms', 0)
                
                if result.get('cache_hit'):
                    cache_hits += 1
                
                # Evaluate response quality
                quality = result.get('quality', {})
                makes_sense = quality.get('makes_sense', False)
                quality_score = quality.get('quality_score', 0.0)
                response_message = result.get('response_message', '')
                sample_data = result.get('sample_data', [])
                
                if makes_sense:
                    quality_responses += 1
                quality_scores.append(quality_score)
                
                source = result.get('source', 'unknown')
                quality_icon = "✅" if makes_sense else "⚠️"
                quality_text = "MAKES SENSE" if makes_sense else "NEEDS REVIEW"
                
                print(f"   ✅ SUCCESS ({source})")
                print(f"   Response time: {result['response_time_ms']:.1f}ms")
                print(f"   Tokens used: {result.get('tokens_used', 0)}")
                print(f"   Data points: {result.get('data_points', 0)}")
                print(f"   Charts: {result.get('charts', 0)}")
                print(f"   {quality_icon} Quality: {quality_text} (Score: {quality_score:.2f})")
                
                if response_message:
                    print(f"   📝 Response: {response_message[:150]}...")
                
                if sample_data:
                    print(f"   📊 Sample Data: {json.dumps(sample_data[0] if sample_data else {}, indent=2)[:100]}...")
                
                if quality.get('issues'):
                    print(f"   ⚠️  Issues: {', '.join(quality['issues'][:2])}")
                
                log.write(f"   ✅ SUCCESS ({source})\n")
                log.write(f"   Response time: {result['response_time_ms']:.1f}ms\n")
                log.write(f"   Tokens used: {result.get('tokens_used', 0)}\n")
                log.write(f"   Data points: {result.get('data_points', 0)}\n")
                log.write(f"   Charts: {result.get('charts', 0)}\n")
                log.write(f"   {quality_icon} Quality: {quality_text} (Score: {quality_score:.2f})\n")
                
                if response_message:
                    log.write(f"   📝 Response Message:\n")
                    log.write(f"      {response_message}\n")
                
                if sample_data:
                    log.write(f"   📊 Sample Data (first {min(3, len(sample_data))} rows):\n")
                    for idx, row in enumerate(sample_data[:3], 1):
                        log.write(f"      Row {idx}: {json.dumps(row, indent=6)}\n")
                
                if quality.get('issues'):
                    log.write(f"   ⚠️  Quality Issues:\n")
                    for issue in quality['issues']:
                        log.write(f"      - {issue}\n")
            else:
                http_status = result.get('http_status', 0)
                error = result.get('error', 'Unknown error')
                print(f"   ❌ FAILED: HTTP {http_status}")
                print(f"   Error: {error[:100]}")
                
                log.write(f"   ❌ FAILED: HTTP {http_status}\n")
                log.write(f"   Response: {error[:200]}...\n")
            
            log.write("\n")
            
            # Small delay between requests
            time.sleep(0.2)
        
        # Generate summary
        success_rate = (successful_queries / total_questions * 100) if total_questions > 0 else 0
        cache_hit_rate = (cache_hits / total_questions * 100) if total_questions > 0 else 0
        avg_tokens = (total_tokens / total_questions) if total_questions > 0 else 0
        avg_response_time = (total_response_time / total_questions) if total_questions > 0 else 0
        quality_rate = (quality_responses / successful_queries * 100) if successful_queries > 0 else 0
        avg_quality_score = (sum(quality_scores) / len(quality_scores)) if quality_scores else 0.0
        
        log.write("=\n")
        log.write("🎉 CURL TEST SUMMARY REPORT\n")
        log.write("=\n")
        log.write("\n")
        log.write("📊 OVERALL RESULTS:\n")
        log.write(f"   Total Questions Tested: {total_questions}\n")
        log.write(f"   Successful Responses: {successful_queries}\n")
        log.write(f"   Failed Responses: {total_questions - successful_queries}\n")
        log.write(f"   Success Rate: {success_rate:.1f}%\n")
        log.write("\n")
        log.write("⚡ PERFORMANCE METRICS:\n")
        log.write(f"   Cache Hit Rate: {cache_hit_rate:.1f}%\n")
        log.write(f"   Total Tokens Used: {total_tokens}\n")
        log.write(f"   Average Tokens per Query: {avg_tokens:.1f}\n")
        log.write(f"   Zero-Token Queries: {cache_hits}\n")
        log.write(f"   Average Response Time: {avg_response_time:.1f}ms\n")
        log.write("\n")
        log.write("🎯 RESPONSE QUALITY METRICS:\n")
        log.write(f"   Quality Response Rate: {quality_rate:.1f}% ({quality_responses}/{successful_queries})\n")
        log.write(f"   Average Quality Score: {avg_quality_score:.2f}/1.0\n")
        log.write(f"   Responses That Make Sense: {quality_responses}\n")
        log.write(f"   Responses Needing Review: {successful_queries - quality_responses}\n")
        log.write("\n")
        log.write("🎯 TOKEN OPTIMIZATION ANALYSIS:\n")
        
        if cache_hit_rate >= 80:
            log.write(f"   🔥 EXCELLENT: {cache_hit_rate:.1f}% cache hit rate!\n")
            log.write("   💰 Major cost savings achieved\n")
        elif cache_hit_rate >= 60:
            log.write(f"   ✅ GOOD: {cache_hit_rate:.1f}% cache hit rate\n")
            log.write("   💡 Room for optimization\n")
        else:
            log.write(f"   ⚠️  NEEDS IMPROVEMENT: {cache_hit_rate:.1f}% cache hit rate\n")
            log.write("   🔧 Consider expanding cached patterns\n")
        
        log.write("\n")
        
        if success_rate >= 80:
            log.write("🎊 EXCELLENT PERFORMANCE!\n")
            log.write("   🚀 System ready for production deployment\n")
            log.write("   💼 Comprehensive BI question coverage achieved\n")
        elif success_rate >= 60:
            log.write("✅ GOOD PERFORMANCE!\n")
            log.write("   📈 System handles most business questions well\n")
            log.write("   🔧 Minor optimizations recommended\n")
        else:
            log.write("⚠️  NEEDS ATTENTION!\n")
            log.write("   🔧 System requires optimization for better coverage\n")
            log.write("   📋 Review failed queries for pattern improvements\n")
        
        log.write("\n")
        log.write(f"Completed at: {datetime.now().strftime('%a %b %d %I:%M:%S %p %Y')}\n")
        log.write(f"📄 Full results logged to: {LOG_FILE}\n")
        
        # Print summary
        print("\n" + "=" * 50)
        print("🎉 TEST SUMMARY")
        print("=" * 50)
        print(f"✅ Success Rate: {success_rate:.1f}% ({successful_queries}/{total_questions})")
        print(f"💰 Total Tokens: {total_tokens}")
        print(f"📊 Cache Hit Rate: {cache_hit_rate:.1f}%")
        print(f"⏱️  Avg Response Time: {avg_response_time:.1f}ms")
        print(f"\n🎯 RESPONSE QUALITY:")
        print(f"   Quality Rate: {quality_rate:.1f}% ({quality_responses}/{successful_queries} make sense)")
        print(f"   Avg Quality Score: {avg_quality_score:.2f}/1.0")
        print(f"   ⚠️  Needs Review: {successful_queries - quality_responses} responses")
        print(f"\n📄 Full results logged to: {LOG_FILE}")

if __name__ == "__main__":
    main()

