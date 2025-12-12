#!/usr/bin/env python3
"""
Script to regenerate SQL dumps when database changes.
This script can be run manually or scheduled as a cron job.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

from dump_generator import DumpGenerator
from database import test_database_connection
from config import ensure_directories

async def regenerate_all_dumps():
    """Regenerate all SQL dumps."""
    print("🔄 Starting complete dump regeneration...")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    
    # Ensure directories exist
    ensure_directories()
    
    # Test database connection
    print("🔗 Testing database connection...")
    if not await test_database_connection():
        print("❌ Database connection failed!")
        return False
    print("✅ Database connection successful")
    
    # Generate dumps
    generator = DumpGenerator()
    results = await generator.generate_all_dumps()
    
    if results["success"]:
        print(f"✅ Successfully regenerated {len(results['generated_files'])} dump files")
        print(f"📊 Categories processed: {len(set(Path(f).parent.name for f in results['generated_files']))}")
        
        if results["errors"]:
            print(f"⚠️  {len(results['errors'])} errors occurred:")
            for error in results["errors"]:
                print(f"   - {error}")
        
        return True
    else:
        print(f"❌ Dump regeneration failed: {results.get('error', 'Unknown error')}")
        return False

async def regenerate_category_dumps(category: str):
    """Regenerate dumps for a specific category."""
    print(f"🔄 Regenerating dumps for category: {category}")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    
    # Test database connection
    if not await test_database_connection():
        print("❌ Database connection failed!")
        return False
    
    # Generate dumps for category
    generator = DumpGenerator()
    results = await generator.refresh_specific_category(category)
    
    if results["success"]:
        print(f"✅ Successfully regenerated {len(results['generated_files'])} files for {category}")
        
        if results["errors"]:
            print(f"⚠️  {len(results['errors'])} errors occurred:")
            for error in results["errors"]:
                print(f"   - {error}")
        
        return True
    else:
        print(f"❌ Category regeneration failed: {results.get('error', 'Unknown error')}")
        return False

def list_available_categories():
    """List available dump categories."""
    from sql_queries import SQLQueryTemplates
    
    templates = SQLQueryTemplates()
    categories = templates.get_all_queries().keys()
    
    print("📋 Available dump categories:")
    for category in categories:
        queries = templates.get_all_queries()[category]
        print(f"   - {category} ({len(queries)} queries)")

async def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Regenerate SQL dumps for token-optimized BI system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python regenerate_dumps.py                    # Regenerate all dumps
  python regenerate_dumps.py --category sales_analytics  # Regenerate specific category
  python regenerate_dumps.py --list             # List available categories
  python regenerate_dumps.py --test             # Test database connection only
        """
    )
    
    parser.add_argument(
        "--category", 
        type=str, 
        help="Regenerate dumps for specific category only"
    )
    
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="List available dump categories"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Test database connection only"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_available_categories()
        return
    
    if args.test:
        print("🔗 Testing database connection...")
        if await test_database_connection():
            print("✅ Database connection successful")
            return
        else:
            print("❌ Database connection failed")
            sys.exit(1)
    
    if args.category:
        success = await regenerate_category_dumps(args.category)
    else:
        success = await regenerate_all_dumps()
    
    if not success:
        sys.exit(1)
    
    print("🎉 Dump regeneration completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())