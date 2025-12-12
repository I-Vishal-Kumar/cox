#!/usr/bin/env python3
"""Startup script for the Token-Optimized BI API server."""

import asyncio
import uvicorn
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import ensure_directories
from dump_generator import DumpGenerator
from database import test_database_connection

async def initialize_system():
    """Initialize the system before starting the server."""
    print("🔧 Initializing Token-Optimized BI System...")
    
    # Ensure directories exist
    ensure_directories()
    print("✅ Directory structure verified")
    
    # Test database connection
    print("🔗 Testing database connection...")
    if await test_database_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed!")
        return False
    
    # Check if dumps exist, generate if needed
    dumps_dir = Path("sql_dumps")
    if not dumps_dir.exists() or not list(dumps_dir.glob("*/*.json")):
        print("📊 No SQL dumps found, generating initial dumps...")
        generator = DumpGenerator()
        result = await generator.generate_all_dumps()
        
        if result["success"]:
            print(f"✅ Generated {len(result['generated_files'])} dump files")
        else:
            print(f"❌ Dump generation failed: {result.get('error')}")
            return False
    else:
        print("✅ SQL dumps found")
    
    print("🎉 System initialization complete!")
    return True

def main():
    """Main function to start the server."""
    print("🚀 Starting Token-Optimized BI System")
    print("=" * 50)
    
    # Initialize system
    if not asyncio.run(initialize_system()):
        print("❌ System initialization failed, exiting...")
        sys.exit(1)
    
    print("\n🌐 Starting API server...")
    print("📍 Server will be available at: http://localhost:8001")
    print("📖 API documentation at: http://localhost:8001/docs")
    print("🔍 Health check at: http://localhost:8001/health")
    print("\nPress Ctrl+C to stop the server")
    
    # Start the server
    try:
        uvicorn.run(
            "api_server:app",
            host="0.0.0.0",
            port=8001,
            reload=False,  # Set to True for development
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()