#!/usr/bin/env python3
"""Test client for the Token-Optimized BI API."""

import requests
import json
import time
from typing import Dict, Any

class TokenOptimizedBIClient:
    """Client for testing the Token-Optimized BI API."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def query(self, query: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a query to the BI system."""
        payload = {"query": query}
        if options:
            payload["options"] = options
        
        response = self.session.post(f"{self.base_url}/api/query", json=payload)
        return response.json()
    
    def batch_query(self, queries: list, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send multiple queries in batch."""
        payload = {"queries": queries}
        if options:
            payload["options"] = options
        
        response = self.session.post(f"{self.base_url}/api/batch", json=payload)
        return response.json()
    
    def get_suggestions(self, partial_query: str = "") -> Dict[str, Any]:
        """Get query suggestions."""
        params = {"partial_query": partial_query} if partial_query else {}
        response = self.session.get(f"{self.base_url}/api/suggestions", params=params)
        return response.json()
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        response = self.session.get(f"{self.base_url}/api/status")
        return response.json()
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get system capabilities."""
        response = self.session.get(f"{self.base_url}/api/capabilities")
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check system health."""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()

def test_api_comprehensive():
    """Comprehensive API testing."""
    print("🧪 Testing Token-Optimized BI API")
    print("=" * 50)
    
    client = TokenOptimizedBIClient()
    
    # Test health check first
    print("\n🏥 Health Check:")
    try:
        health = client.health_check()
        print(f"Status: {health.get('status', 'unknown')}")
        if health.get('checks'):
            for check, result in health['checks'].items():
                status = "✅" if result else "❌"
                print(f"  {status} {check}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test system status
    print("\n📊 System Status:")
    try:
        status = client.get_status()
        perf = status.get('performance', {})
        print(f"Cache hit rate: {perf.get('cache_hit_rate_percent', 0):.1f}%")
        print(f"Avg response time: {perf.get('avg_response_time_ms', 0):.1f}ms")
        print(f"Available patterns: {status.get('data', {}).get('available_patterns', 0)}")
    except Exception as e:
        print(f"❌ Status check failed: {e}")
    
    # Test capabilities
    print("\n🔧 System Capabilities:")
    try:
        capabilities = client.get_capabilities()
        caps = capabilities.get('capabilities', {})
        print(f"Chart types: {len(caps.get('supported_chart_types', []))}")
        print(f"Interactive features: {len(caps.get('interactive_features', []))}")
        print(f"Export formats: {caps.get('export_formats', [])}")
    except Exception as e:
        print(f"❌ Capabilities check failed: {e}")
    
    # Test individual queries
    print("\n🔍 Individual Query Tests:")
    test_queries = [
        "What were the top selling models in the Northeast last week?",
        "Show me KPI health scores",
        "Give me inventory stock levels by plant",
        "CEO weekly summary",
        "This should not match anything"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            start_time = time.time()
            result = client.query(query)
            response_time = (time.time() - start_time) * 1000
            
            if result.get("success"):
                metadata = result.get("metadata", {})
                print(f"✅ Success - {metadata.get('data_points', 0)} data points")
                print(f"⏱️  Response time: {response_time:.1f}ms")
                print(f"📊 Charts: {metadata.get('chart_count', 0)}")
                print(f"🎯 Confidence: {result.get('match_info', {}).get('confidence_score', 0):.3f}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    # Test query with options
    print(f"\n⚙️  Query with Options:")
    try:
        options = {
            "chart_types": ["bar", "pie"],
            "filters": {"region": "Northeast"}
        }
        result = client.query("top selling models by region", options)
        if result.get("success"):
            print(f"✅ With options: {result['metadata']['chart_count']} charts generated")
        else:
            print(f"❌ Options query failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ Options query failed: {e}")
    
    # Test batch queries
    print(f"\n📦 Batch Query Test:")
    try:
        batch_queries = [
            "top selling models",
            "KPI health scores", 
            "inventory levels"
        ]
        result = client.batch_query(batch_queries)
        if result.get("success"):
            batch_meta = result.get("batch_metadata", {})
            print(f"✅ Batch processed: {result['total_queries']} queries")
            print(f"📊 Total data points: {batch_meta.get('total_data_points', 0)}")
            print(f"📈 Total charts: {batch_meta.get('total_charts', 0)}")
        else:
            print(f"❌ Batch failed")
    except Exception as e:
        print(f"❌ Batch query failed: {e}")
    
    # Test suggestions
    print(f"\n💡 Query Suggestions:")
    try:
        suggestions = client.get_suggestions()
        if suggestions.get("success"):
            for i, suggestion in enumerate(suggestions.get("suggestions", [])[:3], 1):
                print(f"{i}. {suggestion.get('category', 'Unknown')}: {suggestion.get('suggestion', 'N/A')}")
        else:
            print("❌ Failed to get suggestions")
    except Exception as e:
        print(f"❌ Suggestions failed: {e}")
    
    print(f"\n🎉 API Testing Complete!")

if __name__ == "__main__":
    test_api_comprehensive()