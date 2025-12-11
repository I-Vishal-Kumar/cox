# Cox Automotive AI Analytics API Documentation

## Overview

The Cox Automotive AI Analytics platform provides intelligent business analytics through natural language queries and structured data endpoints. The system uses OpenRouter's GPT-4 model with specialized tools for automotive industry analysis.

**Base URL:** `http://localhost:8000/api/v1`

---

## 🤖 AI Chat & Analytics Endpoints

### 1. Chat Query (Regular)
**POST** `/chat`

Process natural language queries and get comprehensive AI analysis.

#### Request Body
```json
{
  "message": "Why did F&I revenue drop across Midwest dealers this week?",
  "conversation_id": "optional-uuid-string"
}
```

#### Response
```json
{
  "message": "AI-generated analysis text...",
  "conversation_id": "uuid-string",
  "query_type": "conversational_bi",
  "sql_query": "SELECT ... FROM ...",
  "data": [
    {
      "dealer_name": "XYZ Nissan",
      "dealer_code": "XYZ002",
      "this_week_revenue": 50443.83,
      "last_week_revenue": 97943.65,
      "change_pct": -48.5,
      "current_penetration": 27.0,
      "previous_penetration": 38.4
    }
  ],
  "chart_config": {
    "type": "bar",
    "title": "Revenue Comparison",
    "x_axis": "dealer_name",
    "y_axis": "revenue_change"
  },
  "recommendations": [
    "Implement F&I training for underperforming dealers",
    "Review pricing strategy for winter months"
  ]
}
```

#### Capabilities
- **Natural Language Processing**: Understands complex business questions
- **SQL Generation**: Automatically creates database queries
- **AI Analysis**: Provides root cause analysis and insights
- **Structured Data**: Returns both raw data and processed results
- **Visualizations**: Generates chart configurations
- **Recommendations**: Actionable business recommendations

---

### 2. Chat Stream (Real-time)
**GET** `/chat/stream`

Stream real-time responses for longer queries with live updates.

#### Query Parameters
- `message` (required): The user's question
- `conversation_id` (optional): UUID for conversation continuity

#### Response (Server-Sent Events)
```
data: {"type": "start", "conversation_id": "uuid"}

data: {"type": "status", "content": "Processing your query..."}

data: {"type": "status", "content": "Detected demo scenario: fni_midwest"}

data: {"type": "data", "data": [...]}

data: {"type": "chart", "config": {...}}

data: {"type": "complete", "result": {...}}
```

#### Stream Event Types
- `start`: Initial connection with conversation ID
- `status`: Processing status updates
- `chunk`: Real-time AI response chunks
- `data`: Database query results
- `chart`: Visualization configuration
- `complete`: Final complete result
- `error`: Error information

---

## 🎯 Specialized Analysis Scenarios

The AI orchestrator automatically detects and handles these business scenarios:

### F&I Revenue Analysis
**Keywords:** F&I, finance, insurance, revenue drop, penetration, Midwest, service contracts

**Example Queries:**
- "Why did F&I revenue drop across Midwest dealers this week?"
- "Which dealers have the lowest service contract penetration?"
- "Show me F&I performance by region"

**Structured Data Output:**
```json
{
  "structured_data": {
    "summary": {
      "total_revenue_change": {
        "amount": -500000,
        "percentage": -25.0
      },
      "dealers_analyzed": 5,
      "period": "week_over_week"
    },
    "dealer_performance": {
      "declining": [...],
      "improving": [...]
    },
    "risk_assessment": {
      "high_risk_dealers": ["XYZ002", "MTA003"],
      "medium_risk_dealers": ["ABC001"],
      "low_risk_dealers": []
    }
  }
}
```

### Logistics Delay Analysis
**Keywords:** shipment, delay, carrier, route, weather, late, dwell time

**Example Queries:**
- "Who delayed — carrier, route, or weather?"
- "Show me shipment delays by carrier"
- "What's causing logistics delays this week?"

**Structured Data Output:**
```json
{
  "structured_data": {
    "delay_attribution": {
      "Carrier": {"delayed_shipments": 45, "delay_rate": 12.5},
      "Weather": {"delayed_shipments": 30, "delay_rate": 8.3},
      "Route": {"delayed_shipments": 25, "delay_rate": 6.9}
    },
    "carrier_performance": {...},
    "route_analysis": {...}
  }
}
```

### Plant Downtime Analysis
**Keywords:** plant, downtime, production, manufacturing, line, maintenance

**Example Queries:**
- "Which plants showed downtime and why?"
- "Show me production issues this week"
- "What's causing manufacturing delays?"

### General KPI Monitoring
**Keywords:** Any data-related question not matching above scenarios

**Example Queries:**
- "Show me sales trends"
- "What are our key metrics?"
- "Compare performance across regions"

---

## 📊 Dashboard Endpoints

### 1. Invite (Marketing) Dashboard
**GET** `/dashboard/invite`

#### Query Parameters
- `dealer_id` (optional): Filter by specific dealer

#### Response
```json
{
  "campaigns": [...],
  "performance_metrics": {...},
  "roi_analysis": {...}
}
```

### 2. F&I Dashboard
**GET** `/dashboard/fni`

#### Query Parameters
- `region` (optional): Filter by region (Midwest, Northeast, Southeast, West)

#### Response
```json
{
  "revenue_summary": {...},
  "penetration_rates": {...},
  "dealer_performance": [...]
}
```

### 3. Logistics Dashboard
**GET** `/dashboard/logistics`

#### Response
```json
{
  "shipment_summary": {...},
  "delay_analysis": {...},
  "carrier_performance": [...]
}
```

### 4. Plant Dashboard
**GET** `/dashboard/plant`

#### Response
```json
{
  "downtime_summary": {...},
  "production_metrics": {...},
  "plant_performance": [...]
}
```

---

## 📈 KPI & Metrics Endpoints

### 1. KPI Metrics
**GET** `/kpi/metrics`

#### Query Parameters
- `category` (optional): Sales, Service, F&I, Marketing, Logistics
- `region` (optional): Midwest, Northeast, Southeast, West
- `days` (optional): Number of days (1-365, default: 30)

#### Response
```json
{
  "metrics": [
    {
      "metric_name": "F&I Revenue",
      "metric_value": 2100000,
      "target_value": 2400000,
      "variance": -12.5,
      "trend": "declining"
    }
  ]
}
```

### 2. KPI Alerts
**GET** `/kpi/alerts`

#### Response
```json
{
  "alerts": [
    {
      "id": "alert_001",
      "severity": "warning",
      "metric": "F&I Revenue - Midwest",
      "message": "F&I revenue down 11% vs last week",
      "timestamp": "2024-01-15T09:00:00Z"
    }
  ]
}
```

---

## 🗃️ Data Catalog Endpoints

### 1. Available Tables
**GET** `/data-catalog/tables`

#### Response
```json
{
  "tables": [
    {
      "name": "dealers",
      "description": "Dealer information including location and region",
      "columns": ["id", "dealer_code", "name", "region", "state", "city"],
      "row_count": "~12"
    },
    {
      "name": "fni_transactions",
      "description": "Finance & Insurance transaction records",
      "columns": ["id", "dealer_id", "transaction_date", "fni_revenue", "penetration_rate"],
      "row_count": "~2,000+"
    }
  ],
  "regions": ["Midwest", "Northeast", "Southeast", "West"],
  "kpi_categories": ["Sales", "Service", "F&I", "Marketing", "Logistics"]
}
```

---

## 🧪 Demo & Testing Endpoints

### 1. Demo Scenarios
**GET** `/demo/scenarios`

#### Response
```json
{
  "scenarios": [
    {
      "id": "fni_midwest",
      "title": "F&I Revenue Drop in Midwest",
      "question": "Why did F&I revenue drop across Midwest dealers this week?",
      "category": "F&I Analysis"
    },
    {
      "id": "logistics_delays",
      "title": "Logistics Delays Analysis",
      "question": "Who delayed — carrier, route, or weather?",
      "category": "Logistics"
    },
    {
      "id": "plant_downtime",
      "title": "Plant Downtime & Root Cause",
      "question": "Which plants showed downtime and why?",
      "category": "Manufacturing"
    }
  ]
}
```

---

## 🔧 AI Orchestrator Capabilities

### Intelligent Tool Selection
The AI orchestrator automatically selects appropriate tools based on query analysis:

1. **generate_sql_query** - Converts natural language to SQL
2. **analyze_kpi_data** - General-purpose data analysis
3. **analyze_fni_revenue_drop** - F&I revenue specialist
4. **analyze_logistics_delays** - Logistics specialist
5. **analyze_plant_downtime** - Manufacturing specialist
6. **generate_chart_configuration** - Visualization generator

### Conversation Context
- Maintains conversation history (last 20 messages)
- Understands follow-up questions
- Detects implicit references ("those dealers", "that region")
- Provides contextual analysis

### Data Processing Pipeline
```
User Query → Scenario Detection → SQL Generation → Data Retrieval → AI Analysis → Structured Output
```

---

## 🚀 Frontend Integration Examples

### React/JavaScript Integration

#### Basic Chat Query
```javascript
const queryAI = async (message, conversationId = null) => {
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, conversation_id: conversationId })
  });
  
  const result = await response.json();
  return {
    analysis: result.message,
    data: result.data,
    chartConfig: result.chart_config,
    recommendations: result.recommendations,
    conversationId: result.conversation_id
  };
};
```

#### Streaming Chat
```javascript
const streamChat = async (message, onChunk) => {
  const response = await fetch(`/api/v1/chat/stream?message=${encodeURIComponent(message)}`);
  const reader = response.body.getReader();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = new TextDecoder().decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        onChunk(data);
      }
    }
  }
};
```

#### Dashboard Data
```javascript
const getDashboardData = async (type, filters = {}) => {
  const params = new URLSearchParams(filters);
  const response = await fetch(`/api/v1/dashboard/${type}?${params}`);
  return response.json();
};

// Usage
const fniData = await getDashboardData('fni', { region: 'Midwest' });
const kpiMetrics = await getDashboardData('kpi/metrics', { category: 'F&I', days: 7 });
```

---

## 🔐 Authentication & Security

Currently running in development mode. For production deployment:

- Add API key authentication
- Implement rate limiting
- Add CORS configuration
- Enable HTTPS
- Add request validation
- Implement audit logging

---

## 📝 Response Formats

### Standard Response Structure
```json
{
  "message": "Human-readable AI analysis",
  "conversation_id": "uuid-string",
  "query_type": "scenario-type",
  "sql_query": "Generated SQL query",
  "data": "Raw database results",
  "structured_data": "Processed structured data",
  "chart_config": "Visualization configuration",
  "recommendations": "Actionable recommendations",
  "metadata": {
    "processing_time": "Response time in ms",
    "tokens_used": "AI token consumption",
    "confidence_score": "Analysis confidence"
  }
}
```

### Error Response
```json
{
  "error": "Error description",
  "message": "User-friendly error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-15T09:00:00Z"
}
```

---

## 🎯 Use Cases for Frontend Integration

### 1. Conversational BI Dashboard
- Natural language query interface
- Real-time streaming responses
- Interactive data visualizations
- Contextual follow-up questions

### 2. Executive Reporting
- Automated insight generation
- Structured data for charts/graphs
- Actionable recommendations
- Performance alerts

### 3. Operational Analytics
- Real-time KPI monitoring
- Anomaly detection alerts
- Root cause analysis
- Predictive insights

### 4. Business Intelligence Tools
- SQL query generation
- Data exploration interface
- Custom dashboard creation
- Export capabilities

This API provides a complete foundation for building intelligent automotive analytics applications with both conversational AI and traditional dashboard capabilities.