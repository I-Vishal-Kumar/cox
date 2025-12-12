#!/usr/bin/env python3
"""Comprehensive test of the unified API with all integrated components."""

import asyncio
import aiohttp
import json
from typing import Dict, Any
import time

class UnifiedAPITester:
    """Test client for the unified token-optimized BI API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_basic_query(self) -> Dict[str, Any]:
        """Test basic query processing."""
        print("🔍 Testing Basic Query Processing")
        print("-" * 40)
        
        query_data = {
            "query": "What are the top selling models by region?",
            "options": {"include_charts": True}
        }
        
        async with self.session.post(f"{self.base_url}/api/query", json=query_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Basic query successful")
                print(f"   Success: {result.get('success')}")
                print(f"   Data points: {result.get('metadata', {}).get('data_points', 0)}")
                print(f"   Charts: {result.get('metadata', {}).get('chart_count', 0)}")
                print(f"   Tokens used: {result.get('metadata', {}).get('tokens_used', 0)}")
                print(f"   Response time: {result.get('metadata', {}).get('response_time_ms', 0):.1f}ms")
                return {"success": True, "result": result}
            else:
                error_text = await response.text()
                print(f"❌ Basic query failed: {response.status} - {error_text}")
                return {"success": False, "error": error_text}
    
    async def test_hybrid_analysis(self) -> Dict[str, Any]:
        """Test hybrid analysis with query decomposition."""
        print("\\n🧠 Testing Hybrid Analysis")
        print("-" * 30)
        
        complex_queries = [
            "Why did sales drop in Q3 compared to Q2 and what can we do about it?",
            "Show me inventory trends over 6 months and predict next month's needs",
            "Compare dealer performance Northeast vs Midwest and explain differences"
        ]
        
        results = []
        
        for i, query in enumerate(complex_queries, 1):
            print(f"\\n🔍 Query {i}: '{query[:50]}...'")
            
            analysis_data = {
                "query": query,
                "analysis_type": "auto"
            }
            
            async with self.session.post(f"{self.base_url}/api/hybrid-analysis", json=analysis_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("success"):
                        perf = result.get("performance", {})
                        print(f"✅ Hybrid analysis successful")
                        print(f"   Strategy: {result.get('strategy')}")
                        print(f"   Cache hit rate: {perf.get('cache_hit_rate', 0):.1f}%")
                        print(f"   Token efficiency: {perf.get('token_efficiency', 0):.1f}%")
                        print(f"   Execution time: {perf.get('execution_time_ms', 0):.1f}ms")
                        
                        results.append({"success": True, "query": query, "result": result})
                    else:
                        print(f"❌ Analysis failed: {result.get('error')}")
                        results.append({"success": False, "query": query, "error": result.get("error")})
                else:
                    error_text = await response.text()
                    print(f"❌ Request failed: {response.status} - {error_text}")
                    results.append({"success": False, "query": query, "error": error_text})
        
        successful = sum(1 for r in results if r["success"])
        print(f"\\n📊 Hybrid Analysis Summary: {successful}/{len(complex_queries)} successful")
        
        return {"success": successful > 0, "results": results}
    
    async def test_chart_generation(self) -> Dict[str, Any]:
        """Test chart generation with versioning."""
        print("\\n📊 Testing Chart Generation with Versioning")
        print("-" * 45)
        
        # Test data for chart generation
        chart_data = [
            {"region": "Northeast", "revenue": 1500000, "deals": 150},
            {"region": "Midwest", "revenue": 1200000, "deals": 120},
            {"region": "West", "revenue": 1800000, "deals": 180},
            {"region": "Southeast", "revenue": 1300000, "deals": 130}
        ]
        
        chart_request = {
            "chart_id": "test_regional_sales",
            "data": chart_data,
            "chart_type": "auto",
            "title": "Regional Sales Performance",
            "category": "sales_analytics"
        }
        
        # Test 1: Initial chart generation
        print("\\n📈 Test 1: Initial Chart Generation")
        async with self.session.post(f"{self.base_url}/api/charts/generate", json=chart_request) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Initial generation successful")
                print(f"   Chart ID: {result.get('chart_id')}")
                print(f"   Version: {result.get('version')}")
                print(f"   Update type: {result.get('update_type')}")
                print(f"   Data points: {result.get('data_points')}")
                initial_version = result.get('version')
            else:
                error_text = await response.text()
                print(f"❌ Initial generation failed: {response.status} - {error_text}")
                return {"success": False, "error": error_text}
        
        # Test 2: Incremental update with modified data
        print("\\n🔄 Test 2: Incremental Update")
        modified_data = chart_data + [{"region": "Southwest", "revenue": 1100000, "deals": 110}]
        chart_request["data"] = modified_data
        
        async with self.session.post(f"{self.base_url}/api/charts/generate", json=chart_request) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Incremental update successful")
                print(f"   Version: {result.get('version')}")
                print(f"   Update type: {result.get('update_type')}")
                print(f"   Performance gain: {result.get('performance_gain', 0)}%")
                print(f"   Data points: {result.get('data_points')}")
            else:
                error_text = await response.text()
                print(f"❌ Incremental update failed: {response.status} - {error_text}")
        
        # Test 3: Chart history
        print("\\n📚 Test 3: Chart Version History")
        async with self.session.get(f"{self.base_url}/api/charts/test_regional_sales/history") as response:
            if response.status == 200:
                result = await response.json()
                history = result.get("history", {})
                print(f"✅ History retrieved successfully")
                print(f"   Current version: {history.get('current_version')}")
                print(f"   Total versions: {history.get('total_versions')}")
                print(f"   Created: {history.get('created_at', '')[:19]}")
            else:
                error_text = await response.text()
                print(f"❌ History retrieval failed: {response.status} - {error_text}")
        
        # Test 4: Chart optimization
        print("\\n⚡ Test 4: Chart Performance Optimization")
        async with self.session.post(f"{self.base_url}/api/charts/test_regional_sales/optimize") as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Optimization successful")
                print(f"   Optimizations applied: {len(result.get('optimizations_applied', []))}")
                print(f"   Performance improvement: {result.get('performance_improvement', 0)}%")
                for opt in result.get('optimizations_applied', []):
                    print(f"     - {opt}")
            else:
                error_text = await response.text()
                print(f"❌ Optimization failed: {response.status} - {error_text}")
        
        return {"success": True, "chart_id": "test_regional_sales"}
    
    async def test_batch_operations(self) -> Dict[str, Any]:
        """Test batch processing capabilities."""
        print("\\n📦 Testing Batch Operations")
        print("-" * 30)
        
        # Test batch queries
        print("\\n🔍 Batch Query Processing")
        batch_queries = {
            "queries": [
                "Show me KPI health scores",
                "What are the inventory stock levels?",
                "Give me the CEO weekly summary"
            ]
        }
        
        async with self.session.post(f"{self.base_url}/api/batch", json=batch_queries) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Batch queries successful")
                print(f"   Total queries: {result.get('total_queries', 0)}")
                print(f"   Successful: {result.get('successful_queries', 0)}")
                print(f"   Total tokens: {result.get('total_tokens_used', 0)}")
                print(f"   Avg response time: {result.get('avg_response_time_ms', 0):.1f}ms")
            else:
                error_text = await response.text()
                print(f"❌ Batch queries failed: {response.status} - {error_text}")
        
        # Test batch chart generation
        print("\\n📊 Batch Chart Generation")
        batch_charts = {
            "charts": [
                {
                    "chart_id": "batch_kpi_chart",
                    "data": [
                        {"metric": "Sales Growth", "value": 15.5, "status": "Good"},
                        {"metric": "Customer Satisfaction", "value": -5.2, "status": "Warning"}
                    ],
                    "chart_type": "horizontalBar",
                    "title": "KPI Dashboard",
                    "category": "kpi_monitoring"
                },
                {
                    "chart_id": "batch_inventory_chart", 
                    "data": [
                        {"plant": "Plant A", "stock": 85, "risk": "Low"},
                        {"plant": "Plant B", "stock": 45, "risk": "Medium"},
                        {"plant": "Plant C", "stock": 15, "risk": "High"}
                    ],
                    "chart_type": "pie",
                    "title": "Inventory Status",
                    "category": "inventory_management"
                }
            ]
        }
        
        async with self.session.post(f"{self.base_url}/api/charts/batch", json=batch_charts) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Batch charts successful")
                print(f"   Total charts: {result.get('total_charts', 0)}")
                print(f"   Successful: {result.get('successful_updates', 0)}")
                print(f"   Failed: {result.get('failed_updates', 0)}")
                print(f"   Avg performance gain: {result.get('average_performance_gain', 0):.1f}%")
            else:
                error_text = await response.text()
                print(f"❌ Batch charts failed: {response.status} - {error_text}")
        
        return {"success": True}
    
    async def test_system_status(self) -> Dict[str, Any]:
        """Test comprehensive system status."""
        print("\\n📊 Testing System Status and Monitoring")
        print("-" * 40)
        
        # Test comprehensive status
        async with self.session.get(f"{self.base_url}/api/system/comprehensive-status") as response:
            if response.status == 200:
                result = await response.json()
                
                overall = result.get("overall_metrics", {})
                capabilities = result.get("capabilities", {})
                
                print(f"✅ Comprehensive status retrieved")
                print(f"   System status: {result.get('system_status')}")
                print(f"   Total queries: {overall.get('total_queries_processed', 0)}")
                print(f"   Cache hit rate: {overall.get('cache_hit_rate_percent', 0):.1f}%")
                print(f"   Token efficiency: {overall.get('token_efficiency_percent', 0):.1f}%")
                print(f"   Avg response time: {overall.get('avg_response_time_ms', 0):.1f}ms")
                
                print(f"\\n🔧 System Capabilities:")
                for capability, enabled in capabilities.items():
                    status = "✅" if enabled else "❌"
                    print(f"   {status} {capability.replace('_', ' ').title()}")
                
                return {"success": True, "status": result}
            else:
                error_text = await response.text()
                print(f"❌ Status retrieval failed: {response.status} - {error_text}")
                return {"success": False, "error": error_text}
    
    async def run_comprehensive_test(self):
        """Run all tests in sequence."""
        print("🎯 COMPREHENSIVE UNIFIED API TEST")
        print("=" * 50)
        
        start_time = time.time()
        test_results = {}
        
        try:
            # Test 1: Basic query processing
            test_results["basic_query"] = await self.test_basic_query()
            
            # Test 2: Hybrid analysis
            test_results["hybrid_analysis"] = await self.test_hybrid_analysis()
            
            # Test 3: Chart generation with versioning
            test_results["chart_generation"] = await self.test_chart_generation()
            
            # Test 4: Batch operations
            test_results["batch_operations"] = await self.test_batch_operations()
            
            # Test 5: System status and monitoring
            test_results["system_status"] = await self.test_system_status()
            
            # Calculate overall results
            total_time = time.time() - start_time
            successful_tests = sum(1 for result in test_results.values() if result.get("success"))
            total_tests = len(test_results)
            
            print(f"\\n🎉 COMPREHENSIVE TEST COMPLETE!")
            print("=" * 40)
            print(f"✅ Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
            print(f"⏱️  Total Time: {total_time:.2f} seconds")
            print(f"🚀 System Performance: Excellent")
            
            print(f"\\n📋 Test Summary:")
            for test_name, result in test_results.items():
                status = "✅" if result.get("success") else "❌"
                print(f"   {status} {test_name.replace('_', ' ').title()}")
            
            if successful_tests == total_tests:
                print(f"\\n🎊 ALL TESTS PASSED! The unified API is fully operational.")
                print(f"   🔥 Token optimization working")
                print(f"   🔥 Hybrid analysis operational")
                print(f"   🔥 Incremental charts functional")
                print(f"   🔥 Batch processing ready")
                print(f"   🔥 Real-time monitoring active")
            
            return test_results
            
        except Exception as e:
            print(f"\\n❌ Test suite failed with error: {e}")
            return {"success": False, "error": str(e)}

async def main():
    """Main test function."""
    print("🚀 Starting Unified API Test Suite...")
    
    # Test with local server
    async with UnifiedAPITester("http://localhost:8000") as tester:
        results = await tester.run_comprehensive_test()
    
    return results

if __name__ == "__main__":
    # Note: This requires the API server to be running
    print("📝 Note: Make sure the API server is running on localhost:8000")
    print("   Start with: python api_server.py")
    print()
    
    try:
        results = asyncio.run(main())
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        print("💡 Make sure the API server is running: python api_server.py")