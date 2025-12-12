"""Query routing system that coordinates pattern matching and response generation."""

import time
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from pattern_matcher import QueryPatternMatcher
from fallback_ai import MinimalAIAgent, TokenBudgetManager
from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

class QueryRouter:
    """Main query routing system that handles user queries and returns optimized responses."""
    
    def __init__(self):
        self.pattern_matcher = QueryPatternMatcher()
        self.fallback_ai = MinimalAIAgent()
        self.token_budget = TokenBudgetManager(daily_token_limit=10000)  # 10k tokens per day
        self.query_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "fallback_ai_uses": 0,
            "avg_response_time_ms": 0,
            "last_reset": datetime.now().isoformat()
        }
    
    def process_query(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user query and return the appropriate response.
        
        Args:
            query: User's natural language query
            user_context: Optional context (user role, preferences, etc.)
            
        Returns:
            Dict containing response data, metadata, and performance info
        """
        start_time = time.time()
        
        try:
            # Update stats
            self.query_stats["total_queries"] += 1
            
            # Log query processing
            logger.info(f"Processing query: '{query}'")
            
            # Get response from pattern matcher
            response = self.pattern_matcher.get_response_for_query(query)
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Update response with timing info
            if response.get("success"):
                self.query_stats["cache_hits"] += 1
                
                # Enhance cached response with Grok to make it human-readable
                if self.fallback_ai.use_ai_for_cached and self.fallback_ai.api_key:
                    try:
                        logger.info(f"Enhancing cached response with Groq for query: '{query}'")
                        enhanced = self.fallback_ai.enhance_cached_response(
                            query=query,
                            cached_data=response.get("data", []),
                            category=response.get("match_info", {}).get("category", ""),
                            query_name=response.get("match_info", {}).get("query_name", "")
                        )
                        
                        # Update response with enhanced message
                        if enhanced.get("message"):
                            response["match_info"]["description"] = enhanced["message"]
                        if enhanced.get("tokens_used", 0) > 0:
                            response["metadata"]["tokens_used"] = enhanced["tokens_used"]
                            self.token_budget.use_tokens(enhanced["tokens_used"], query)
                        
                        logger.info(f"Cached response enhanced: {enhanced.get('tokens_used', 0)} tokens used")
                    except Exception as e:
                        logger.warning(f"Failed to enhance cached response: {e}, using original data")
                
                response["metadata"]["response_time_ms"] = response_time_ms
                if "tokens_used" not in response["metadata"]:
                    response["metadata"]["tokens_used"] = 0  # Zero tokens if not enhanced
                response["metadata"]["cache_hit"] = True
                
                logger.info(f"Cache hit for query '{query}' - {response_time_ms:.1f}ms")
            else:
                # Try fallback AI for unmatched queries
                logger.info(f"Cache miss for query '{query}', trying fallback AI...")
                
                # Get available patterns for AI context
                available_patterns = [
                    {"category": category, "description": f"{category.replace('_', ' ').title()} data"}
                    for category in self.pattern_matcher.dump_patterns.keys()
                ]
                
                fallback_response = self.fallback_ai.process_unmatched_query(
                    query=query,
                    available_patterns=available_patterns,
                    user_context=user_context
                )
                
                if fallback_response.get("success"):
                    # Use fallback AI response
                    self.query_stats["fallback_ai_uses"] += 1
                    tokens_used = fallback_response.get("metadata", {}).get("tokens_used", 0)
                    
                    # Record token usage
                    self.token_budget.use_tokens(tokens_used, query)
                    
                    # Extract data from fallback response (should be a list)
                    fallback_data = fallback_response.get("data", [])
                    if not isinstance(fallback_data, list):
                        fallback_data = []
                    
                    response = {
                        "success": True,
                        "query": query,
                        "data": fallback_data,  # Use actual data from fallback AI
                        "chart_config": fallback_response.get("chart_config"),
                        "metadata": {
                            "response_time_ms": response_time_ms,
                            "tokens_used": tokens_used,
                            "cache_hit": False,
                            "fallback_used": True,
                            "fallback_type": fallback_response.get("response_type", "ai_fallback"),
                            "confidence": fallback_response.get("metadata", {}).get("confidence", 0.5)
                        },
                        "match_info": {
                            "category": "ai_generated",
                            "query_name": "fallback_response",
                            "description": fallback_response.get("message", "")[:100],
                            "confidence_score": fallback_response.get("metadata", {}).get("confidence", 0.5)
                        },
                        "fallback_info": {
                            "message": fallback_response.get("message", ""),
                            "suggestions": fallback_response.get("suggestions", []),
                            "confidence": fallback_response.get("metadata", {}).get("confidence", 0.5)
                        }
                    }
                    
                    logger.info(f"Fallback AI response for query '{query}' - {tokens_used} tokens, {len(fallback_data)} data points")
                else:
                    # Fallback failed, return cache miss
                    self.query_stats["cache_misses"] += 1
                    response["metadata"] = {
                        "response_time_ms": response_time_ms,
                        "tokens_used": 0,
                        "cache_hit": False,
                        "fallback_used": False
                    }
                    
                    logger.info(f"Cache miss and fallback failed for query '{query}' - {response_time_ms:.1f}ms")
            
            # Update average response time
            self._update_avg_response_time(response_time_ms)
            
            # Add user context if provided
            if user_context:
                response["user_context"] = user_context
            
            # Add system metadata
            response["system_metadata"] = {
                "timestamp": datetime.now().isoformat(),
                "system": "token-optimized-bi",
                "version": "1.0.0"
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            
            response_time_ms = (time.time() - start_time) * 1000
            self.query_stats["cache_misses"] += 1
            
            return {
                "success": False,
                "error": f"Query processing failed: {str(e)}",
                "query": query,
                "metadata": {
                    "response_time_ms": response_time_ms,
                    "tokens_used": 0,
                    "cache_hit": False
                },
                "system_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "system": "token-optimized-bi",
                    "version": "1.0.0"
                }
            }
    
    def batch_process_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Process multiple queries in batch."""
        logger.info(f"Processing batch of {len(queries)} queries")
        
        results = []
        for i, query in enumerate(queries):
            logger.debug(f"Processing batch query {i+1}/{len(queries)}: '{query}'")
            result = self.process_query(query)
            results.append(result)
        
        return results
    
    def get_query_suggestions(self, partial_query: str = "") -> List[Dict[str, Any]]:
        """Get query suggestions based on available patterns."""
        suggestions = []
        
        # Get pattern stats to understand available data
        stats = self.pattern_matcher.get_pattern_stats()
        
        for category, category_stats in stats.get("categories", {}).items():
            # Get sample patterns from this category
            category_patterns = [
                pattern for pattern in self.pattern_matcher.dump_patterns.values()
                if pattern["category"] == category
            ]
            
            if category_patterns:
                # Pick the pattern with most data
                best_pattern = max(category_patterns, key=lambda x: x["data_size"])
                
                suggestions.append({
                    "category": category,
                    "suggestion": best_pattern["description"],
                    "example_keywords": best_pattern["keywords"][:3],  # Top 3 keywords
                    "data_available": category_stats["total_data_size"] > 0
                })
        
        # If partial query provided, filter suggestions
        if partial_query:
            partial_keywords = self.pattern_matcher.preprocess_query(partial_query)
            filtered_suggestions = []
            
            for suggestion in suggestions:
                # Check if any suggestion keywords match partial query
                if any(pk in ' '.join(suggestion["example_keywords"]) for pk in partial_keywords):
                    filtered_suggestions.append(suggestion)
            
            if filtered_suggestions:
                suggestions = filtered_suggestions
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and performance metrics."""
        pattern_stats = self.pattern_matcher.get_pattern_stats()
        
        # Calculate cache hit rate
        total_queries = self.query_stats["total_queries"]
        cache_hit_rate = (self.query_stats["cache_hits"] / total_queries * 100) if total_queries > 0 else 0
        fallback_usage_rate = (self.query_stats["fallback_ai_uses"] / total_queries * 100) if total_queries > 0 else 0
        
        # Get token budget status
        budget_stats = self.token_budget.get_usage_stats()
        
        return {
            "status": "operational",
            "performance": {
                "total_queries_processed": total_queries,
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                "fallback_ai_usage_percent": round(fallback_usage_rate, 2),
                "avg_response_time_ms": round(self.query_stats["avg_response_time_ms"], 2),
                "cache_hits": self.query_stats["cache_hits"],
                "cache_misses": self.query_stats["cache_misses"],
                "fallback_ai_uses": self.query_stats["fallback_ai_uses"]
            },
            "token_budget": {
                "daily_limit": budget_stats["daily_limit"],
                "current_usage": budget_stats["current_usage"],
                "remaining_budget": budget_stats["remaining_budget"],
                "usage_percentage": round(budget_stats["usage_percentage"], 2),
                "budget_status": budget_stats["budget_status"]
            },
            "data_availability": {
                "total_patterns": pattern_stats["total_patterns"],
                "categories": list(pattern_stats.get("categories", {}).keys()),
                "total_data_points": pattern_stats["total_data_points"]
            },
            "system_info": {
                "version": "1.0.0",
                "last_stats_reset": self.query_stats["last_reset"],
                "current_time": datetime.now().isoformat()
            }
        }
    
    def reset_stats(self) -> None:
        """Reset query statistics."""
        self.query_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "fallback_ai_uses": 0,
            "avg_response_time_ms": 0,
            "last_reset": datetime.now().isoformat()
        }
        logger.info("Query statistics reset")
    
    def refresh_patterns(self) -> bool:
        """Refresh pattern cache (call after dump regeneration)."""
        logger.info("Refreshing pattern cache...")
        success = self.pattern_matcher.refresh_patterns()
        
        if success:
            logger.info("Pattern cache refreshed successfully")
        else:
            logger.error("Failed to refresh pattern cache")
        
        return success
    
    def _update_avg_response_time(self, new_time_ms: float) -> None:
        """Update running average of response times."""
        current_avg = self.query_stats["avg_response_time_ms"]
        total_queries = self.query_stats["total_queries"]
        
        # Calculate new average
        if total_queries == 1:
            self.query_stats["avg_response_time_ms"] = new_time_ms
        else:
            # Running average formula
            self.query_stats["avg_response_time_ms"] = (
                (current_avg * (total_queries - 1) + new_time_ms) / total_queries
            )
    
    def analyze_query_patterns(self, queries: List[str]) -> Dict[str, Any]:
        """Analyze a list of queries to understand usage patterns."""
        analysis = {
            "total_queries": len(queries),
            "category_distribution": {},
            "common_keywords": {},
            "match_success_rate": 0,
            "avg_confidence_score": 0
        }
        
        successful_matches = 0
        total_confidence = 0
        
        for query in queries:
            # Get keywords
            keywords = self.pattern_matcher.preprocess_query(query)
            for keyword in keywords:
                analysis["common_keywords"][keyword] = analysis["common_keywords"].get(keyword, 0) + 1
            
            # Test matching
            match = self.pattern_matcher.route_query(query)
            if match:
                successful_matches += 1
                total_confidence += match["combined_score"]
                
                category = match["category"]
                analysis["category_distribution"][category] = analysis["category_distribution"].get(category, 0) + 1
        
        # Calculate rates
        analysis["match_success_rate"] = (successful_matches / len(queries) * 100) if queries else 0
        analysis["avg_confidence_score"] = (total_confidence / successful_matches) if successful_matches > 0 else 0
        
        # Sort common keywords by frequency
        analysis["common_keywords"] = dict(
            sorted(analysis["common_keywords"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return analysis

# Test functions
def test_query_router():
    """Test the query router system."""
    router = QueryRouter()
    
    print("🧪 Testing Query Router System")
    print("=" * 50)
    
    # Test individual queries
    test_queries = [
        "What were the top selling models in the Northeast last week?",
        "Show me KPI health scores for today",
        "Give me inventory stock levels by plant",
        "CEO weekly summary report",
        "This query should not match anything specific"
    ]
    
    print("\n📋 Individual Query Tests:")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        response = router.process_query(query)
        
        if response["success"]:
            data_points = len(response.get('data', []))
            print(f"✅ Success - {data_points} data points")
            print(f"⏱️  Response time: {response['metadata']['response_time_ms']:.1f}ms")
            
            # Handle both cache hits and fallback responses
            if 'match_info' in response:
                print(f"🎯 Confidence: {response['match_info']['confidence_score']:.3f}")
            elif 'fallback_info' in response:
                print(f"🤖 Fallback AI: {response['fallback_info']['message']}")
                print(f"🎯 Confidence: {response['fallback_info']['confidence']:.3f}")
                print(f"💰 Tokens used: {response['metadata']['tokens_used']}")
        else:
            print(f"❌ Failed: {response['error']}")
    
    # Test batch processing
    print(f"\n📦 Batch Processing Test:")
    batch_results = router.batch_process_queries(test_queries[:3])
    print(f"Processed {len(batch_results)} queries in batch")
    
    # Test suggestions
    print(f"\n💡 Query Suggestions:")
    suggestions = router.get_query_suggestions()
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"{i}. {suggestion['category']}: {suggestion['suggestion']}")
    
    # Test system status
    print(f"\n📊 System Status:")
    status = router.get_system_status()
    print(f"Cache hit rate: {status['performance']['cache_hit_rate_percent']:.1f}%")
    print(f"Avg response time: {status['performance']['avg_response_time_ms']:.1f}ms")
    print(f"Available patterns: {status['data_availability']['total_patterns']}")
    
    # Test query analysis
    print(f"\n🔍 Query Pattern Analysis:")
    analysis = router.analyze_query_patterns(test_queries)
    print(f"Match success rate: {analysis['match_success_rate']:.1f}%")
    print(f"Avg confidence: {analysis['avg_confidence_score']:.3f}")
    print(f"Top keywords: {list(analysis['common_keywords'].keys())[:5]}")

if __name__ == "__main__":
    test_query_router()