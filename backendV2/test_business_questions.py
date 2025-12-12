#!/usr/bin/env python3
"""Test the backendV2 API with real business intelligence questions."""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any

class BusinessQuestionTester:
    """Test the BI system with real business questions."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()
        
    def load_questions(self, questions_file: str) -> Dict[str, Any]:
        """Load questions from the JSON file."""
        try:
            with open(questions_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading questions: {e}")
            return {}
    
    def test_single_query(self, query: str, category: str) -> Dict[str, Any]:
        """Test a single query against the API."""
        start_time = time.time()
        
        try:
            # Test basic query endpoint
            payload = {
                "query": query,
                "options": {"include_charts": True}
            }
            
            response = self.session.post(
                f"{self.base_url}/api/query",
                json=payload,
                timeout=30
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    "query": query,
                    "category": category,
                    "success": result.get("success", False),
                    "response_time_ms": response_time,
                    "status_code": response.status_code,
                    "data_points": result.get("metadata", {}).get("data_points", 0),
                    "chart_count": result.get("metadata", {}).get("chart_count", 0),
                    "tokens_used": result.get("metadata", {}).get("tokens_used", 0),
                    "cache_hit": result.get("metadata", {}).get("cache_hit", False),
                    "source": result.get("metadata", {}).get("source", "unknown"),
                    "ai_response": result.get("ai_response", ""),
                    "error": None
                }
            else:
                return {
                    "query": query,
                    "category": category,
                    "success": False,
                    "response_time_ms": response_time,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "query": query,
                "category": category,
                "success": False,
                "response_time_ms": response_time,
                "status_code": 0,
                "error": str(e)
            }
    
    def test_hybrid_analysis(self, query: str, category: str) -> Dict[str, Any]:
        """Test complex queries with hybrid analysis."""
        start_time = time.time()
        
        try:
            payload = {
                "query": query,
                "analysis_type": "auto"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/hybrid-analysis",
                json=payload,
                timeout=30
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    "query": query,
                    "category": category,
                    "success": result.get("success", False),
                    "response_time_ms": response_time,
                    "status_code": response.status_code,
                    "strategy": result.get("strategy", "unknown"),
                    "cache_hit_rate": result.get("performance", {}).get("cache_hit_rate", 0),
                    "token_efficiency": result.get("performance", {}).get("token_efficiency", 0),
                    "execution_time_ms": result.get("performance", {}).get("execution_time_ms", 0),
                    "analysis": str(result.get("analysis", {}))[:200] + "..." if result.get("analysis") else "",
                    "error": None
                }
            else:
                return {
                    "query": query,
                    "category": category,
                    "success": False,
                    "response_time_ms": response_time,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "query": query,
                "category": category,
                "success": False,
                "response_time_ms": response_time,
                "status_code": 0,
                "error": str(e)
            }
    
    def run_comprehensive_test(self, questions_file: str):
        """Run comprehensive test of all business questions."""
        print("🎯 COMPREHENSIVE BUSINESS INTELLIGENCE QUESTION TEST")
        print("=" * 70)
        
        # Load questions
        questions_data = self.load_questions(questions_file)
        if not questions_data:
            print("❌ Failed to load questions file")
            return
        
        total_questions = 0
        successful_responses = 0
        total_tokens = 0
        cache_hits = 0
        
        # Test each category
        for category_name, category_data in questions_data.items():
            print(f"\\n📋 Testing Category: {category_name.replace('_', ' ').title()}")
            print(f"Description: {category_data.get('description', 'N/A')}")
            print("-" * 60)
            
            questions = category_data.get('questions', [])
            category_successful = 0
            
            for i, question in enumerate(questions, 1):
                total_questions += 1
                print(f"\\n🔍 Question {i}: '{question}'")
                
                # Test basic query first
                basic_result = self.test_single_query(question, category_name)
                self.test_results.append(basic_result)
                
                if basic_result["success"]:
                    category_successful += 1
                    successful_responses += 1
                    total_tokens += basic_result.get("tokens_used", 0)
                    
                    if basic_result.get("cache_hit"):
                        cache_hits += 1
                    
                    print(f"✅ SUCCESS ({basic_result.get('source', 'unknown')})")
                    print(f"   Response time: {basic_result['response_time_ms']:.1f}ms")
                    print(f"   Tokens used: {basic_result.get('tokens_used', 0)}")
                    print(f"   Data points: {basic_result.get('data_points', 0)}")
                    print(f"   Charts: {basic_result.get('chart_count', 0)}")
                    
                    if basic_result.get("ai_response"):
                        print(f"   AI Response: {basic_result['ai_response'][:80]}...")
                else:
                    print(f"❌ FAILED: {basic_result.get('error', 'Unknown error')}")
                
                # For complex analytical questions, also test hybrid analysis
                if any(keyword in question.lower() for keyword in ['why', 'explain', 'analyze', 'cause', 'trend']):
                    print(f"   🧠 Testing hybrid analysis...")
                    hybrid_result = self.test_hybrid_analysis(question, category_name)
                    
                    if hybrid_result["success"]:
                        print(f"   ✅ Hybrid analysis: {hybrid_result.get('strategy', 'unknown')} strategy")
                        print(f"   Cache hit rate: {hybrid_result.get('cache_hit_rate', 0):.1f}%")
                        print(f"   Token efficiency: {hybrid_result.get('token_efficiency', 0):.1f}%")
                    else:
                        print(f"   ❌ Hybrid analysis failed: {hybrid_result.get('error', 'Unknown')}")
                
                # Small delay between requests
                time.sleep(0.1)
            
            # Category summary
            success_rate = (category_successful / len(questions) * 100) if questions else 0
            print(f"\\n📊 Category Summary: {category_successful}/{len(questions)} successful ({success_rate:.1f}%)")
        
        # Overall summary
        self._generate_test_report(total_questions, successful_responses, total_tokens, cache_hits)
        
        # Save detailed results
        self._save_results_to_file()
    
    def _generate_test_report(self, total_questions: int, successful_responses: int, 
                            total_tokens: int, cache_hits: int):
        """Generate comprehensive test report."""
        success_rate = (successful_responses / total_questions * 100) if total_questions > 0 else 0
        cache_hit_rate = (cache_hits / total_questions * 100) if total_questions > 0 else 0
        avg_tokens = total_tokens / total_questions if total_questions > 0 else 0
        
        print(f"\\n" + "=" * 70)
        print(f"🎉 COMPREHENSIVE TEST REPORT")
        print("=" * 70)
        
        print(f"\\n📊 OVERALL RESULTS:")
        print(f"   Total Questions Tested: {total_questions}")
        print(f"   Successful Responses: {successful_responses}")
        print(f"   Failed Responses: {total_questions - successful_responses}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\\n⚡ PERFORMANCE METRICS:")
        print(f"   Cache Hit Rate: {cache_hit_rate:.1f}%")
        print(f"   Total Tokens Used: {total_tokens}")
        print(f"   Average Tokens per Query: {avg_tokens:.1f}")
        print(f"   Zero-Token Queries: {cache_hits}")
        
        print(f"\\n🎯 TOKEN OPTIMIZATION ANALYSIS:")
        if cache_hit_rate >= 80:
            print(f"   🔥 EXCELLENT: {cache_hit_rate:.1f}% cache hit rate!")
            print(f"   💰 Major cost savings achieved")
        elif cache_hit_rate >= 60:
            print(f"   ✅ GOOD: {cache_hit_rate:.1f}% cache hit rate")
            print(f"   💡 Room for optimization")
        else:
            print(f"   ⚠️  NEEDS IMPROVEMENT: {cache_hit_rate:.1f}% cache hit rate")
            print(f"   🔧 Consider expanding cached patterns")
        
        print(f"\\n📈 BUSINESS INTELLIGENCE COVERAGE:")
        
        # Analyze by category
        category_stats = {}
        for result in self.test_results:
            category = result["category"]
            if category not in category_stats:
                category_stats[category] = {"total": 0, "successful": 0}
            
            category_stats[category]["total"] += 1
            if result["success"]:
                category_stats[category]["successful"] += 1
        
        for category, stats in category_stats.items():
            success_pct = (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0
            status = "✅" if success_pct >= 70 else "⚠️" if success_pct >= 50 else "❌"
            print(f"   {status} {category.replace('_', ' ').title()}: {success_pct:.1f}% ({stats['successful']}/{stats['total']})")
        
        if success_rate >= 80:
            print(f"\\n🎊 EXCELLENT PERFORMANCE!")
            print(f"   🚀 System ready for production deployment")
            print(f"   💼 Comprehensive BI question coverage achieved")
        elif success_rate >= 60:
            print(f"\\n✅ GOOD PERFORMANCE!")
            print(f"   📈 System handles most business questions well")
            print(f"   🔧 Minor optimizations recommended")
        else:
            print(f"\\n⚠️  NEEDS ATTENTION!")
            print(f"   🔧 System requires optimization for better coverage")
            print(f"   📋 Review failed queries for pattern improvements")
    
    def _save_results_to_file(self):
        """Save detailed test results to a log file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"business_questions_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "test_metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "total_questions": len(self.test_results),
                        "successful_responses": sum(1 for r in self.test_results if r["success"]),
                        "base_url": self.base_url
                    },
                    "detailed_results": self.test_results
                }, f, indent=2)
            
            print(f"\\n💾 Detailed results saved to: {filename}")
            
        except Exception as e:
            print(f"\\n❌ Failed to save results: {e}")

def main():
    """Main test execution."""
    print("🚀 Starting Business Intelligence Question Testing...")
    print("📝 Testing against backendV2 API server")
    print()
    
    # Wait a moment for server to be fully ready
    time.sleep(2)
    
    tester = BusinessQuestionTester()
    
    # Test server connectivity first
    try:
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server connectivity confirmed")
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Server connectivity failed: {e}")
        print("💡 Make sure the API server is running on localhost:8001")
        return
    
    # Run comprehensive test
    questions_file = "../backend/questions.txt"
    tester.run_comprehensive_test(questions_file)

if __name__ == "__main__":
    main()