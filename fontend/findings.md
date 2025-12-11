# Frontend Data Usage Findings

This document outlines the data usage and structure across the frontend application. Currently, most of the data is hardcoded within the components or pages, with some limited API integration in the chat interface.

## 1. Chat Interface
**File:** `src/components/chat/ChatInterface.tsx`

**Data Usage:**
- **Demo Scenarios:** Hardcoded array of `DemoScenario` objects used to populate the "Ask anything about your data" section.
- **Demo Responses:** Hardcoded map of responses (`demoResponses`) used as a fallback when the backend is offline or errors occur.
- **API Integration:** Uses `sendChatMessage` from `src/lib/api.ts` to communicate with the backend (`/api/v1/chat`).
- **Data Structure:**
    - `DemoScenario`: `{ id: string, title: string, question: string, category: string }`
    - `ChatResponse` (from API):
      ```typescript
      interface ChatResponse {
        message: string;
        conversation_id: string;
        query_type: string;
        sql_query?: string;
        data?: Record<string, unknown>[];
        chart_config?: {
          type: string;
          title: string;
          x_axis?: string;
          y_axis?: string;
        };
        recommendations?: string[];
      }
      ```

## 2. Alerts Page
**File:** `src/app/alerts/page.tsx`

**Data Usage:**
- **Mock Alerts:** Hardcoded array `mockAlerts` used to display the list of alerts.
- **Data Structure:**
  ```typescript
  {
    id: string;
    metric_name: string;
    current_value: number;
    previous_value: number;
    change_percent: number;
    severity: 'critical' | 'warning' | 'info';
    message: string;
    timestamp: string;
    root_cause: string;
    category: string;
  }
  ```

## 3. F&I Analysis Page
**File:** `src/app/analysis/fni/page.tsx`

**Data Usage:**
- **Dealer Comparison:** Hardcoded `dealerComparisonData` array.
- **Manager Breakdown:** Hardcoded `managerBreakdown` array.
- **Weekly Trend:** Hardcoded `weeklyTrend` array.
- **Data Structure:**
    - `dealerComparisonData`: `{ dealer: string, this_week: number, last_week: number, change: number, penetration: number }`
    - `managerBreakdown`: `{ manager: string, dealer: string, penetration: number, transactions: number, revenue: number }`
    - `weeklyTrend`: `{ week: string, midwest: number, northeast: number, southeast: number, west: number }`

## 4. Logistics Analysis Page
**File:** `src/app/analysis/logistics/page.tsx`

**Data Usage:**
- **Carrier Data:** Hardcoded `carrierData` array.
- **Route Data:** Hardcoded `routeData` array.
- **Delay Reasons:** Hardcoded `delayReasons` array.
- **Dwell Time Comparison:** Hardcoded `dwellTimeComparison` array.
- **Data Structure:**
    - `carrierData`: `{ carrier: string, total: number, delayed: number, delay_rate: number, avg_dwell: number }`
    - `routeData`: `{ route: string, carrier: string, delayed: number, total: number, reason: string }`
    - `delayReasons`: `{ name: string, value: number, color: string }`
    - `dwellTimeComparison`: `{ period: string, 'Carrier X': number, 'Carrier Y': number, 'Carrier Z': number }`

## 5. Plant Analysis Page
**File:** `src/app/analysis/plant/page.tsx`

**Data Usage:**
- **Plant Summary:** Hardcoded `plantSummary` array.
- **Downtime Details:** Hardcoded `downtimeDetails` array.
- **Cause Breakdown:** Hardcoded `causeBreakdown` array.
- **Data Structure:**
    - `plantSummary`: `{ plant: string, code: string, total_downtime: number, events: number, unplanned: number }`
    - `downtimeDetails`: `{ plant: string, line: string, hours: number, category: string, detail: string, supplier: string | null }`
    - `causeBreakdown`: `{ name: string, value: number, color: string }`

## 6. Data Catalog Page
**File:** `src/app/catalog/page.tsx`

**Data Usage:**
- **Data Catalog:** Hardcoded `dataCatalog` array describing available tables.
- **Data Structure:**
  ```typescript
  {
    name: string;
    description: string;
    columns: {
      name: string;
      type: string;
      description: string;
    }[];
    rowCount: string;
    lastUpdated: string;
    category: string;
  }
  ```

## 7. Invite Dashboard
**File:** `src/components/dashboard/InviteDashboard.tsx` (Rendered by `src/app/invite/page.tsx`)

**Data Usage:**
- **Program Performance:** Hardcoded `programPerformanceData` array.
- **Monthly Data:** Hardcoded `monthlyData` array.
- **Data Structure:**
    - `programPerformanceData`: `{ campaign_name: string, category: string, emails_sent: number, unique_opens: number, open_rate: number, ro_count: number, revenue: number }`
    - `monthlyData`: `{ month: string, emails: number, opens: number, ro: number, revenue: number }`

## Summary
The frontend is currently heavily reliant on hardcoded mock data for all dashboard and analysis pages. Only the `ChatInterface` has logic to attempt a connection to a backend API (`http://localhost:8000/api/v1`), but it also falls back to hardcoded demo responses if the backend is unavailable or returns an error. To make the application dynamic, these hardcoded data sources need to be replaced with API calls to fetch real-time data from the backend.
