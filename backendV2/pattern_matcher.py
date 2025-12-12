"""Pattern matching system for routing user queries to appropriate SQL dumps."""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from difflib import SequenceMatcher
import logging

from config import settings
from sql_queries import SQLQueryTemplates

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

class QueryPatternMatcher:
    """Matches user queries to pre-computed SQL dumps using keyword and fuzzy matching."""
    
    def __init__(self):
        self.templates = SQLQueryTemplates()
        self.dump_patterns = self._load_dump_patterns()
        
    def _load_dump_patterns(self) -> Dict[str, Any]:
        """Load patterns from generated dump files."""
        patterns = {}
        
        try:
            # Load patterns from all dump files
            dumps_dir = Path(settings.dumps_dir)
            if not dumps_dir.exists():
                logger.warning(f"Dumps directory not found: {dumps_dir}")
                return patterns
            
            for category_dir in dumps_dir.iterdir():
                if category_dir.is_dir() and category_dir.name != "__pycache__":
                    for dump_file in category_dir.glob("*.json"):
                        try:
                            with open(dump_file, 'r', encoding='utf-8') as f:
                                dump_data = json.load(f)
                                
                            pattern_key = f"{category_dir.name}/{dump_file.stem}"
                            patterns[pattern_key] = {
                                "keywords": dump_data.get("keywords", []),
                                "description": dump_data.get("description", ""),
                                "category": category_dir.name,
                                "query_name": dump_file.stem,
                                "file_path": str(dump_file),
                                "sql_query": dump_data.get("sql_query", ""),
                                "data_size": len(dump_data.get("data", [])),
                                "last_updated": dump_data.get("metadata", {}).get("generated_at", "")
                            }
                        except Exception as e:
                            logger.error(f"Failed to load pattern from {dump_file}: {e}")
            
            logger.info(f"Loaded {len(patterns)} query patterns from dump files")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to load dump patterns: {e}")
            return {}
    
    def preprocess_query(self, query: str) -> List[str]:
        """Preprocess user query into normalized keywords."""
        # Convert to lowercase
        query = query.lower().strip()
        
        # Remove punctuation and special characters
        query = re.sub(r'[^\w\s]', ' ', query)
        
        # Split into words and remove common stop words
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
        
        words = [word for word in query.split() if word and word not in stop_words and len(word) > 1]
        
        # Add some stemming for common variations
        stemmed_words = []
        for word in words:
            # Simple stemming rules
            if word.endswith('ing'):
                stemmed_words.append(word[:-3])
            elif word.endswith('ed'):
                stemmed_words.append(word[:-2])
            elif word.endswith('s') and len(word) > 3:
                stemmed_words.append(word[:-1])
            stemmed_words.append(word)
        
        return list(set(stemmed_words))  # Remove duplicates
    
    def calculate_keyword_match_score(self, query_keywords: List[str], pattern_keywords: List[str]) -> float:
        """Calculate keyword match score between query and pattern."""
        if not pattern_keywords:
            return 0.0
        
        # Count exact matches
        exact_matches = sum(1 for qkw in query_keywords if any(qkw in pkw or pkw in qkw for pkw in pattern_keywords))
        
        # Calculate match ratio
        match_score = exact_matches / len(pattern_keywords)
        
        # Bonus for multiple matches
        if exact_matches > 1:
            match_score *= 1.2
        
        # Bonus for high coverage of query keywords
        query_coverage = exact_matches / len(query_keywords) if query_keywords else 0
        match_score += query_coverage * 0.3
        
        return min(match_score, 1.0)  # Cap at 1.0
    
    def calculate_fuzzy_match_score(self, query: str, description: str) -> float:
        """Calculate fuzzy match score using sequence matching."""
        # Normalize both strings
        query_norm = ' '.join(self.preprocess_query(query))
        desc_norm = ' '.join(self.preprocess_query(description))
        
        # Use SequenceMatcher for fuzzy matching
        matcher = SequenceMatcher(None, query_norm, desc_norm)
        return matcher.ratio()
    
    def find_best_matches(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Find best matching patterns for a user query."""
        if not self.dump_patterns:
            logger.warning("No dump patterns loaded")
            return []
        
        query_keywords = self.preprocess_query(query)
        logger.debug(f"Query keywords: {query_keywords}")
        
        matches = []
        
        for pattern_key, pattern_info in self.dump_patterns.items():
            # Calculate keyword match score
            keyword_score = self.calculate_keyword_match_score(
                query_keywords, 
                pattern_info["keywords"]
            )
            
            # Calculate fuzzy match score
            fuzzy_score = self.calculate_fuzzy_match_score(
                query, 
                pattern_info["description"]
            )
            
            # Combined score (weighted)
            combined_score = (keyword_score * 0.7) + (fuzzy_score * 0.3)
            
            # Only include matches above threshold
            if combined_score >= settings.fuzzy_match_threshold:
                matches.append({
                    "pattern_key": pattern_key,
                    "category": pattern_info["category"],
                    "query_name": pattern_info["query_name"],
                    "description": pattern_info["description"],
                    "file_path": pattern_info["file_path"],
                    "keyword_score": keyword_score,
                    "fuzzy_score": fuzzy_score,
                    "combined_score": combined_score,
                    "data_size": pattern_info["data_size"],
                    "last_updated": pattern_info["last_updated"],
                    "matched_keywords": [kw for kw in query_keywords if any(kw in pk for pk in pattern_info["keywords"])]
                })
        
        # Sort by combined score (descending)
        matches.sort(key=lambda x: x["combined_score"], reverse=True)
        
        logger.info(f"Found {len(matches)} matches for query: '{query}'")
        return matches[:max_results]
    
    def route_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Route a query to the best matching dump file."""
        matches = self.find_best_matches(query, max_results=1)
        
        if not matches:
            logger.info(f"No matches found for query: '{query}'")
            return None
        
        best_match = matches[0]
        
        # Check if match meets minimum threshold
        if best_match["combined_score"] < settings.keyword_match_threshold:
            logger.info(f"Best match score {best_match['combined_score']:.3f} below threshold {settings.keyword_match_threshold}")
            return None
        
        logger.info(f"Routed query '{query}' to {best_match['pattern_key']} (score: {best_match['combined_score']:.3f})")
        return best_match
    
    def load_dump_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load data from a specific dump file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load dump data from {file_path}: {e}")
            return None
    
    def get_response_for_query(self, query: str) -> Dict[str, Any]:
        """Get complete response for a user query."""
        # Route query to best match
        match = self.route_query(query)
        
        if not match:
            return {
                "success": False,
                "error": "No matching data found",
                "query": query,
                "suggestions": self._get_query_suggestions()
            }
        
        # Load dump data
        dump_data = self.load_dump_data(match["file_path"])
        
        if not dump_data:
            return {
                "success": False,
                "error": "Failed to load data",
                "query": query,
                "match_info": match
            }
        
        return {
            "success": True,
            "query": query,
            "match_info": {
                "category": match["category"],
                "query_name": match["query_name"],
                "description": match["description"],
                "confidence_score": match["combined_score"],
                "matched_keywords": match["matched_keywords"]
            },
            "data": dump_data["data"],
            "chart_config": dump_data.get("chart_config"),
            "metadata": {
                "data_size": len(dump_data["data"]),
                "last_updated": dump_data.get("metadata", {}).get("generated_at"),
                "sql_query": dump_data.get("sql_query"),
                "response_time_ms": 0  # Will be set by caller
            }
        }
    
    def _get_query_suggestions(self) -> List[str]:
        """Get query suggestions when no match is found."""
        suggestions = []
        
        # Get top categories and their descriptions
        category_examples = {
            "sales_analytics": "Try: 'top selling models by region' or 'dealer performance'",
            "kpi_monitoring": "Try: 'KPI health scores' or 'variance reports'", 
            "inventory_management": "Try: 'inventory stock levels' or 'stockout risks'",
            "warranty_analysis": "Try: 'warranty claims by model' or 'repeat repairs'",
            "executive_reports": "Try: 'CEO weekly summary' or 'margin analysis'"
        }
        
        for category, example in category_examples.items():
            if any(category in pattern["category"] for pattern in self.dump_patterns.values()):
                suggestions.append(example)
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def refresh_patterns(self) -> bool:
        """Refresh patterns from dump files (call after regenerating dumps)."""
        try:
            self.dump_patterns = self._load_dump_patterns()
            logger.info("Pattern cache refreshed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh patterns: {e}")
            return False
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded patterns."""
        if not self.dump_patterns:
            return {"total_patterns": 0, "categories": {}}
        
        stats = {
            "total_patterns": len(self.dump_patterns),
            "categories": {},
            "total_data_points": 0,
            "last_refresh": None
        }
        
        for pattern in self.dump_patterns.values():
            category = pattern["category"]
            if category not in stats["categories"]:
                stats["categories"][category] = {
                    "count": 0,
                    "total_data_size": 0
                }
            
            stats["categories"][category]["count"] += 1
            stats["categories"][category]["total_data_size"] += pattern["data_size"]
            stats["total_data_points"] += pattern["data_size"]
        
        return stats

# Test functions
def test_pattern_matching():
    """Test the pattern matching system."""
    matcher = QueryPatternMatcher()
    
    test_queries = [
        "What were the top selling models in the Northeast last week?",
        "Show me KPI health scores",
        "Give me inventory levels by factory",
        "Why did warranty claims increase?",
        "CEO weekly summary",
        "F&I revenue by region",
        "Plant downtime analysis",
        "This is a completely unrelated query about weather"
    ]
    
    print("🧪 Testing Pattern Matching System")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        # Test routing
        match = matcher.route_query(query)
        if match:
            print(f"✅ Matched: {match['category']}/{match['query_name']}")
            print(f"   Score: {match['combined_score']:.3f}")
            print(f"   Keywords: {match['matched_keywords']}")
        else:
            print("❌ No match found")
        
        # Test full response
        response = matcher.get_response_for_query(query)
        if response["success"]:
            print(f"📊 Data points: {len(response['data'])}")
            print(f"📈 Chart config: {'Yes' if response['chart_config'] else 'No'}")
        else:
            print(f"⚠️  Error: {response['error']}")
            if "suggestions" in response:
                print(f"💡 Suggestions: {response['suggestions']}")

if __name__ == "__main__":
    test_pattern_matching()