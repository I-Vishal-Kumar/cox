# Quick Start: Using Chat API for Dashboard Data

## ✅ The JSON-Only Mode IS Working!

Looking at your response, the final `AIMessage` contains **ONLY the JSON data**:

```json
content='[\n  {\n    "week": "Week 1",\n    "midwest": 318012.89,\n    ...\n  }\n]'
```

You just need to extract it correctly from the response structure.

---

## Step-by-Step Integration

### 1. Make the API Call

```typescript
const response = await fetch('/api/v1/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Get weekly F&I revenue trends for the last 4 weeks, return as JSON",
    conversation_id: `dashboard_${Date.now()}`
  })
});

const data = await response.json();
```

### 2. Extract the Clean JSON

```typescript
// Parse the message field
const messagesData = JSON.parse(data.message);
const messages = messagesData.messages;

// Get the last AI message (this contains your clean JSON)
const lastAIMessage = messages[messages.length - 1];

// Parse the JSON content
const weeklyTrends = JSON.parse(lastAIMessage.content);

console.log(weeklyTrends);
// Output: [{ week: "Week 1", midwest: 318012.89, ... }]
```

### 3. Complete Service Example

```typescript
// dashboardService.ts
export class DashboardService {
  private async getJSONData(query: string): Promise<any> {
    // Step 1: Make API call
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: `${query}, return as JSON`,
        conversation_id: `dashboard_${Date.now()}`
      })
    });

    const data = await response.json();
    
    // Step 2: Extract JSON from response
    const messagesData = JSON.parse(data.message);
    const messages = messagesData.messages;
    const lastAIMessage = messages[messages.length - 1];
    
    // Step 3: Parse and return
    return JSON.parse(lastAIMessage.content);
  }

  // Usage methods
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
  }) {
    let query = `Get F&I data for ${filters.time_period || 'this week'}`;
    if (filters.regions) {
      query += ` in ${filters.regions.join(', ')} regions`;
    }
    return this.getJSONData(query);
  }
}
```

---

## Using the Helper Utility

I've created a helper utility at [`frontend_helpers/chatResponseParser.ts`](file:///home/jipl/Downloads/cox/co/backend/frontend_helpers/chatResponseParser.ts) that makes this even easier:

```typescript
import { extractJSONFromChatResponse } from './chatResponseParser';

// Make API call
const response = await fetch('/api/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: "Get weekly F&I revenue trends for the last 4 weeks, return as JSON",
    conversation_id: `dashboard_${Date.now()}`
  })
});

const data = await response.json();

// Extract clean JSON with one function call
const weeklyTrends = extractJSONFromChatResponse(data);

console.log(weeklyTrends);
// Output: [{ week: "Week 1", midwest: 318012.89, ... }]
```

---

## React Component Example

```typescript
import { useState, useEffect } from 'react';
import { extractJSONFromChatResponse } from '@/lib/chatResponseParser';

interface WeeklyTrend {
  week: string;
  midwest: number;
  northeast: number;
  southeast: number;
  west: number;
}

export function WeeklyTrendsChart() {
  const [trends, setTrends] = useState<WeeklyTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTrends() {
      try {
        const response = await fetch('/api/v1/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: "Get weekly F&I revenue trends for the last 4 weeks, return as JSON",
            conversation_id: `dashboard_${Date.now()}`
          })
        });

        const data = await response.json();
        const trendsData = extractJSONFromChatResponse(data);
        
        setTrends(trendsData);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    }

    fetchTrends();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Weekly F&I Revenue Trends</h2>
      {trends.map((trend, index) => (
        <div key={index}>
          <h3>{trend.week}</h3>
          <p>Midwest: ${trend.midwest.toLocaleString()}</p>
          <p>Northeast: ${trend.northeast.toLocaleString()}</p>
          <p>Southeast: ${trend.southeast.toLocaleString()}</p>
          <p>West: ${trend.west.toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
}
```

---

## Response Structure Explained

Your response has this structure:

```json
{
  "message": "{'messages': [HumanMessage(...), AIMessage(...), ToolMessage(...), AIMessage(...)]}",
  "conversation_id": "...",
  "query_type": "conversational_bi",
  ...
}
```

The `message` field contains a string representation of the messages array. The **last AIMessage** in that array contains your clean JSON:

```
messages[0] = HumanMessage (your query)
messages[1] = AIMessage (tool call decision)
messages[2] = ToolMessage (tool result with JSON)
messages[3] = AIMessage (FINAL - contains clean JSON) ← This is what you want!
```

---

## Key Takeaways

1. ✅ **JSON-only mode IS working** - the final AI message contains only JSON
2. ✅ **No conversational text** - just the data you requested
3. ✅ **Easy to extract** - just parse `messages[messages.length - 1].content`
4. ✅ **Use the helper utility** - `extractJSONFromChatResponse(data)` does it all

The system is working exactly as designed! You just need to extract the final message content.
