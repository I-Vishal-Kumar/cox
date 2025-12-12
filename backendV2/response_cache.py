"""High-performance response serving and caching system."""

import json
import gzip
import hashlib
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

class ResponseCache:
    """High-performance response cache with compression and memory optimization."""
    
    def __init__(self, cache_dir: str = None, max_memory_cache_mb: int = 100):
        self.cache_dir = Path(cache_dir or settings.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory cache for frequently accessed responses
        self.memory_cache = {}
        self.max_memory_cache_size = max_memory_cache_mb * 1024 * 1024  # Convert to bytes
        self.current_memory_usage = 0
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "disk_hits": 0,
            "compressions": 0,
            "total_requests": 0,
            "avg_response_time_ms": 0,
            "cache_size_mb": 0,
            "last_cleanup": datetime.now().isoformat()
        }
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def _generate_cache_key(self, query: str, options: Dict[str, Any] = None) -> str:
        """Generate a unique cache key for the query and options."""
        # Normalize query
        normalized_query = query.lower().strip()
        
        # Include options in cache key if provided
        cache_data = {"query": normalized_query}
        if options:
            cache_data["options"] = options
        
        # Generate hash
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        # Use first 2 characters for subdirectory to avoid too many files in one dir
        subdir = cache_key[:2]
        cache_subdir = self.cache_dir / subdir
        cache_subdir.mkdir(exist_ok=True)
        return cache_subdir / f"{cache_key}.json.gz"
    
    def _compress_response(self, response: Dict[str, Any]) -> bytes:
        """Compress response data using gzip."""
        json_data = json.dumps(response, separators=(',', ':'), default=str)
        compressed = gzip.compress(json_data.encode('utf-8'))
        self.stats["compressions"] += 1
        return compressed
    
    def _decompress_response(self, compressed_data: bytes) -> Dict[str, Any]:
        """Decompress response data."""
        json_data = gzip.decompress(compressed_data).decode('utf-8')
        return json.loads(json_data)
    
    async def get_cached_response(
        self, 
        query: str, 
        options: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for a query.
        
        Args:
            query: User query string
            options: Query options
            
        Returns:
            Cached response or None if not found
        """
        start_time = time.time()
        cache_key = self._generate_cache_key(query, options)
        
        try:
            self.stats["total_requests"] += 1
            
            # Check memory cache first
            if cache_key in self.memory_cache:
                response = self.memory_cache[cache_key].copy()
                response["metadata"]["cache_source"] = "memory"
                response["metadata"]["response_time_ms"] = (time.time() - start_time) * 1000
                
                self.stats["hits"] += 1
                self.stats["memory_hits"] += 1
                
                logger.debug(f"Memory cache hit for query: '{query[:50]}...'")
                return response
            
            # Check disk cache
            cache_file = self._get_cache_file_path(cache_key)
            if cache_file.exists():
                # Load from disk asynchronously
                loop = asyncio.get_event_loop()
                compressed_data = await loop.run_in_executor(
                    self.executor, 
                    self._load_from_disk, 
                    cache_file
                )
                
                if compressed_data:
                    response = self._decompress_response(compressed_data)
                    response["metadata"]["cache_source"] = "disk"
                    response["metadata"]["response_time_ms"] = (time.time() - start_time) * 1000
                    
                    # Add to memory cache if there's space
                    await self._add_to_memory_cache(cache_key, response)
                    
                    self.stats["hits"] += 1
                    self.stats["disk_hits"] += 1
                    
                    logger.debug(f"Disk cache hit for query: '{query[:50]}...'")
                    return response
            
            # Cache miss
            self.stats["misses"] += 1
            logger.debug(f"Cache miss for query: '{query[:50]}...'")
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            self.stats["misses"] += 1
            return None
        finally:
            # Update average response time
            response_time = (time.time() - start_time) * 1000
            self._update_avg_response_time(response_time)
    
    async def cache_response(
        self, 
        query: str, 
        response: Dict[str, Any], 
        options: Dict[str, Any] = None,
        ttl_hours: int = 24
    ) -> bool:
        """
        Cache a response for future use.
        
        Args:
            query: User query string
            response: Response to cache
            options: Query options
            ttl_hours: Time to live in hours
            
        Returns:
            True if cached successfully
        """
        try:
            cache_key = self._generate_cache_key(query, options)
            
            # Add cache metadata
            cached_response = response.copy()
            cached_response["cache_metadata"] = {
                "cached_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=ttl_hours)).isoformat(),
                "cache_key": cache_key,
                "query_hash": cache_key[:8]
            }
            
            # Save to disk asynchronously
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor,
                self._save_to_disk,
                cache_key,
                cached_response
            )
            
            if success:
                # Add to memory cache if there's space
                await self._add_to_memory_cache(cache_key, cached_response)
                logger.debug(f"Cached response for query: '{query[:50]}...'")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            return False
    
    def _load_from_disk(self, cache_file: Path) -> Optional[bytes]:
        """Load compressed data from disk."""
        try:
            with open(cache_file, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Disk read error: {e}")
            return None
    
    def _save_to_disk(self, cache_key: str, response: Dict[str, Any]) -> bool:
        """Save compressed response to disk."""
        try:
            cache_file = self._get_cache_file_path(cache_key)
            compressed_data = self._compress_response(response)
            
            with open(cache_file, 'wb') as f:
                f.write(compressed_data)
            
            return True
        except Exception as e:
            logger.error(f"Disk write error: {e}")
            return False
    
    async def _add_to_memory_cache(self, cache_key: str, response: Dict[str, Any]) -> None:
        """Add response to memory cache with size management."""
        try:
            # Estimate response size
            response_size = len(json.dumps(response, default=str).encode('utf-8'))
            
            # Check if we have space
            if self.current_memory_usage + response_size > self.max_memory_cache_size:
                await self._evict_memory_cache(response_size)
            
            # Add to cache
            self.memory_cache[cache_key] = response.copy()
            self.current_memory_usage += response_size
            
        except Exception as e:
            logger.error(f"Memory cache error: {e}")
    
    async def _evict_memory_cache(self, needed_space: int) -> None:
        """Evict items from memory cache to make space."""
        # Simple LRU eviction - remove oldest items
        # In production, could use more sophisticated algorithms
        
        items_to_remove = []
        space_freed = 0
        
        for cache_key in list(self.memory_cache.keys()):
            if space_freed >= needed_space:
                break
            
            response = self.memory_cache[cache_key]
            item_size = len(json.dumps(response, default=str).encode('utf-8'))
            
            items_to_remove.append((cache_key, item_size))
            space_freed += item_size
        
        # Remove items
        for cache_key, item_size in items_to_remove:
            del self.memory_cache[cache_key]
            self.current_memory_usage -= item_size
        
        logger.debug(f"Evicted {len(items_to_remove)} items from memory cache, freed {space_freed} bytes")
    
    def _update_avg_response_time(self, response_time_ms: float) -> None:
        """Update running average response time."""
        current_avg = self.stats["avg_response_time_ms"]
        total_requests = self.stats["total_requests"]
        
        if total_requests == 1:
            self.stats["avg_response_time_ms"] = response_time_ms
        else:
            self.stats["avg_response_time_ms"] = (
                (current_avg * (total_requests - 1) + response_time_ms) / total_requests
            )
    
    async def cleanup_expired_cache(self) -> Dict[str, Any]:
        """Clean up expired cache entries."""
        logger.info("Starting cache cleanup...")
        
        cleanup_stats = {
            "files_checked": 0,
            "files_removed": 0,
            "space_freed_mb": 0,
            "errors": 0
        }
        
        try:
            # Check all cache files
            for cache_file in self.cache_dir.rglob("*.json.gz"):
                cleanup_stats["files_checked"] += 1
                
                try:
                    # Load and check expiration
                    compressed_data = self._load_from_disk(cache_file)
                    if compressed_data:
                        response = self._decompress_response(compressed_data)
                        
                        # Check if expired
                        expires_at = response.get("cache_metadata", {}).get("expires_at")
                        if expires_at:
                            expiry_time = datetime.fromisoformat(expires_at)
                            if datetime.now() > expiry_time:
                                # Remove expired file
                                file_size = cache_file.stat().st_size
                                cache_file.unlink()
                                
                                cleanup_stats["files_removed"] += 1
                                cleanup_stats["space_freed_mb"] += file_size / (1024 * 1024)
                
                except Exception as e:
                    logger.error(f"Error processing cache file {cache_file}: {e}")
                    cleanup_stats["errors"] += 1
            
            self.stats["last_cleanup"] = datetime.now().isoformat()
            logger.info(f"Cache cleanup complete: {cleanup_stats}")
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            cleanup_stats["errors"] += 1
        
        return cleanup_stats
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        # Calculate cache hit rate
        total_requests = self.stats["total_requests"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate cache size
        cache_size_bytes = sum(
            f.stat().st_size for f in self.cache_dir.rglob("*.json.gz")
        )
        cache_size_mb = cache_size_bytes / (1024 * 1024)
        
        return {
            "performance": {
                "hit_rate_percent": round(hit_rate, 2),
                "total_requests": total_requests,
                "cache_hits": self.stats["hits"],
                "cache_misses": self.stats["misses"],
                "memory_hits": self.stats["memory_hits"],
                "disk_hits": self.stats["disk_hits"],
                "avg_response_time_ms": round(self.stats["avg_response_time_ms"], 2)
            },
            "storage": {
                "disk_cache_size_mb": round(cache_size_mb, 2),
                "memory_cache_size_mb": round(self.current_memory_usage / (1024 * 1024), 2),
                "memory_cache_items": len(self.memory_cache),
                "compression_count": self.stats["compressions"]
            },
            "maintenance": {
                "last_cleanup": self.stats["last_cleanup"],
                "cache_directory": str(self.cache_dir)
            }
        }
    
    async def preload_common_queries(self, common_queries: List[str]) -> Dict[str, Any]:
        """Preload common queries into memory cache."""
        logger.info(f"Preloading {len(common_queries)} common queries...")
        
        preload_stats = {
            "queries_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "memory_loaded": 0
        }
        
        for query in common_queries:
            try:
                cached_response = await self.get_cached_response(query)
                preload_stats["queries_processed"] += 1
                
                if cached_response:
                    preload_stats["cache_hits"] += 1
                    if cached_response["metadata"].get("cache_source") == "memory":
                        preload_stats["memory_loaded"] += 1
                else:
                    preload_stats["cache_misses"] += 1
                    
            except Exception as e:
                logger.error(f"Error preloading query '{query}': {e}")
        
        logger.info(f"Preload complete: {preload_stats}")
        return preload_stats

# Test functions
async def test_response_cache():
    """Test the response cache system."""
    print("🧪 Testing Response Cache System")
    print("=" * 50)
    
    cache = ResponseCache(cache_dir="test_cache", max_memory_cache_mb=10)
    
    # Test data
    test_queries = [
        "top selling models by region",
        "KPI health scores",
        "inventory stock levels",
        "CEO weekly summary"
    ]
    
    test_response = {
        "success": True,
        "data": [{"test": "data"}],
        "metadata": {"generated_at": datetime.now().isoformat()}
    }
    
    print(f"\n💾 Testing cache operations...")
    
    # Test caching
    for query in test_queries:
        success = await cache.cache_response(query, test_response)
        print(f"Cache store '{query}': {'✅' if success else '❌'}")
    
    # Test retrieval
    print(f"\n🔍 Testing cache retrieval...")
    for query in test_queries:
        cached = await cache.get_cached_response(query)
        if cached:
            source = cached["metadata"].get("cache_source", "unknown")
            print(f"Cache hit '{query}': ✅ (source: {source})")
        else:
            print(f"Cache miss '{query}': ❌")
    
    # Test cache statistics
    print(f"\n📊 Cache Statistics:")
    stats = cache.get_cache_stats()
    perf = stats["performance"]
    storage = stats["storage"]
    
    print(f"Hit rate: {perf['hit_rate_percent']:.1f}%")
    print(f"Total requests: {perf['total_requests']}")
    print(f"Memory hits: {perf['memory_hits']}")
    print(f"Disk hits: {perf['disk_hits']}")
    print(f"Disk cache size: {storage['disk_cache_size_mb']:.2f} MB")
    print(f"Memory cache size: {storage['memory_cache_size_mb']:.2f} MB")
    print(f"Avg response time: {perf['avg_response_time_ms']:.2f}ms")
    
    # Test preloading
    print(f"\n🚀 Testing preload...")
    preload_stats = await cache.preload_common_queries(test_queries[:2])
    print(f"Preload results: {preload_stats}")
    
    # Test cleanup
    print(f"\n🧹 Testing cleanup...")
    cleanup_stats = await cache.cleanup_expired_cache()
    print(f"Cleanup results: {cleanup_stats}")

if __name__ == "__main__":
    asyncio.run(test_response_cache())