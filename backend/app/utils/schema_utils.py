"""Utility functions for database schema operations."""

from typing import Dict, List, Optional
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_database_schema(db_session: AsyncSession) -> str:
    """
    Dynamically fetch database schema from the database.
    
    Args:
        db_session: Active database session
        
    Returns:
        Formatted string containing database schema information
    """
    try:
        # Get all table names
        result = await db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        tables = [row[0] for row in result.fetchall()]
        
        schema_parts = ["Tables in the Cox Automotive database:\n"]
        
        for idx, table_name in enumerate(tables, 1):
            # Get table info
            table_info_result = await db_session.execute(
                text(f"PRAGMA table_info({table_name})")
            )
            columns = table_info_result.fetchall()
            
            schema_parts.append(f"\n{idx}. {table_name}")
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                
                # Build column description
                col_desc = f"   - {col_name}: {col_type}"
                
                if is_pk:
                    col_desc += " (Primary Key)"
                if not_null and not is_pk:
                    col_desc += " (NOT NULL)"
                    
                schema_parts.append(col_desc)
            
            # Get foreign keys
            fk_result = await db_session.execute(
                text(f"PRAGMA foreign_key_list({table_name})")
            )
            foreign_keys = fk_result.fetchall()
            
            for fk in foreign_keys:
                fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                schema_parts.append(
                    f"   - {from_col}: Foreign Key -> {ref_table}.{to_col}"
                )
        
        return "\n".join(schema_parts)
        
    except Exception as e:
        # Fallback to basic schema if dynamic fetch fails
        return get_fallback_schema()


def get_fallback_schema() -> str:
    """
    Fallback schema in case dynamic fetch fails.
    
    Returns:
        Basic schema string
    """
    return """Tables in the Cox Automotive database:

1. dealers - Dealer information
2. fni_transactions - Finance & Insurance transactions
3. shipments - Logistics and shipment data
4. plants - Manufacturing plant information
5. plant_downtime - Plant downtime records
6. marketing_campaigns - Marketing campaign data
7. service_appointments - Service appointment records
8. kpi_metrics - KPI tracking metrics

Use PRAGMA table_info(table_name) to get detailed column information."""


# Cache for schema to avoid repeated database calls
_schema_cache: Optional[str] = None


async def get_cached_schema(db_session: AsyncSession, force_refresh: bool = False) -> str:
    """
    Get database schema with caching.
    
    Args:
        db_session: Active database session
        force_refresh: Force refresh of cached schema
        
    Returns:
        Formatted database schema string
    """
    global _schema_cache
    
    if _schema_cache is None or force_refresh:
        _schema_cache = await get_database_schema(db_session)
    
    return _schema_cache
