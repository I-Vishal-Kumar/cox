"""High-performance file serving system for SQL dumps and cached responses."""

import mmap
import json
import gzip
from typing import Dict, List, Any, Optional, BinaryIO
from pathlib import Path
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio

from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

class FastFileServer:
    """High-performance file server with memory mapping and concurrent access."""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or settings.max_concurrent_requests
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # File cache for frequently accessed files
        self.file_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "files_cached": 0,
            "total_requests": 0,
            "avg_response_time_ms": 0
        }
    
    async def serve_dump_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Serve a SQL dump file with high performance.
        
        Args:
            file_path: Path to the dump file
            
        Returns:
            File contents as dictionary or None if not found
        """
        start_time = time.time()
        
        try:
            self.cache_stats["total_requests"] += 1
            
            # Check if file is in cache
            if file_path in self.file_cache:
                self.cache_stats["hits"] += 1
                response_time = (time.time() - start_time) * 1000
                self._update_avg_response_time(response_time)
                
                logger.debug(f"File cache hit: {file_path}")
                return self.file_cache[file_path].copy()
            
            # Load file asynchronously
            loop = asyncio.get_event_loop()
            file_data = await loop.run_in_executor(
                self.executor,
                self._load_file_optimized,
                file_path
            )
            
            if file_data:
                # Cache the file data
                self.file_cache[file_path] = file_data
                self.cache_stats["files_cached"] += 1
                self.cache_stats["misses"] += 1
                
                response_time = (time.time() - start_time) * 1000
                self._update_avg_response_time(response_time)
                
                logger.debug(f"File loaded and cached: {file_path} ({response_time:.1f}ms)")
                return file_data.copy()
            
            return None
            
        except Exception as e:
            logger.error(f"Error serving file {file_path}: {e}")
            return None
    
    def _load_file_optimized(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load file using optimized methods (memory mapping for large files)."""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            file_size = path.stat().st_size
            
            # Use memory mapping for larger files (>1MB)
            if file_size > 1024 * 1024:
                return self._load_with_mmap(path)
            else:
                return self._load_standard(path)
                
        except Exception as e:
            logger.error(f"File loading error: {e}")
            return None
    
    def _load_with_mmap(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load file using memory mapping for better performance."""
        try:
            with open(file_path, 'rb') as f:
                # Memory map the file
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                    if file_path.suffix == '.gz':
                        # Decompress gzipped file
                        data = gzip.decompress(mmapped_file.read())
                        return json.loads(data.decode('utf-8'))
                    else:
                        # Regular JSON file
                        return json.loads(mmapped_file.read().decode('utf-8'))
                        
        except Exception as e:
            logger.error(f"Memory mapping error for {file_path}: {e}")
            return None
    
    def _load_standard(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load file using standard file operations."""
        try:
            if file_path.suffix == '.gz':
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
        except Exception as e:
            logger.error(f"Standard loading error for {file_path}: {e}")
            return None
    
    async def serve_multiple_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Serve multiple files concurrently.
        
        Args:
            file_paths: List of file paths to serve
            
        Returns:
            Dictionary mapping file paths to their contents
        """
        start_time = time.time()
        
        try:
            # Create tasks for concurrent loading
            tasks = [
                self.serve_dump_file(file_path) 
                for file_path in file_paths
            ]
            
            # Execute concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            file_data = {}
            for file_path, result in zip(file_paths, results):
                if isinstance(result, Exception):
                    logger.error(f"Error loading {file_path}: {result}")
                    file_data[file_path] = None
                else:
                    file_data[file_path] = result
            
            response_time = (time.time() - start_time) * 1000
            logger.info(f"Served {len(file_paths)} files concurrently in {response_time:.1f}ms")
            
            return file_data
            
        except Exception as e:
            logger.error(f"Concurrent file serving error: {e}")
            return {}
    
    def _update_avg_response_time(self, response_time_ms: float) -> None:
        """Update running average response time."""
        current_avg = self.cache_stats["avg_response_time_ms"]
        total_requests = self.cache_stats["total_requests"]
        
        if total_requests == 1:
            self.cache_stats["avg_response_time_ms"] = response_time_ms
        else:
            self.cache_stats["avg_response_time_ms"] = (
                (current_avg * (total_requests - 1) + response_time_ms) / total_requests
            )
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get file server performance statistics."""
        total_requests = self.cache_stats["total_requests"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "performance": {
                "total_requests": total_requests,
                "cache_hit_rate_percent": round(hit_rate, 2),
                "cache_hits": self.cache_stats["hits"],
                "cache_misses": self.cache_stats["misses"],
                "avg_response_time_ms": round(self.cache_stats["avg_response_time_ms"], 2)
            },
            "cache": {
                "files_cached": self.cache_stats["files_cached"],
                "current_cache_size": len(self.file_cache)
            },
            "configuration": {
                "max_workers": self.max_workers,
                "target_response_time_ms": settings.max_response_time_ms
            }
        }
    
    def clear_cache(self) -> None:
        """Clear the file cache."""
        cache_size = len(self.file_cache)
        self.file_cache.clear()
        logger.info(f"Cleared file cache ({cache_size} files)")
    
    async def preload_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Preload frequently accessed files into cache."""
        logger.info(f"Preloading {len(file_paths)} files...")
        
        preload_stats = {
            "files_processed": 0,
            "files_loaded": 0,
            "files_failed": 0,
            "total_time_ms": 0
        }
        
        start_time = time.time()
        
        for file_path in file_paths:
            try:
                result = await self.serve_dump_file(file_path)
                preload_stats["files_processed"] += 1
                
                if result:
                    preload_stats["files_loaded"] += 1
                else:
                    preload_stats["files_failed"] += 1
                    
            except Exception as e:
                logger.error(f"Error preloading {file_path}: {e}")
                preload_stats["files_failed"] += 1
        
        preload_stats["total_time_ms"] = (time.time() - start_time) * 1000
        
        logger.info(f"Preload complete: {preload_stats}")
        return preload_stats

class ResponseOptimizer:
    """Optimizes responses for fast delivery to frontend."""
    
    def __init__(self):
        self.compression_threshold = 1024  # Compress responses larger than 1KB
    
    def optimize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize response for fast frontend delivery.
        
        Args:
            response: Original response
            
        Returns:
            Optimized response
        """
        try:
            optimized = response.copy()
            
            # Add performance metadata
            optimized["performance"] = {
                "optimized": True,
                "optimization_timestamp": time.time(),
                "original_size_estimate": len(json.dumps(response, default=str))
            }
            
            # Optimize data structure
            if "data" in optimized:
                optimized["data"] = self._optimize_data_structure(optimized["data"])
            
            # Optimize chart configurations
            if "charts" in optimized:
                optimized["charts"] = self._optimize_chart_configs(optimized["charts"])
            
            # Add compression hints
            response_size = len(json.dumps(optimized, default=str))
            optimized["performance"]["optimized_size_estimate"] = response_size
            optimized["performance"]["should_compress"] = response_size > self.compression_threshold
            
            return optimized
            
        except Exception as e:
            logger.error(f"Response optimization error: {e}")
            return response
    
    def _optimize_data_structure(self, data: Any) -> Any:
        """Optimize data structure for frontend consumption."""
        if isinstance(data, dict):
            if "raw" in data and "processed" in data:
                # For data with both raw and processed, prioritize processed
                return {
                    "processed": data["processed"],
                    "raw": data["raw"][:100] if isinstance(data["raw"], list) else data["raw"],  # Limit raw data
                    "summary": data.get("summary", {})
                }
        
        return data
    
    def _optimize_chart_configs(self, charts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize chart configurations for faster rendering."""
        optimized_charts = []
        
        for chart in charts:
            optimized_chart = chart.copy()
            
            # Add performance hints
            config = optimized_chart.get("config", {})
            if "options" not in config:
                config["options"] = {}
            
            # Add performance optimizations
            config["options"]["performance"] = {
                "optimized": True,
                "lazy_loading": True,
                "data_decimation": len(config.get("data", {}).get("labels", [])) > 100
            }
            
            optimized_chart["config"] = config
            optimized_charts.append(optimized_chart)
        
        return optimized_charts
    
    def create_response_metadata(
        self, 
        query: str, 
        processing_time_ms: float,
        data_source: str = "cache"
    ) -> Dict[str, Any]:
        """Create comprehensive response metadata."""
        return {
            "query_hash": hash(query) % 1000000,  # Simple hash for tracking
            "processing_time_ms": round(processing_time_ms, 2),
            "data_source": data_source,
            "timestamp": time.time(),
            "performance_target_met": processing_time_ms < settings.max_response_time_ms,
            "optimization_applied": True
        }

# Test functions
async def test_fast_server():
    """Test the fast file server system."""
    print("🧪 Testing Fast File Server System")
    print("=" * 50)
    
    server = FastFileServer(max_workers=4)
    optimizer = ResponseOptimizer()
    
    # Test file paths (using existing dump files)
    test_files = [
        "sql_dumps/sales_analytics/top_models_by_region.json",
        "sql_dumps/kpi_monitoring/health_scores.json",
        "sql_dumps/inventory_management/stock_levels.json"
    ]
    
    print(f"\n📁 Testing individual file serving...")
    
    # Test individual file serving
    for file_path in test_files:
        start_time = time.time()
        result = await server.serve_dump_file(file_path)
        response_time = (time.time() - start_time) * 1000
        
        if result:
            data_size = len(result.get("data", []))
            print(f"✅ {file_path}: {data_size} records ({response_time:.1f}ms)")
        else:
            print(f"❌ {file_path}: Not found")
    
    # Test concurrent file serving
    print(f"\n🚀 Testing concurrent file serving...")
    start_time = time.time()
    concurrent_results = await server.serve_multiple_files(test_files)
    total_time = (time.time() - start_time) * 1000
    
    successful_loads = sum(1 for result in concurrent_results.values() if result is not None)
    print(f"✅ Loaded {successful_loads}/{len(test_files)} files concurrently in {total_time:.1f}ms")
    
    # Test response optimization
    print(f"\n⚡ Testing response optimization...")
    
    if concurrent_results:
        sample_response = {
            "success": True,
            "data": {"raw": list(concurrent_results.values())[0].get("data", [])},
            "charts": [{"config": {"data": {"labels": ["A", "B", "C"]}}}]
        }
        
        optimized = optimizer.optimize_response(sample_response)
        
        original_size = optimized["performance"]["original_size_estimate"]
        optimized_size = optimized["performance"]["optimized_size_estimate"]
        
        print(f"Original size: {original_size} bytes")
        print(f"Optimized size: {optimized_size} bytes")
        print(f"Should compress: {optimized['performance']['should_compress']}")
    
    # Display server statistics
    print(f"\n📊 Server Statistics:")
    stats = server.get_server_stats()
    perf = stats["performance"]
    cache = stats["cache"]
    
    print(f"Total requests: {perf['total_requests']}")
    print(f"Cache hit rate: {perf['cache_hit_rate_percent']:.1f}%")
    print(f"Avg response time: {perf['avg_response_time_ms']:.2f}ms")
    print(f"Files cached: {cache['files_cached']}")
    print(f"Current cache size: {cache['current_cache_size']}")

if __name__ == "__main__":
    asyncio.run(test_fast_server())