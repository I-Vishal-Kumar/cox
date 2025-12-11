# SQL Query Generation System Prompt Update

## Changes Made

Updated the system prompt in [`generate_sql_query`](file:///home/jipl/Downloads/cox/co/backend/app/agents/tools.py#L211-L258) tool to include:

### 1. Database Environment Information
```
- Database: SQLite 3.x
- ORM: SQLAlchemy 1.4 (async)
- Execution: Queries are executed using SQLAlchemy's text() function with async sessions
```

### 2. Critical SQLite-Specific Rules

#### Date Modifiers (Most Important!)
- ✅ **CORRECT**: `date('now', '-28 days')` for 4 weeks ago
- ✅ **CORRECT**: `date('now', '-7 days')` for 1 week ago
- ❌ **WRONG**: `date('now', '-4 weeks')` - returns NULL!
- ❌ **WRONG**: `date('now', '-1 month')` - use '-30 days' instead

#### NULL Handling
- Always use `COALESCE(SUM(revenue), 0)` for aggregations
- Prevents NULL results when no data exists

#### Other SQLite Best Practices
- Proper JOIN syntax
- ROUND() for currency/percentages
- ORDER BY for sorting
- LIMIT for result caps
- Window functions for comparisons

## Impact

This update will help the LLM generate correct SQLite queries by:

1. **Preventing NULL date errors** - The most common issue we encountered
2. **Handling NULL aggregations** - Ensures consistent numeric results
3. **Following SQLite syntax** - Uses SQLite-compatible date functions
4. **Understanding execution context** - Knows it's using SQLAlchemy async

## Before vs After

### Before (Incorrect)
```sql
WHERE transaction_date >= date('now', '-4 weeks')  -- Returns NULL!
```

### After (Correct)
```sql
WHERE transaction_date >= date('now', '-28 days')  -- Works correctly
```

## Testing

The updated prompt has been deployed. Test with queries like:
- "Get F&I revenue for the last 4 weeks"
- "Show me data from last month"
- "Weekly trends for the past 6 weeks"

The agent should now generate correct SQLite date syntax automatically.
