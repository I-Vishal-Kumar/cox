"""Complex query decomposition and hybrid analysis system."""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from config import settings
from pattern_matcher import QueryPatternMatcher
from fallback_ai import MinimalAIAgent, TokenBudgetManager

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

@dataclass
class QueryComponent:
    """Represents a decomposed query component."""
    component_id: str
    component_type: str  # 'cacheable', 'dynamic', 'analytical'
    query_text: str
    confidence: float
    dependencies: List[str]
    estimated_tokens: int
    cache_key: Optional[str] = None

@dataclass
class AnalysisWorkflow:
    """Represents a multi-step analysis workflow."""
    workflow_id: str
    components: List[QueryComponent]
    execution_order: List[str]
    total_estimated_tokens: int
    cache_hit_potential: float
    hybrid_strategy: str

class QueryDecompositionEngine:
    """Decomposes complex queries into cacheable and dynamic components."""
    
    def __init__(self):
        self.pattern_matcher = QueryPatternMatcher()
        self.fallback_ai = MinimalAIAgent()
        self.token_manager = TokenBudgetManager()
        
        # Query patterns for decomposition
        self.decomposition_patterns = {
            'temporal_analysis': {
                'keywords': ['trend', 'over time', 'monthly', 'quarterly', 'yearly', 'compare', 'vs', 'versus'],
                'components': ['historical_data', 'trend_calculation', 'comparison_analysis']
            },
            'comparative_analysis': {
                'keywords': ['compare', 'vs', 'versus', 'difference', 'better', 'worse', 'higher', 'lower'],
                'components': ['baseline_data', 'comparison_data', 'variance_calculation']
            },
            'predictive_analysis': {
                'keywords': ['predict', 'forecast', 'future', 'next', 'upcoming', 'projection'],
                'components': ['historical_trends', 'predictive_model', 'forecast_generation']
            },
            'root_cause_analysis': {
                'keywords': ['why', 'cause', 'reason', 'explain', 'behind', 'factor'],
                'components': ['symptom_data', 'correlation_analysis', 'causal_inference']
            },
            'drill_down_analysis': {
                'keywords': ['breakdown', 'detail', 'drill down', 'segment', 'by region', 'by category'],
                'components': ['summary_data', 'detailed_breakdown', 'hierarchical_analysis']
            }
        }
        
        # Cacheable data patterns
        self.cacheable_patterns = [
            'historical sales data',
            'inventory levels',
            'kpi metrics',
            'warranty claims',
            'dealer performance',
            'regional summaries',
            'monthly reports',
            'quarterly summaries'
        ]
        
        # Dynamic analysis patterns (require AI/computation)
        self.dynamic_patterns = [
            'trend analysis',
            'correlation calculation',
            'variance explanation',
            'predictive modeling',
            'anomaly detection',
            'causal inference',
            'optimization recommendations'
        ]
    
    def decompose_complex_query(self, query: str) -> AnalysisWorkflow:
        """Decompose a complex query into manageable components."""
        try:
            logger.info(f"Decomposing complex query: '{query}'")
            
            # Step 1: Identify query type and patterns
            query_analysis = self._analyze_query_complexity(query)
            
            # Step 2: Extract components based on patterns
            components = self._extract_query_components(query, query_analysis)
            
            # Step 3: Determine execution order and dependencies
            execution_order = self._determine_execution_order(components)
            
            # Step 4: Calculate token estimates and cache potential
            total_tokens, cache_potential = self._calculate_resource_estimates(components)
            
            # Step 5: Select hybrid strategy
            hybrid_strategy = self._select_hybrid_strategy(components, cache_potential)
            
            workflow = AnalysisWorkflow(
                workflow_id=f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                components=components,
                execution_order=execution_order,
                total_estimated_tokens=total_tokens,
                cache_hit_potential=cache_potential,
                hybrid_strategy=hybrid_strategy
            )
            
            logger.info(f"Query decomposed into {len(components)} components with {cache_potential:.1f}% cache potential")
            return workflow
            
        except Exception as e:
            logger.error(f"Query decomposition failed: {e}")
            # Return simple fallback workflow
            return self._create_fallback_workflow(query)
    
    def _analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Analyze query to determine complexity and patterns."""
        query_lower = query.lower()
        
        analysis = {
            'complexity_score': 0,
            'detected_patterns': [],
            'temporal_elements': [],
            'comparative_elements': [],
            'analytical_elements': [],
            'entities': []
        }
        
        # Check for decomposition patterns
        for pattern_name, pattern_info in self.decomposition_patterns.items():
            matches = sum(1 for keyword in pattern_info['keywords'] if keyword in query_lower)
            if matches > 0:
                analysis['detected_patterns'].append({
                    'pattern': pattern_name,
                    'matches': matches,
                    'confidence': matches / len(pattern_info['keywords'])
                })
                analysis['complexity_score'] += matches
        
        # Detect temporal elements
        temporal_keywords = ['yesterday', 'today', 'week', 'month', 'quarter', 'year', 'trend', 'over time']
        for keyword in temporal_keywords:
            if keyword in query_lower:
                analysis['temporal_elements'].append(keyword)
        
        # Detect comparative elements
        comparative_keywords = ['vs', 'versus', 'compare', 'difference', 'better', 'worse', 'higher', 'lower']
        for keyword in comparative_keywords:
            if keyword in query_lower:
                analysis['comparative_elements'].append(keyword)
        
        # Detect analytical elements
        analytical_keywords = ['why', 'cause', 'predict', 'forecast', 'analyze', 'explain', 'correlation']
        for keyword in analytical_keywords:
            if keyword in query_lower:
                analysis['analytical_elements'].append(keyword)
        
        # Extract business entities
        entity_patterns = [
            r'\\b(sales|revenue|inventory|warranty|kpi|dealer|region|model|plant)\\b',
            r'\\b(northeast|midwest|west|southeast|southwest)\\b',
            r'\\b(q[1-4]|quarter|monthly|yearly)\\b'
        ]
        
        for pattern in entity_patterns:
            matches = re.findall(pattern, query_lower)
            analysis['entities'].extend(matches)
        
        return analysis
    
    def _extract_query_components(self, query: str, analysis: Dict[str, Any]) -> List[QueryComponent]:
        """Extract individual components from the complex query."""
        components = []
        component_counter = 0
        
        # Determine primary analysis type
        primary_pattern = None
        if analysis['detected_patterns']:
            primary_pattern = max(analysis['detected_patterns'], key=lambda x: x['confidence'])['pattern']
        
        if primary_pattern:
            pattern_info = self.decomposition_patterns[primary_pattern]
            
            for component_type in pattern_info['components']:
                component_counter += 1
                
                # Determine if component is cacheable or dynamic
                is_cacheable = self._is_component_cacheable(component_type, analysis)
                comp_type = 'cacheable' if is_cacheable else 'dynamic'
                
                # Generate component query text
                component_query = self._generate_component_query(component_type, query, analysis)
                
                # Estimate token usage
                estimated_tokens = 0 if is_cacheable else self._estimate_component_tokens(component_type)
                
                component = QueryComponent(
                    component_id=f"comp_{component_counter}",
                    component_type=comp_type,
                    query_text=component_query,
                    confidence=0.8 if is_cacheable else 0.6,
                    dependencies=[],
                    estimated_tokens=estimated_tokens,
                    cache_key=self._generate_cache_key(component_query) if is_cacheable else None
                )
                
                components.append(component)
        
        # If no clear pattern, create generic components
        if not components:
            components = self._create_generic_components(query, analysis)
        
        # Set up dependencies
        self._establish_component_dependencies(components)
        
        return components
    
    def _is_component_cacheable(self, component_type: str, analysis: Dict[str, Any]) -> bool:
        """Determine if a component can be served from cache."""
        cacheable_component_types = [
            'historical_data', 'baseline_data', 'summary_data', 'inventory_levels',
            'kpi_metrics', 'dealer_performance', 'regional_summaries'
        ]
        
        dynamic_component_types = [
            'trend_calculation', 'variance_calculation', 'predictive_model',
            'correlation_analysis', 'causal_inference', 'forecast_generation'
        ]
        
        if component_type in cacheable_component_types:
            return True
        elif component_type in dynamic_component_types:
            return False
        else:
            # Heuristic: if query has analytical elements, likely dynamic
            return len(analysis.get('analytical_elements', [])) == 0
    
    def _generate_component_query(self, component_type: str, original_query: str, analysis: Dict[str, Any]) -> str:
        """Generate specific query text for a component."""
        entities = analysis.get('entities', [])
        
        component_templates = {
            'historical_data': f"Get historical {' '.join(entities[:2])} data",
            'baseline_data': f"Get baseline {' '.join(entities[:2])} metrics",
            'summary_data': f"Get summary {' '.join(entities[:2])} report",
            'trend_calculation': f"Calculate trends for {' '.join(entities[:2])}",
            'variance_calculation': f"Calculate variance in {' '.join(entities[:2])}",
            'predictive_model': f"Generate predictions for {' '.join(entities[:2])}",
            'correlation_analysis': f"Analyze correlations in {' '.join(entities[:2])}",
            'causal_inference': f"Determine causes of {' '.join(entities[:2])} changes",
            'forecast_generation': f"Generate forecast for {' '.join(entities[:2])}"
        }
        
        return component_templates.get(component_type, f"Process {component_type} for: {original_query[:50]}...")
    
    def _estimate_component_tokens(self, component_type: str) -> int:
        """Estimate token usage for dynamic components."""
        token_estimates = {
            'trend_calculation': 150,
            'variance_calculation': 100,
            'predictive_model': 300,
            'correlation_analysis': 200,
            'causal_inference': 250,
            'forecast_generation': 350,
            'comparison_analysis': 120,
            'hierarchical_analysis': 180
        }
        
        return token_estimates.get(component_type, 150)
    
    def _generate_cache_key(self, component_query: str) -> str:
        """Generate cache key for cacheable components."""
        import hashlib
        return hashlib.md5(component_query.encode()).hexdigest()[:12]
    
    def _create_generic_components(self, query: str, analysis: Dict[str, Any]) -> List[QueryComponent]:
        """Create generic components when no specific pattern is detected."""
        components = []
        
        # Always start with data retrieval (cacheable)
        data_component = QueryComponent(
            component_id="comp_1",
            component_type="cacheable",
            query_text=f"Retrieve relevant data for: {query}",
            confidence=0.7,
            dependencies=[],
            estimated_tokens=0,
            cache_key=self._generate_cache_key(query)
        )
        components.append(data_component)
        
        # Add analysis component if analytical elements detected
        if analysis.get('analytical_elements'):
            analysis_component = QueryComponent(
                component_id="comp_2",
                component_type="dynamic",
                query_text=f"Analyze data for: {query}",
                confidence=0.6,
                dependencies=["comp_1"],
                estimated_tokens=200
            )
            components.append(analysis_component)
        
        return components
    
    def _establish_component_dependencies(self, components: List[QueryComponent]) -> None:
        """Establish dependencies between components."""
        for i, component in enumerate(components):
            if i > 0 and component.component_type == 'dynamic':
                # Dynamic components typically depend on previous cacheable components
                cacheable_deps = [c.component_id for c in components[:i] if c.component_type == 'cacheable']
                component.dependencies.extend(cacheable_deps)
    
    def _determine_execution_order(self, components: List[QueryComponent]) -> List[str]:
        """Determine optimal execution order based on dependencies."""
        # Simple topological sort based on dependencies
        executed = set()
        execution_order = []
        
        while len(execution_order) < len(components):
            for component in components:
                if (component.component_id not in executed and 
                    all(dep in executed for dep in component.dependencies)):
                    execution_order.append(component.component_id)
                    executed.add(component.component_id)
                    break
        
        return execution_order
    
    def _calculate_resource_estimates(self, components: List[QueryComponent]) -> Tuple[int, float]:
        """Calculate total token estimates and cache hit potential."""
        total_tokens = sum(c.estimated_tokens for c in components)
        
        cacheable_components = sum(1 for c in components if c.component_type == 'cacheable')
        cache_potential = (cacheable_components / len(components) * 100) if components else 0
        
        return total_tokens, cache_potential
    
    def _select_hybrid_strategy(self, components: List[QueryComponent], cache_potential: float) -> str:
        """Select optimal hybrid analysis strategy."""
        if cache_potential >= 80:
            return "cache_heavy"  # Mostly cached data with minimal AI
        elif cache_potential >= 50:
            return "balanced_hybrid"  # Mix of cached and AI analysis
        elif cache_potential >= 20:
            return "ai_heavy"  # Mostly AI with some cached baseline data
        else:
            return "full_ai"  # Minimal cache usage, mostly AI analysis
    
    def _create_fallback_workflow(self, query: str) -> AnalysisWorkflow:
        """Create simple fallback workflow for failed decomposition."""
        fallback_component = QueryComponent(
            component_id="fallback_1",
            component_type="dynamic",
            query_text=query,
            confidence=0.5,
            dependencies=[],
            estimated_tokens=200
        )
        
        return AnalysisWorkflow(
            workflow_id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            components=[fallback_component],
            execution_order=["fallback_1"],
            total_estimated_tokens=200,
            cache_hit_potential=0.0,
            hybrid_strategy="full_ai"
        )

class HybridAnalysisSystem:
    """Executes hybrid analysis combining cached data with AI processing."""
    
    def __init__(self):
        self.decomposition_engine = QueryDecompositionEngine()
        self.pattern_matcher = QueryPatternMatcher()
        self.fallback_ai = MinimalAIAgent()
        self.token_manager = TokenBudgetManager()
        self.execution_cache = {}
    
    async def execute_hybrid_analysis(self, query: str) -> Dict[str, Any]:
        """Execute hybrid analysis workflow."""
        try:
            start_time = datetime.now()
            
            # Step 1: Decompose query
            workflow = self.decomposition_engine.decompose_complex_query(query)
            
            # Step 2: Execute components in order
            component_results = {}
            total_tokens_used = 0
            cache_hits = 0
            
            for component_id in workflow.execution_order:
                component = next(c for c in workflow.components if c.component_id == component_id)
                
                result = await self._execute_component(component, component_results)
                component_results[component_id] = result
                
                if result.get("success"):
                    total_tokens_used += result.get("tokens_used", 0)
                    if result.get("cache_hit"):
                        cache_hits += 1
            
            # Step 3: Combine results
            final_result = self._combine_component_results(workflow, component_results)
            
            # Step 4: Add execution metadata
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "query": query,
                "workflow_id": workflow.workflow_id,
                "hybrid_strategy": workflow.hybrid_strategy,
                "execution_metadata": {
                    "total_components": len(workflow.components),
                    "cache_hits": cache_hits,
                    "cache_hit_rate": (cache_hits / len(workflow.components) * 100) if workflow.components else 0,
                    "total_tokens_used": total_tokens_used,
                    "estimated_tokens": workflow.total_estimated_tokens,
                    "token_efficiency": ((workflow.total_estimated_tokens - total_tokens_used) / workflow.total_estimated_tokens * 100) if workflow.total_estimated_tokens > 0 else 0,
                    "execution_time_ms": execution_time,
                    "cache_potential": workflow.cache_hit_potential
                },
                "component_results": component_results,
                "final_analysis": final_result
            }
            
        except Exception as e:
            logger.error(f"Hybrid analysis execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "fallback_used": True
            }
    
    async def _execute_component(self, component: QueryComponent, previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single component of the workflow."""
        try:
            if component.component_type == 'cacheable':
                # Try to get from cache/pattern matcher
                cache_result = self.pattern_matcher.get_response_for_query(component.query_text)
                
                if cache_result.get("success"):
                    return {
                        "success": True,
                        "component_id": component.component_id,
                        "data": cache_result.get("data", {}),
                        "tokens_used": 0,
                        "cache_hit": True,
                        "execution_time_ms": 5  # Fast cache access
                    }
                else:
                    # Cache miss - use fallback
                    fallback_result = self.fallback_ai.process_unmatched_query(component.query_text, [])
                    return {
                        "success": fallback_result.get("success", False),
                        "component_id": component.component_id,
                        "data": {"message": fallback_result.get("message", "")},
                        "tokens_used": fallback_result.get("metadata", {}).get("tokens_used", 0),
                        "cache_hit": False,
                        "execution_time_ms": 50
                    }
            
            else:  # dynamic component
                # Use AI for analysis
                ai_result = self.fallback_ai.process_unmatched_query(component.query_text, [])
                
                return {
                    "success": ai_result.get("success", False),
                    "component_id": component.component_id,
                    "analysis": ai_result.get("message", ""),
                    "tokens_used": ai_result.get("metadata", {}).get("tokens_used", 0),
                    "cache_hit": False,
                    "execution_time_ms": 100
                }
                
        except Exception as e:
            logger.error(f"Component execution failed for {component.component_id}: {e}")
            return {
                "success": False,
                "component_id": component.component_id,
                "error": str(e),
                "tokens_used": 0,
                "cache_hit": False
            }
    
    def _combine_component_results(self, workflow: AnalysisWorkflow, component_results: Dict[str, Any]) -> Dict[str, Any]:
        """Combine results from all components into final analysis."""
        combined_data = []
        combined_analysis = []
        
        for component_id, result in component_results.items():
            if result.get("success"):
                if "data" in result:
                    data = result["data"]
                    if isinstance(data, dict) and "processed" in data:
                        combined_data.extend(data.get("processed", []))
                
                if "analysis" in result:
                    combined_analysis.append(result["analysis"])
        
        return {
            "strategy": workflow.hybrid_strategy,
            "data_points": len(combined_data),
            "data": combined_data[:10],  # Limit for response size
            "analysis_summary": " | ".join(combined_analysis) if combined_analysis else "Analysis completed using cached data",
            "workflow_efficiency": f"{workflow.cache_hit_potential:.1f}% cache utilization"
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get hybrid analysis system status."""
        return {
            "status": "operational",
            "decomposition_patterns": len(self.decomposition_engine.decomposition_patterns),
            "cacheable_patterns": len(self.decomposition_engine.cacheable_patterns),
            "dynamic_patterns": len(self.decomposition_engine.dynamic_patterns),
            "execution_cache_size": len(self.execution_cache),
            "supported_strategies": ["cache_heavy", "balanced_hybrid", "ai_heavy", "full_ai"]
        }

# Test functions
async def test_query_decomposition():
    """Test the query decomposition and hybrid analysis system."""
    print("🧪 Testing Query Decomposition and Hybrid Analysis")
    print("=" * 60)
    
    hybrid_system = HybridAnalysisSystem()
    
    # Test queries of varying complexity
    test_queries = [
        "Why did sales drop in Q3 compared to Q2?",
        "Show me the trend of inventory levels over the past 6 months and predict next month",
        "Compare dealer performance in the Northeast vs Midwest and explain the differences",
        "What are the root causes of warranty claim increases in the West region?",
        "Analyze KPI variance and provide recommendations for improvement"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\\n🔍 Test {i}: '{query}'")
        print("-" * 50)
        
        # Test decomposition
        decomposition_engine = QueryDecompositionEngine()
        workflow = decomposition_engine.decompose_complex_query(query)
        
        print(f"📋 Decomposition Results:")
        print(f"   Components: {len(workflow.components)}")
        print(f"   Estimated Tokens: {workflow.total_estimated_tokens}")
        print(f"   Cache Potential: {workflow.cache_hit_potential:.1f}%")
        print(f"   Strategy: {workflow.hybrid_strategy}")
        
        # Show component breakdown
        for component in workflow.components:
            cache_indicator = "💾" if component.component_type == 'cacheable' else "🤖"
            print(f"   {cache_indicator} {component.component_id}: {component.query_text[:40]}... ({component.estimated_tokens} tokens)")
        
        # Test execution
        result = await hybrid_system.execute_hybrid_analysis(query)
        
        if result.get("success"):
            metadata = result["execution_metadata"]
            print(f"\\n✅ Execution Results:")
            print(f"   Cache Hit Rate: {metadata['cache_hit_rate']:.1f}%")
            print(f"   Tokens Used: {metadata['total_tokens_used']}/{metadata['estimated_tokens']}")
            print(f"   Token Efficiency: {metadata['token_efficiency']:.1f}%")
            print(f"   Execution Time: {metadata['execution_time_ms']:.1f}ms")
            
            final_analysis = result.get("final_analysis", {})
            print(f"   Data Points: {final_analysis.get('data_points', 0)}")
            print(f"   Analysis: {final_analysis.get('analysis_summary', 'N/A')[:60]}...")
        else:
            print(f"❌ Execution failed: {result.get('error')}")
    
    # Test system status
    print(f"\\n📊 System Status:")
    status = hybrid_system.get_system_status()
    print(f"   Status: {status['status']}")
    print(f"   Decomposition Patterns: {status['decomposition_patterns']}")
    print(f"   Supported Strategies: {len(status['supported_strategies'])}")
    
    print(f"\\n🎉 Query Decomposition and Hybrid Analysis Test Complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_query_decomposition())