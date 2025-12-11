# JSON-Only Response Mode Guide

## Overview

The `/api/v1/chat` endpoint now supports a **JSON-only response mode** that returns clean JSON data without conversational text. This is perfect for frontend dashboard integrations.

---

## How It Works

When your query includes specific keywords, the agent will return ONLY the JSON data from the tool, with no additional explanation or formatting.

### Trigger Keywords

Include any of these phrases in your query:
- `"return as JSON"`
- `"give me JSON"`  
- `"format as JSON"`
- `"JSON only"`
- `"raw data"`

---

## Usage Examples

### Example 1: Weekly Trends (JSON Only)

**Request:**
```typescript
const response = await fetch('/api/v1/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Get weekly F&I revenue trends for the last 4 weeks, return as JSON",
    conversation_id: `dashboard_${Date.now()}`
  })
});
```

**Response (in message field):**
```json
[
  {
    "week": "Week 1",
    "midwest": 318012.89,
    "northeast": 206226.81,
    "southeast": 104589.48,
    "west": 124283.92
  },
  {
    "week": "Week 2",
    "midwest": 408745.91,
    "northeast": 265080.84,
    "southeast": 143632.94,
    "west": 157990.13
  }
]
```

### Example 2: Enhanced KPIs (JSON Only)

**Request:**
```typescript
const response = await fetch('/api/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: "Get enhanced KPI data for this week, JSON only",
    conversation_id: `dashboard_kpi_${Date.now()}`
  })
});
```

**Response:**
```json
{
  "current_period": {
    "total_revenue": 450000,
    "avg_penetration": 68.5,
    "total_transactions": 1250,
    "period_label": "This Week"
  },
  "previous_period": {
    "total_revenue": 420000,
    "avg_penetration": 65.2,
    "total_transactions": 1180,
    "period_label": "Last Week"
  },
  "changes": {
    "revenue_change_pct": 7.14,
    "penetration_change_pct": 5.06,
    "transactions_change_pct": 5.93
  }
}
```

### Example 3: Filtered Data (JSON Only)

**Request:**
```typescript
const response = await fetch('/api/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: "Get F&I data for Midwest region this week, raw data",
    conversation_id: `dashboard_filtered_${Date.now()}`
  })
});
```

**Response:**
```json
[
  {
    "dealer_name": "Premium Auto Group",
    "region": "Midwest",
    "finance_manager": "John Smith",
    "total_revenue": 45000,
    "avg_penetration": 72.5,
    "transaction_count": 125
  }
]
```

---

## Frontend Integration

### React/TypeScript Service

```typescript
// dashboardService.ts
export class DashboardService {
  private async getJSONData(query: string): Promise<any> {
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: `${query}, return as JSON`,  // Add JSON trigger
        conversation_id: `dashboard_${Date.now()}`
      })
    });

    const data = await response.json();
    
    // The agent returns clean JSON in the final AIMessage content
    const messages = JSON.parse(data.message).messages;
    const finalMessage = messages[messages.length - 1];
    
    // Parse the JSON from the content
    return JSON.parse(finalMessage.content);
  }

  async getWeeklyTrends(weeks: number = 4) {
    return this.getJSONData(
      `Get weekly F&I revenue trends for the last ${weeks} weeks`
    );
  }

  async getEnhancedKPIs(period: string = 'this_week') {
    return this.getJSONData(
      `Get enhanced KPI data for ${period.replace('_', ' ')}`
    );
  }

  async getFilteredData(filters: {
    time_period?: string;
    regions?: string[];
    dealer_ids?: number[];
  }) {
    let query = `Get F&I data for ${filters.time_period || 'this week'}`;
    
    if (filters.regions) {
      query += ` in ${filters.regions.join(', ')} regions`;
    }
    
    if (filters.dealer_ids) {
      query += ` for dealers ${filters.dealer_ids.join(', ')}`;
    }
    
    return this.getJSONData(query);
  }
}
```

### Usage in Components

```typescript
// In your React component
const Dashboard = () => {
  const [weeklyTrends, setWeeklyTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const service = new DashboardService();
    
    service.getWeeklyTrends(4)
      .then(data => {
        setWeeklyTrends(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Failed to load trends:', error);
        setLoading(false);
      });
  }, []);
  
  if (loading) return <LoadingSkeleton />;
  
  return <WeeklyTrendChart data={weeklyTrends} />;
};
```

---

## Comparison: Normal vs JSON-Only Mode

### Normal Mode (Conversational)

**Query:** `"Get weekly F&I revenue trends for the last 4 weeks"`

**Response:**
```
Here are the F&I revenue trends for the last 4 weeks:

- Week 1: 
  - Midwest: $318,012.89
  - Northeast: $206,226.81
  ...

Please note that the data for Week 5 might not be complete...
```

### JSON-Only Mode

**Query:** `"Get weekly F&I revenue trends for the last 4 weeks, return as JSON"`

**Response:**
```json
[
  {
    "week": "Week 1",
    "midwest": 318012.89,
    "northeast": 206226.81,
    ...
  }
]
```

---

## Best Practices

### 1. Always Include JSON Trigger
```typescript
// ✅ Good
message: "Get weekly trends, return as JSON"

// ❌ Bad (will get conversational response)
message: "Get weekly trends"
```

### 2. Use Unique Conversation IDs
```typescript
// ✅ Good - unique per request
conversation_id: `dashboard_${Date.now()}`

// ❌ Bad - reusing same ID
conversation_id: "dashboard_session"
```

### 3. Handle Parsing Errors
```typescript
try {
  const data = JSON.parse(finalMessage.content);
  return data;
} catch (error) {
  console.error('Failed to parse JSON:', error);
  // Fallback or retry logic
}
```

### 4. Add Loading States
```typescript
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

// Show loading spinner while fetching
if (loading) return <Spinner />;
if (error) return <ErrorMessage error={error} />;
```

---

## Supported Dashboard Tools

All dashboard tools support JSON-only mode:

1. ✅ `get_weekly_fni_trends` - Weekly revenue trends
2. ✅ `get_enhanced_kpi_data` - KPI comparisons
3. ✅ `get_filtered_fni_data` - Filtered F&I data

---

## Troubleshooting

### Issue: Getting conversational text instead of JSON

**Solution:** Make sure you include a JSON trigger keyword:
```typescript
message: "Get weekly trends, return as JSON"  // ✅
```

### Issue: JSON parsing fails

**Solution:** Check the message structure:
```typescript
const messages = JSON.parse(data.message).messages;
const finalMessage = messages[messages.length - 1];
console.log('Content:', finalMessage.content);  // Debug
```

### Issue: Empty or null data

**Solution:** Check if the tool was called successfully:
```typescript
const toolMessage = messages.find(m => m.name === 'get_weekly_fni_trends');
if (!toolMessage) {
  console.error('Tool was not called');
}
```

---

## Migration Guide

### Before (Hardcoded Data)
```typescript
const weeklyTrends = [
  { week: "Week 1", midwest: 125000, ... }
];
```

### After (Dynamic JSON)
```typescript
const service = new DashboardService();
const weeklyTrends = await service.getWeeklyTrends(4);
```

---

## Performance Considerations

- **Caching**: Use TanStack Query or similar for client-side caching
- **Debouncing**: Debounce filter changes to avoid excessive API calls
- **Pagination**: For large datasets, consider adding LIMIT to queries
- **Error Retry**: Implement exponential backoff for failed requests

---

## Next Steps

1. ✅ Update frontend to use JSON-only mode
2. ✅ Remove hardcoded data
3. ✅ Add loading states
4. ✅ Implement error handling
5. ✅ Add data refresh logic
