"""Fallback AI system with minimal token usage for unmatched queries."""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

class MinimalAIAgent:
    """Ultra-lightweight AI agent for handling unmatched queries with minimal token usage."""
    
    def __init__(self):
        self.max_tokens_per_query = 50  # Hard limit
        self.system_prompt_tokens = 30  # Reserved for system prompt
        self.response_tokens = 20       # Reserved for response
        
        # Template responses for common unmatched query patterns
        self.response_templates = {
            "data_request": "I found related data about {topic}. Try: '{suggestion}'",
            "comparison": "For comparisons, try: '{suggestion1}' or '{suggestion2}'",
            "trend_analysis": "For trend analysis, try: '{suggestion}'",
            "general_help": "I can help with: {available_categories}. Try: '{suggestion}'",
            "clarification": "Could you be more specific? Available data: {categories}"
        }
        
        # Common query patterns and their suggested redirections
        self.query_patterns = {
            "revenue": ["dealer performance", "margin analysis", "CEO weekly summary"],
            "sales": ["top selling models by region", "dealer performance"],
            "inventory": ["inventory stock levels", "stockout risks"],
            "warranty": ["warranty claims by model", "repeat repairs"],
            "kpi": ["KPI health scores", "variance reports"],
            "performance": ["dealer performance", "KPI health scores"],
            "analysis": ["margin analysis", "variance reports"],
            "summary": ["CEO weekly summary", "margin analysis"],
            "trend": ["dealer performance", "KPI health scores"],
            "comparison": ["margin analysis", "dealer performance"]
        }
    
    def process_unmatched_query(
        self, 
        query: str, 
        available_patterns: List[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an unmatched query with minimal token usage.
        
        Args:
            query: The unmatched user query
            available_patterns: Available data patterns for suggestions
            user_context: Optional user context
            
        Returns:
            Response with suggestions and minimal AI processing
        """
        start_time = time.time()
        
        try:
            # First, try template-based response (0 tokens)
            template_response = self._try_template_response(query, available_patterns)
            
            if template_response:
                response_time = (time.time() - start_time) * 1000
                logger.info(f"Template response for unmatched query: '{query}' - {response_time:.1f}ms, 0 tokens")
                
                return {
                    "success": True,
                    "query": query,
                    "response_type": "template",
                    "message": template_response["message"],
                    "suggestions": template_response["suggestions"],
                    "metadata": {
                        "tokens_used": 0,
                        "response_time_ms": response_time,
                        "fallback_type": "template",
                        "confidence": template_response.get("confidence", 0.7)
                    }
                }
            
            # If template fails, use minimal AI (up to 50 tokens)
            ai_response = self._minimal_ai_response(query, available_patterns, user_context)
            
            response_time = (time.time() - start_time) * 1000
            tokens_used = ai_response.get("tokens_used", self.max_tokens_per_query)
            
            logger.info(f"AI fallback for unmatched query: '{query}' - {response_time:.1f}ms, {tokens_used} tokens")
            
            return {
                "success": True,
                "query": query,
                "response_type": "ai_fallback",
                "message": ai_response["message"],
                "suggestions": ai_response["suggestions"],
                "metadata": {
                    "tokens_used": tokens_used,
                    "response_time_ms": response_time,
                    "fallback_type": "ai_minimal",
                    "confidence": ai_response.get("confidence", 0.5)
                }
            }
            
        except Exception as e:
            logger.error(f"Fallback AI processing failed: {e}")
            
            # Ultimate fallback - static response (0 tokens)
            return self._static_fallback_response(query, available_patterns)
    
    def _try_template_response(
        self, 
        query: str, 
        available_patterns: List[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Try to generate a response using templates (0 tokens)."""
        query_lower = query.lower()
        
        # Extract keywords from query
        keywords = self._extract_keywords(query_lower)
        
        # Find matching patterns
        matched_patterns = []
        for keyword in keywords:
            if keyword in self.query_patterns:
                matched_patterns.extend(self.query_patterns[keyword])
        
        if not matched_patterns:
            return None
        
        # Remove duplicates and get top suggestions
        suggestions = list(dict.fromkeys(matched_patterns))[:3]
        
        # Determine response type based on query content
        if any(word in query_lower for word in ["compare", "vs", "versus", "difference"]):
            template_type = "comparison"
            message = self.response_templates["comparison"].format(
                suggestion1=suggestions[0] if suggestions else "dealer performance",
                suggestion2=suggestions[1] if len(suggestions) > 1 else "margin analysis"
            )
        elif any(word in query_lower for word in ["trend", "over time", "change", "growth"]):
            template_type = "trend_analysis"
            message = self.response_templates["trend_analysis"].format(
                suggestion=suggestions[0] if suggestions else "dealer performance"
            )
        elif any(word in query_lower for word in ["what", "show", "give", "get"]):
            template_type = "data_request"
            topic = self._extract_main_topic(query_lower, keywords)
            message = self.response_templates["data_request"].format(
                topic=topic,
                suggestion=suggestions[0] if suggestions else "available data categories"
            )
        else:
            template_type = "general_help"
            categories = self._get_available_categories(available_patterns)
            message = self.response_templates["general_help"].format(
                available_categories=", ".join(categories[:3]),
                suggestion=suggestions[0] if suggestions else "KPI health scores"
            )
        
        return {
            "message": message,
            "suggestions": suggestions,
            "template_type": template_type,
            "confidence": 0.7 if suggestions else 0.5
        }
    
    def _minimal_ai_response(
        self, 
        query: str, 
        available_patterns: List[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate minimal AI response (simulated - would use actual LLM with 50 token limit).
        
        In a real implementation, this would call an LLM with a very short system prompt.
        """
        # Simulate minimal AI processing
        # In production, this would be:
        # response = llm.generate(
        #     system_prompt="Help user find relevant BI data. Max 20 words.",
        #     user_query=query,
        #     max_tokens=20
        # )
        
        keywords = self._extract_keywords(query.lower())
        categories = self._get_available_categories(available_patterns)
        
        # Simulate AI response generation
        if any(word in query.lower() for word in ["why", "reason", "cause"]):
            message = f"For analysis of '{' '.join(keywords[:2])}', try our available reports."
            suggestions = ["margin analysis", "variance reports", "dealer performance"]
        elif any(word in query.lower() for word in ["how", "what", "show"]):
            message = f"I can show data about {categories[0] if categories else 'business metrics'}."
            suggestions = [f"{categories[0]} data" if categories else "KPI health scores"]
        else:
            message = f"Try searching for: {', '.join(keywords[:2])} in our available data."
            suggestions = categories[:2] if categories else ["KPI health scores", "dealer performance"]
        
        # Simulate token usage (system prompt + response)
        estimated_tokens = len(message.split()) + self.system_prompt_tokens
        
        return {
            "message": message,
            "suggestions": suggestions[:3],
            "tokens_used": min(estimated_tokens, self.max_tokens_per_query),
            "confidence": 0.6
        }
    
    def _static_fallback_response(
        self, 
        query: str, 
        available_patterns: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Ultimate fallback response (0 tokens)."""
        categories = self._get_available_categories(available_patterns)
        
        return {
            "success": True,
            "query": query,
            "response_type": "static_fallback",
            "message": "I couldn't find specific data for your query. Here are some available options:",
            "suggestions": categories[:3] if categories else [
                "KPI health scores",
                "dealer performance", 
                "inventory stock levels"
            ],
            "metadata": {
                "tokens_used": 0,
                "response_time_ms": 0,
                "fallback_type": "static",
                "confidence": 0.3
            }
        }
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from query."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'what', 'where', 'when', 'why', 'how', 'who', 'which', 'that', 'this',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me',
            'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their',
            'show', 'give', 'get', 'tell', 'find', 'see', 'look'
        }
        
        words = [word for word in query.split() if word and word not in stop_words and len(word) > 2]
        return words[:5]  # Limit to top 5 keywords
    
    def _extract_main_topic(self, query: str, keywords: List[str]) -> str:
        """Extract the main topic from the query."""
        # Business domain mapping
        domain_keywords = {
            "sales": ["sales", "selling", "revenue", "deals", "transactions"],
            "inventory": ["inventory", "stock", "warehouse", "supply"],
            "warranty": ["warranty", "claims", "repairs", "defects"],
            "performance": ["performance", "metrics", "kpi", "scores"],
            "financial": ["financial", "margin", "profit", "cost", "budget"]
        }
        
        for domain, domain_words in domain_keywords.items():
            if any(word in query for word in domain_words):
                return domain
        
        # Fallback to first meaningful keyword
        return keywords[0] if keywords else "business data"
    
    def _get_available_categories(self, available_patterns: List[Dict[str, Any]] = None) -> List[str]:
        """Get list of available data categories."""
        if available_patterns:
            categories = list(set(pattern.get("category", "").replace("_", " ").title() 
                                for pattern in available_patterns))
            return [cat for cat in categories if cat]
        
        # Default categories
        return [
            "Sales Analytics",
            "KPI Monitoring", 
            "Inventory Management",
            "Warranty Analysis",
            "Executive Reports"
        ]
    
    def get_token_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics for the fallback system."""
        return {
            "max_tokens_per_query": self.max_tokens_per_query,
            "system_prompt_tokens": self.system_prompt_tokens,
            "response_tokens": self.response_tokens,
            "template_responses": len(self.response_templates),
            "query_patterns": len(self.query_patterns),
            "zero_token_fallbacks": ["template", "static"],
            "minimal_token_fallbacks": ["ai_minimal"]
        }

class TokenBudgetManager:
    """Manages token budget and usage tracking for the fallback system."""
    
    def __init__(self, daily_token_limit: int = 10000):
        self.daily_token_limit = daily_token_limit
        self.current_usage = 0
        self.usage_history = []
        self.last_reset = datetime.now().date()
    
    def can_use_tokens(self, requested_tokens: int) -> bool:
        """Check if we can use the requested number of tokens."""
        self._check_daily_reset()
        return (self.current_usage + requested_tokens) <= self.daily_token_limit
    
    def use_tokens(self, tokens_used: int, query: str = "") -> bool:
        """Record token usage."""
        self._check_daily_reset()
        
        if not self.can_use_tokens(tokens_used):
            logger.warning(f"Token budget exceeded: requested {tokens_used}, available {self.daily_token_limit - self.current_usage}")
            return False
        
        self.current_usage += tokens_used
        self.usage_history.append({
            "timestamp": datetime.now().isoformat(),
            "tokens_used": tokens_used,
            "query": query[:100],  # Truncate for privacy
            "remaining_budget": self.daily_token_limit - self.current_usage
        })
        
        logger.info(f"Token usage: {tokens_used} tokens, remaining budget: {self.daily_token_limit - self.current_usage}")
        return True
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        self._check_daily_reset()
        
        return {
            "daily_limit": self.daily_token_limit,
            "current_usage": self.current_usage,
            "remaining_budget": self.daily_token_limit - self.current_usage,
            "usage_percentage": (self.current_usage / self.daily_token_limit * 100),
            "queries_today": len(self.usage_history),
            "last_reset": self.last_reset.isoformat(),
            "budget_status": "healthy" if self.current_usage < self.daily_token_limit * 0.8 else "warning"
        }
    
    def _check_daily_reset(self):
        """Reset usage if it's a new day."""
        today = datetime.now().date()
        if today > self.last_reset:
            logger.info(f"Daily token budget reset: {self.current_usage} tokens used yesterday")
            self.current_usage = 0
            self.usage_history = []
            self.last_reset = today

# Test functions
def test_fallback_ai():
    """Test the fallback AI system."""
    print("🧪 Testing Fallback AI System")
    print("=" * 50)
    
    ai_agent = MinimalAIAgent()
    budget_manager = TokenBudgetManager(daily_token_limit=1000)
    
    # Test queries that should not match existing patterns
    test_queries = [
        "Why did sales drop in Q3?",
        "Compare our performance to competitors",
        "What's the weather forecast for next week?",
        "How do I reset my password?",
        "Show me trending topics on social media",
        "Analyze customer sentiment from reviews",
        "What are the best practices for inventory management?",
        "Can you help me with data visualization?"
    ]
    
    print(f"\n📋 Testing {len(test_queries)} unmatched queries:")
    
    total_tokens = 0
    successful_responses = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: '{query}'")
        
        try:
            # Simulate available patterns
            available_patterns = [
                {"category": "sales_analytics", "description": "Sales performance data"},
                {"category": "kpi_monitoring", "description": "KPI health scores"},
                {"category": "inventory_management", "description": "Inventory levels"}
            ]
            
            response = ai_agent.process_unmatched_query(query, available_patterns)
            
            if response["success"]:
                successful_responses += 1
                tokens_used = response["metadata"]["tokens_used"]
                total_tokens += tokens_used
                
                # Record token usage
                budget_manager.use_tokens(tokens_used, query)
                
                print(f"✅ {response['response_type'].upper()}")
                print(f"   💬 Message: {response['message']}")
                print(f"   💡 Suggestions: {response['suggestions'][:2]}")
                print(f"   💰 Tokens: {tokens_used}")
                print(f"   ⏱️  Time: {response['metadata']['response_time_ms']:.1f}ms")
                print(f"   🎯 Confidence: {response['metadata']['confidence']:.2f}")
            else:
                print(f"❌ Failed to generate response")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Display summary
    print(f"\n📊 FALLBACK AI SUMMARY")
    print("=" * 30)
    print(f"✅ Success Rate: {successful_responses}/{len(test_queries)} ({successful_responses/len(test_queries)*100:.1f}%)")
    print(f"💰 Total Tokens Used: {total_tokens}")
    print(f"📊 Avg Tokens per Query: {total_tokens/successful_responses:.1f}" if successful_responses > 0 else "N/A")
    
    # Token budget status
    budget_stats = budget_manager.get_usage_stats()
    print(f"💳 Budget Status: {budget_stats['budget_status'].upper()}")
    print(f"📈 Budget Used: {budget_stats['usage_percentage']:.1f}%")
    print(f"🔋 Remaining: {budget_stats['remaining_budget']} tokens")
    
    # System capabilities
    token_stats = ai_agent.get_token_usage_stats()
    print(f"\n🔧 System Capabilities:")
    print(f"   Max tokens per query: {token_stats['max_tokens_per_query']}")
    print(f"   Zero-token fallbacks: {token_stats['zero_token_fallbacks']}")
    print(f"   Template responses: {token_stats['template_responses']}")

if __name__ == "__main__":
    test_fallback_ai()