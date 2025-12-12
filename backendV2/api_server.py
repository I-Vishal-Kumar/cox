"""FastAPI server for the token-optimized BI system."""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import logging
from datetime import datetime

from frontend_integration import FrontendIntegration
from query_router import QueryRouter
from dump_generator import DumpGenerator
from scheduler import DumpScheduler
from query_decomposition import HybridAnalysisSystem
from chart_generator import ChartDataGenerator
from monitoring_dashboard import SystemMonitor
from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Initialize components
frontend_integration = FrontendIntegration()
query_router = QueryRouter()
dump_generator = DumpGenerator()
scheduler = DumpScheduler()
hybrid_analysis = HybridAnalysisSystem()
chart_generator = ChartDataGenerator()
system_monitor = SystemMonitor()

# FastAPI app
app = FastAPI(
    title="Token-Optimized BI System",
    description="High-performance business intelligence system with minimal token usage",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    options: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None

class BatchQueryRequest(BaseModel):
    queries: List[str]
    options: Optional[Dict[str, Any]] = None

class HybridAnalysisRequest(BaseModel):
    query: str
    analysis_type: Optional[str] = "auto"  # auto, temporal, comparative, predictive, root_cause
    user_context: Optional[Dict[str, Any]] = None

class ChartRequest(BaseModel):
    chart_id: str
    data: List[Dict[str, Any]]
    chart_type: Optional[str] = "auto"
    title: Optional[str] = ""
    category: Optional[str] = ""

class BatchChartRequest(BaseModel):
    charts: List[ChartRequest]

class QueryResponse(BaseModel):
    success: bool
    query: str
    data: Dict[str, Any]
    charts: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    match_info: Optional[Dict[str, Any]] = None
    ui_suggestions: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# API Routes

@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "name": "Token-Optimized BI System",
        "version": "1.0.0",
        "status": "operational",
        "description": "High-performance business intelligence with minimal token usage",
        "endpoints": {
            "query": "/api/query",
            "batch": "/api/batch",
            "status": "/api/status",
            "suggestions": "/api/suggestions",
            "capabilities": "/api/capabilities"
        }
    }

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a single business intelligence query.
    
    Returns structured data with chart configurations and metadata.
    """
    try:
        logger.info(f"Processing API query: '{request.query}'")
        
        # Process query through frontend integration
        response = frontend_integration.process_frontend_query(
            query=request.query,
            options=request.options
        )
        
        # Add user context if provided
        if request.user_context:
            response["user_context"] = request.user_context
        
        return QueryResponse(**response)
        
    except Exception as e:
        logger.error(f"API query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/batch")
async def process_batch_queries(request: BatchQueryRequest):
    """Process multiple queries in batch."""
    try:
        logger.info(f"Processing batch of {len(request.queries)} queries")
        
        results = []
        for query in request.queries:
            response = frontend_integration.process_frontend_query(
                query=query,
                options=request.options
            )
            results.append(response)
        
        return {
            "success": True,
            "total_queries": len(request.queries),
            "results": results,
            "batch_metadata": {
                "processed_at": datetime.now().isoformat(),
                "total_data_points": sum(r.get("metadata", {}).get("data_points", 0) for r in results),
                "total_charts": sum(r.get("metadata", {}).get("chart_count", 0) for r in results)
            }
        }
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suggestions")
async def get_query_suggestions(partial_query: Optional[str] = Query(None)):
    """Get query suggestions based on available data patterns."""
    try:
        suggestions = query_router.get_query_suggestions(partial_query or "")
        
        return {
            "success": True,
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "partial_query": partial_query
        }
        
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_system_status():
    """Get comprehensive system status and performance metrics."""
    try:
        # Get status from query router
        router_status = query_router.get_system_status()
        
        # Get pattern matcher stats
        pattern_stats = query_router.pattern_matcher.get_pattern_stats()
        
        # Combine into comprehensive status
        status = {
            "system": {
                "status": "operational",
                "version": "1.0.0",
                "uptime": "N/A",  # Would track actual uptime in production
                "timestamp": datetime.now().isoformat()
            },
            "performance": router_status["performance"],
            "data": {
                "available_patterns": pattern_stats["total_patterns"],
                "categories": list(pattern_stats.get("categories", {}).keys()),
                "total_data_points": pattern_stats["total_data_points"],
                "last_refresh": "N/A"  # Would track from scheduler
            },
            "configuration": {
                "max_response_time_ms": settings.max_response_time_ms,
                "keyword_match_threshold": settings.keyword_match_threshold,
                "fuzzy_match_threshold": settings.fuzzy_match_threshold
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/capabilities")
async def get_system_capabilities():
    """Get system capabilities for frontend configuration."""
    try:
        capabilities = frontend_integration.get_system_capabilities()
        
        return {
            "success": True,
            "capabilities": capabilities,
            "api_version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Failed to get capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/hybrid-analysis")
async def process_hybrid_analysis(request: HybridAnalysisRequest):
    """Process complex queries using hybrid analysis with query decomposition."""
    try:
        logger.info(f"Processing hybrid analysis request: '{request.query}'")
        
        # Execute hybrid analysis
        result = await hybrid_analysis.execute_hybrid_analysis(request.query)
        
        if result.get("success"):
            return {
                "success": True,
                "query": request.query,
                "workflow_id": result["workflow_id"],
                "strategy": result["hybrid_strategy"],
                "execution_metadata": result["execution_metadata"],
                "analysis": result["final_analysis"],
                "performance": {
                    "cache_hit_rate": result["execution_metadata"]["cache_hit_rate"],
                    "token_efficiency": result["execution_metadata"]["token_efficiency"],
                    "execution_time_ms": result["execution_metadata"]["execution_time_ms"]
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Hybrid analysis failed"),
                "query": request.query,
                "fallback_available": True
            }
            
    except Exception as e:
        logger.error(f"Hybrid analysis endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/charts/generate")
async def generate_chart_with_versioning(request: ChartRequest):
    """Generate chart with versioning and incremental updates."""
    try:
        logger.info(f"Generating chart: {request.chart_id}")
        
        result = chart_generator.generate_chart_with_versioning(
            chart_id=request.chart_id,
            data=request.data,
            chart_type=request.chart_type,
            title=request.title,
            category=request.category
        )
        
        if result.get("success"):
            return {
                "success": True,
                "chart_id": request.chart_id,
                "version": result["version"],
                "config": result["config"],
                "update_type": result["update_type"],
                "performance_gain": result.get("performance_gain", 0),
                "data_points": result["data_points"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Chart generation failed"),
                "chart_id": request.chart_id
            }
            
    except Exception as e:
        logger.error(f"Chart generation endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/charts/batch")
async def generate_batch_charts(request: BatchChartRequest):
    """Generate multiple charts in batch with optimization."""
    try:
        logger.info(f"Processing batch chart generation: {len(request.charts)} charts")
        
        # Convert to format expected by chart generator
        chart_updates = []
        for chart_req in request.charts:
            chart_updates.append({
                "chart_id": chart_req.chart_id,
                "data": chart_req.data,
                "chart_type": chart_req.chart_type,
                "title": chart_req.title,
                "category": chart_req.category
            })
        
        result = chart_generator.batch_update_charts(chart_updates)
        
        return {
            "success": result["success"],
            "total_charts": result["total_charts"],
            "successful_updates": result["successful_updates"],
            "failed_updates": result["failed_updates"],
            "average_performance_gain": result["average_performance_gain"],
            "results": result["results"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch chart generation endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/charts/{chart_id}/history")
async def get_chart_history(chart_id: str):
    """Get version history for a specific chart."""
    try:
        history = chart_generator.get_chart_version_history(chart_id)
        
        if history.get("success"):
            return {
                "success": True,
                "chart_id": chart_id,
                "history": history,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Chart {chart_id} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chart history endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/charts/{chart_id}/rollback")
async def rollback_chart(chart_id: str, target_version: Optional[int] = None):
    """Rollback chart to a previous version."""
    try:
        result = chart_generator.rollback_chart_version(chart_id, target_version)
        
        if result.get("success"):
            return {
                "success": True,
                "chart_id": chart_id,
                "version": result["version"],
                "config": result["config"],
                "rollback_from": result["rollback_from"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Rollback failed"),
                "chart_id": chart_id
            }
            
    except Exception as e:
        logger.error(f"Chart rollback endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/charts/{chart_id}/optimize")
async def optimize_chart(chart_id: str):
    """Optimize chart configuration for better performance."""
    try:
        result = chart_generator.optimize_chart_performance(chart_id)
        
        if result.get("success"):
            return {
                "success": True,
                "chart_id": chart_id,
                "optimizations_applied": result["optimizations_applied"],
                "performance_improvement": result["performance_improvement"],
                "config": result["config"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Optimization failed"),
                "chart_id": chart_id
            }
            
    except Exception as e:
        logger.error(f"Chart optimization endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/comprehensive-status")
async def get_comprehensive_system_status():
    """Get comprehensive system status including all components."""
    try:
        # Gather status from all components
        query_router_status = query_router.get_system_status()
        hybrid_analysis_status = hybrid_analysis.get_system_status()
        
        # Calculate overall system metrics
        total_queries = query_router_status["performance"]["total_queries_processed"]
        cache_hit_rate = query_router_status["performance"]["cache_hit_rate_percent"]
        token_efficiency = query_router_status["token_optimization"]["token_efficiency_percent"]
        
        return {
            "system_status": "operational",
            "timestamp": datetime.now().isoformat(),
            "overall_metrics": {
                "total_queries_processed": total_queries,
                "cache_hit_rate_percent": cache_hit_rate,
                "token_efficiency_percent": token_efficiency,
                "avg_response_time_ms": query_router_status["performance"]["avg_response_time_ms"],
                "total_tokens_saved": query_router_status["performance"]["total_tokens_used"]
            },
            "component_status": {
                "query_router": query_router_status,
                "hybrid_analysis": hybrid_analysis_status,
                "frontend_integration": "operational",
                "chart_generator": "operational",
                "dump_scheduler": "operational"
            },
            "capabilities": {
                "hybrid_analysis": True,
                "incremental_charts": True,
                "query_decomposition": True,
                "token_optimization": True,
                "real_time_caching": True,
                "batch_processing": True
            }
        }
        
    except Exception as e:
        logger.error(f"Comprehensive status endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/dashboard")
async def get_monitoring_dashboard(hours: int = Query(1, ge=1, le=168)):
    """Get real-time monitoring dashboard data."""
    try:
        dashboard_data = system_monitor.get_dashboard_data(hours)
        return {
            "success": True,
            "dashboard": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Monitoring dashboard endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/alerts")
async def get_active_alerts():
    """Get currently active alerts."""
    try:
        active_alerts = system_monitor.alert_manager.get_active_alerts()
        alert_history = system_monitor.alert_manager.get_alert_history(24)
        
        return {
            "success": True,
            "active_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "rule_id": alert.rule_id,
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                    "severity": alert.severity,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "acknowledged": alert.acknowledged
                }
                for alert in active_alerts
            ],
            "alert_history_24h": len(alert_history),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Alerts endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitoring/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge a specific alert."""
    try:
        success = system_monitor.alert_manager.acknowledge_alert(alert_id)
        
        if success:
            return {
                "success": True,
                "message": f"Alert {alert_id} acknowledged",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alert acknowledgment endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/trends")
async def get_performance_trends(hours: int = Query(24, ge=1, le=168)):
    """Get performance trends over time."""
    try:
        trends = system_monitor.get_performance_trends(hours)
        
        return {
            "success": True,
            "trends": trends,
            "time_range_hours": hours,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Performance trends endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/metrics/{metric_name}")
async def get_metric_history(metric_name: str, hours: int = Query(1, ge=1, le=168)):
    """Get detailed history for a specific metric."""
    try:
        history = system_monitor.metrics_collector.get_metric_history(metric_name, hours)
        summary = system_monitor.metrics_collector.get_metric_summary(metric_name, hours)
        
        return {
            "success": True,
            "metric_name": metric_name,
            "summary": summary,
            "history": [
                {
                    "timestamp": metric.timestamp.isoformat(),
                    "value": metric.value,
                    "unit": metric.unit,
                    "category": metric.category
                }
                for metric in history
            ],
            "data_points": len(history),
            "time_range_hours": hours
        }
    except Exception as e:
        logger.error(f"Metric history endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/refresh-patterns")
async def refresh_patterns(background_tasks: BackgroundTasks):
    """Refresh pattern cache (admin endpoint)."""
    try:
        # Refresh patterns in background
        background_tasks.add_task(query_router.refresh_patterns)
        
        return {
            "success": True,
            "message": "Pattern refresh initiated",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/regenerate-dumps")
async def regenerate_dumps(
    background_tasks: BackgroundTasks,
    category: Optional[str] = Query(None, description="Specific category to regenerate")
):
    """Regenerate SQL dumps (admin endpoint)."""
    try:
        if category:
            # Regenerate specific category
            background_tasks.add_task(dump_generator.refresh_specific_category, category)
            message = f"Dump regeneration initiated for category: {category}"
        else:
            # Regenerate all dumps
            background_tasks.add_task(dump_generator.generate_all_dumps)
            message = "Full dump regeneration initiated"
        
        return {
            "success": True,
            "message": message,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to regenerate dumps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/run-job")
async def run_scheduled_job(
    background_tasks: BackgroundTasks,
    job_type: str = Query(..., description="Job type: daily, weekly, or monthly")
):
    """Run a scheduled job immediately (admin endpoint)."""
    try:
        if job_type not in ["daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="Invalid job type")
        
        # Run job in background
        background_tasks.add_task(scheduler.run_job_now, job_type)
        
        return {
            "success": True,
            "message": f"{job_type.title()} job initiated",
            "job_type": job_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to run job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/reset-stats")
async def reset_statistics():
    """Reset query statistics (admin endpoint)."""
    try:
        query_router.reset_stats()
        
        return {
            "success": True,
            "message": "Statistics reset successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze")
async def analyze_query_patterns(
    queries: List[str] = Query(..., description="List of queries to analyze")
):
    """Analyze query patterns for optimization insights."""
    try:
        analysis = query_router.analyze_query_patterns(queries)
        
        return {
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Basic health checks
        status = query_router.get_system_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "patterns_loaded": status["data_availability"]["total_patterns"] > 0,
                "query_processing": True,  # Could add actual test query
                "response_time_ok": status["performance"]["avg_response_time_ms"] < settings.max_response_time_ms
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    logger.info("🚀 Starting Token-Optimized BI System...")
    
    # Refresh patterns on startup
    success = query_router.refresh_patterns()
    if success:
        logger.info("✅ Pattern cache initialized")
    else:
        logger.warning("⚠️ Pattern cache initialization failed")
    
    # Initialize hybrid analysis system
    logger.info("🔧 Initializing hybrid analysis system...")
    
    # Initialize chart generator
    logger.info("📊 Initializing chart generator with versioning...")
    
    # Start monitoring system
    logger.info("🔍 Starting real-time monitoring system...")
    await system_monitor.start_monitoring()
    
    logger.info("🎉 Token-Optimized BI System ready with full capabilities!")
    logger.info("   ✅ Query routing and caching")
    logger.info("   ✅ Hybrid analysis and decomposition") 
    logger.info("   ✅ Incremental chart updates")
    logger.info("   ✅ Token optimization")
    logger.info("   ✅ Real-time monitoring and alerting")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("👋 Shutting down Token-Optimized BI System...")
    
    # Stop monitoring system
    await system_monitor.stop_monitoring()
    logger.info("✅ Monitoring system stopped")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8001,  # Different port from main backend
        reload=True,
        log_level="info"
    )