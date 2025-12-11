# Dashboard Data Integration Guide

## Overview

Instead of creating separate REST endpoints for each dashboard data requirement, you can use the existing `/api/v1/chat/stream` endpoint with specialized tools. The LangChain agent will automatically call the appropriate tool and return structured JSON data.

## Benefits

✅ **No new endpoints needed** - Reuse existing infrastructure  
✅ **Flexible** - Agent can handle variations in queries  
✅ **Type-safe** - Tools return structured JSON matching frontend interfaces  
✅ **Maintainable** - All dashboard logic in one place  

## Available Dashboard Tools

### 1. Weekly Trend Data

**Tool**: `get_weekly_fni_trends`

**Frontend Query**:
```typescript
// Call the chat endpoint with this query
const response = await fetch('/api/v1/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "Get weekly F&I revenue trends for the last 4 weeks",
    session_id: "dashboard_session_123"
  })
});
```

**Alternative Queries** (agent will understand):
- "Show me weekly revenue trends by region"
- "Get 4-week F&I trend data for Midwest and Northeast"
- "Weekly revenue breakdown for the last 6 weeks"

**Response Format**:
```json
[
  {
    "week": "Week 1",
    "midwest": 125000,
    "northeast": 98000,
    "southeast": 110000,
    "west": 87000
  },
  {
    "week": "Week 2",
    "midwest": 130000,
    "northeast": 102000,
    "southeast": 115000,
    "west": 92000
  }
]
```

### 2. Enhanced KPI Data

**Tool**: `get_enhanced_kpi_data`

**Frontend Query**:
```typescript
const response = await fetch('/api/v1/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "Get enhanced KPI data for this week",
    session_id: "dashboard_session_123"
  })
});
```

**Alternative Queries**:
- "Show me KPI metrics for this month with comparisons"
- "Get last 7 days KPI data with previous period"
- "Monthly KPI comparison data"

**Response Format**:
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

### 3. Filtered F&I Data

**Tool**: `get_filtered_fni_data`

**Frontend Query**:
```typescript
const response = await fetch('/api/v1/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "Get F&I data for Midwest region this week",
    session_id: "dashboard_session_123"
  })
});
```

**Alternative Queries**:
- "Show F&I data for dealers 101, 102, 103 this month"
- "Get last 2 weeks F&I data for John Smith manager"
- "Filter F&I data by Northeast and Southeast regions"

**Response Format**:
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

## Frontend Integration Example

### React/TypeScript Example

```typescript
// types.ts
interface WeeklyTrendData {
  week: string;
  midwest?: number;
  northeast?: number;
  southeast?: number;
  west?: number;
}

interface EnhancedKPIData {
  current_period: {
    total_revenue: number;
    avg_penetration: number;
    total_transactions: number;
    period_label: string;
  };
  previous_period: {
    total_revenue: number;
    avg_penetration: number;
    total_transactions: number;
    period_label: string;
  };
  changes: {
    revenue_change_pct: number;
    penetration_change_pct: number;
    transactions_change_pct: number;
  };
}

// dashboardService.ts
export class DashboardService {
  private async queryAgent(query: string): Promise<any> {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        session_id: `dashboard_${Date.now()}`
      })
    });

    // Parse SSE stream
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let result = '';

    while (true) {
      const { done, value } = await reader!.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'complete') {
            result = data.result.analysis;
          }
        }
      }
    }

    return JSON.parse(result);
  }

  async getWeeklyTrends(weeks: number = 4): Promise<WeeklyTrendData[]> {
    return this.queryAgent(`Get weekly F&I revenue trends for the last ${weeks} weeks`);
  }

  async getEnhancedKPIs(period: string = 'this_week'): Promise<EnhancedKPIData> {
    return this.queryAgent(`Get enhanced KPI data for ${period.replace('_', ' ')}`);
  }

  async getFilteredData(filters: {
    time_period?: string;
    regions?: string[];
    dealer_ids?: number[];
  }): Promise<any[]> {
    let query = `Get F&I data for ${filters.time_period || 'this week'}`;
    
    if (filters.regions) {
      query += ` in ${filters.regions.join(', ')} regions`;
    }
    
    if (filters.dealer_ids) {
      query += ` for dealers ${filters.dealer_ids.join(', ')}`;
    }
    
    return this.queryAgent(query);
  }
}

// Usage in component
const Dashboard = () => {
  const [weeklyTrends, setWeeklyTrends] = useState<WeeklyTrendData[]>([]);
  const [kpiData, setKpiData] = useState<EnhancedKPIData | null>(null);
  
  useEffect(() => {
    const service = new DashboardService();
    
    // Load weekly trends
    service.getWeeklyTrends(4).then(setWeeklyTrends);
    
    // Load KPI data
    service.getEnhancedKPIs('this_week').then(setKpiData);
  }, []);
  
  return (
    <div>
      <WeeklyTrendChart data={weeklyTrends} />
      <KPIMetrics data={kpiData} />
    </div>
  );
};
```

## Migration Path

### Current State (Hardcoded)
```typescript
// ❌ Old way - hardcoded data
const weeklyTrends = [
  { week: "Week 1", midwest: 125000, ... }
];
```

### New State (Dynamic)
```typescript
// ✅ New way - dynamic from agent
const service = new DashboardService();
const weeklyTrends = await service.getWeeklyTrends(4);
```

## Testing

Test the tools directly via curl:

```bash
# Test weekly trends
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Get weekly F&I revenue trends for the last 4 weeks",
    "session_id": "test_123"
  }'

# Test enhanced KPIs
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Get enhanced KPI data for this week",
    "session_id": "test_123"
  }'

# Test filtered data
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Get F&I data for Midwest region this month",
    "session_id": "test_123"
  }'
```

## Benefits Over Separate Endpoints

| Aspect | Separate Endpoints | Agent Tools |
|--------|-------------------|-------------|
| **Flexibility** | Fixed parameters | Natural language queries |
| **Maintenance** | Multiple endpoints | Single endpoint |
| **Versioning** | API versioning needed | Backward compatible |
| **Discovery** | Documentation needed | Self-documenting |
| **Filtering** | Complex query params | Simple natural language |

## Next Steps

1. ✅ Tools created and integrated
2. ⏳ Update frontend to use agent queries
3. ⏳ Remove hardcoded data
4. ⏳ Add loading states for async data
5. ⏳ Add error handling for failed queries
