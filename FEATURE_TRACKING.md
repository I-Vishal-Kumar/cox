# Feature Tracking & API Documentation

This document tracks all features, APIs, and their expected input/output types as we build and complete them.

## 📋 API Endpoints

### 1. Chat API - `/api/v1/chat` ✅
**File:** `backend/app/api/routes.py`  
**Method:** POST  
**Status:** ✅ Implemented

**Expected Input (ChatRequest):**
```typescript
{
  message: string;                    // User's natural language query
  conversation_id?: string;           // Session ID for conversation continuity
  query_type?: QueryType;              // Optional query type hint
}
```

**Expected Output (ChatResponse):**
```typescript
{
  message: string;                    // AI-generated analysis/response
  conversation_id: string;            // Session ID
  query_type: QueryType;              // Detected query type
  sql_query?: string;                 // SQL query executed (if any)
  data?: Array<Record<string, any>>;  // Query results data
  chart_config?: Record<string, any>; // Chart configuration for visualization
  recommendations?: string[];          // Actionable recommendations
  sources?: string[];                 // Data sources used
}
```

**Features:**
- Natural language query processing
- LangChain-based orchestrator
- Conversation history management
- SQL query generation and execution
- Chart configuration generation
- Root cause analysis for demo scenarios

---

### 2. Chat Stream API - `/api/v1/chat/stream` ✅
**File:** `backend/app/api/routes.py`  
**Method:** GET  
**Status:** ✅ Implemented

**Expected Input (Query Parameters):**
```typescript
{
  message: string;                    // User's natural language query (required)
  conversation_id?: string;           // Session ID for conversation continuity
}
```

**Expected Output (Server-Sent Events):**
```typescript
// Event types:
{
  type: "start" | "chunk" | "complete" | "error";
  conversation_id?: string;           // On start
  content?: string;                    // On chunk
  result?: ChatResponse;               // On complete - Full ChatResponse data
  error?: string;                     // On error
}
```

**Features:**
- Real-time streaming responses
- Progressive updates as agent processes query
- Error handling via SSE

---

### 3. Invite Dashboard API - `/api/v1/dashboard/invite` ✅
**File:** `backend/app/api/routes.py`  
**Method:** GET  
**Status:** ✅ Implemented

**Expected Input (Query Parameters):**
```typescript
{
  dealer_id?: number;                  // Filter by specific dealer ID
}
```

**Expected Output:**
```typescript
{
  program_summary: {
    total_programs: number;
    total_emails: number;
    total_opens: number;
    avg_open_rate: number;
    total_ros: number;
    total_revenue: number;
  };
  program_performance: Array<{
    campaign_name: string;
    category: string;
    emails_sent: number;
    unique_opens: number;
    open_rate: number;
    ro_count: number;
    revenue: number;
  }>;
  monthly_metrics: Array<{
    month: string;
    emails_sent: number;
    unique_opens: number;
    ro_count: number;
    revenue: number;
  }>;
  last_updated: string;                // ISO timestamp
}
```

**Features:**
- Marketing campaign performance data
- Program summary statistics
- Monthly trend analysis
- Dealer-specific filtering

---

### 4. F&I Dashboard API - `/api/v1/dashboard/fni` ✅
**File:** `backend/app/api/routes.py`  
**Method:** GET  
**Status:** ✅ Implemented

**Expected Input (Query Parameters):**
```typescript
{
  region?: string;                     // Filter by region (Midwest, Northeast, Southeast, West)
}
```

**Expected Output:**
```typescript
{
  weekly_trends: Array<Record<string, any>>;  // Weekly F&I revenue trends
  kpi_data: Record<string, any>;                // KPI metrics and comparisons
  filtered_data: Array<Record<string, any>>;  // Filtered transaction data
}
```

**Features:**
- F&I revenue analysis
- Weekly trend visualization
- Regional filtering
- KPI comparisons

---

### 5. Logistics Dashboard API - `/api/v1/dashboard/logistics` ✅
**File:** `backend/app/api/routes.py`  
**Method:** GET  
**Status:** ✅ Implemented

**Expected Input:**
- None (no query parameters)

**Expected Output:**
```typescript
{
  delay_summary: Record<string, any>;          // Overall delay statistics
  carrier_performance: Array<Record<string, any>>;  // Performance by carrier
  route_analysis: Array<Record<string, any>>;   // Route-level delay data
}
```

**Features:**
- Shipment delay analysis
- Carrier performance metrics
- Route-level analysis

---

### 6. Plant Dashboard API - `/api/v1/dashboard/plant` ✅
**File:** `backend/app/api/routes.py`  
**Method:** GET  
**Status:** ✅ Implemented

**Expected Input:**
- None (no query parameters)

**Expected Output:**
```typescript
{
  downtime_summary: Record<string, any>;       // Overall downtime statistics
  plant_breakdown: Array<Record<string, any>>; // Downtime by plant
  root_causes: Array<Record<string, any>>;    // Root cause analysis
}
```

**Features:**
- Plant downtime analysis
- Root cause identification
- Plant-level breakdown

---

### 7. KPI Metrics API - `/api/v1/kpi/metrics` ✅
**File:** `backend/app/api/routes.py`  
**Method:** GET  
**Status:** ✅ Implemented

**Expected Input (Query Parameters):**
```typescript
{
  category?: string;                   // Filter by KPI category (Sales, Service, F&I, Marketing, Logistics)
  region?: string;                     // Filter by region
  days?: number;                      // Number of days to look back (default: 30, range: 1-365)
}
```

**Expected Output:**
```typescript
{
  metrics: Array<{
    metric_name: string;
    metric_value: number;
    metric_date: string;
    target_value: number;
    variance: number;
    // ... other fields
  }>;
}
```

**Features:**
- KPI metric retrieval
- Category and region filtering
- Time range filtering
- Target comparison

---

### 8. KPI Alerts API - `/api/v1/kpi/alerts` ✅
**File:** `backend/app/api/routes.py`  
**Method:** GET  
**Status:** ✅ Implemented

**Expected Input:**
- None (no query parameters)

**Expected Output:**
```typescript
{
  alerts: Array<{
    id: string;
    metric_name: string;
    current_value: number;
    previous_value: number;
    change_percent: number;
    severity: "info" | "warning" | "critical";
    message: string;
    timestamp: string;                 // ISO datetime
    root_cause?: string;
  }>;
}
```

**Features:**
- Anomaly detection
- Alert severity classification
- Root cause analysis
- Change percentage calculation

---

### 9. Inspect/Repair Orders API - `/api/v1/inspect/repair-orders` ✅
**File:** `backend/app/api/routes.py`  
**Method:** GET  
**Status:** ✅ Implemented

**Expected Input (Query Parameters):**
```typescript
{
  ro_type?: string;              // Filter by RO type (Standard, Express, Warranty)
  shop_type?: string;            // Filter by shop type (Service, Body Shop, Quick Service)
  waiter?: string;               // Filter by waiter status (Yes, No)
  search?: string;                // Search by RO number or customer name
}
```

**Expected Output:**
```typescript
{
  repair_orders: Array<{
    id: number;
    ro: string;                   // RO number (e.g., "6149706")
    p: string;                    // Priority (1-5)
    tag: string;                  // Tag (A, B, C, D, E)
    promised: string;             // Promised time (e.g., "8:00 pm", "W 12:00 am")
    promised_date: string;        // ISO date
    e: string;                    // Indicator
    customer: string;             // Customer name
    adv: string;                  // Advisor ID
    tech: string;                 // Technician ID
    mt: string;                   // Metric time (e.g., "1:16", "00:03")
    pt: string;                   // Process time (e.g., "4d", "28d")
    status: string;               // awaiting_dispatch, in_inspection, pending_approval, in_repair, pending_review
    ro_type?: string;
    shop_type?: string;
    waiter?: string;
    is_overdue?: boolean;
    is_urgent?: boolean;
  }>;
}
```

**Features:**
- Repair order retrieval with filtering
- Status-based organization
- Search functionality
- Real-time updates (30-second refetch)

---

### 10. Data Catalog API - `/api/v1/data-catalog/tables` ✅
**File:** `backend/app/api/routes.py`  
**Method:** GET  
**Status:** ✅ Implemented

**Expected Input:**
- None (no query parameters)

**Expected Output:**
```typescript
{
  tables: Array<{
    name: string;
    description: string;
    columns: string[];
    row_count: string;
  }>;
  regions: string[];                    // Available regions
  kpi_categories: string[];             // Available KPI categories
}
```

**Features:**
- Table schema information
- Available regions list
- KPI categories list

---

### 11. Engage/Service Appointments API - `/api/v1/engage/appointments` ✅
**File:** `backend/app/api/routes.py`  
**Method:** GET  
**Status:** ✅ Implemented

**Expected Input (Query Parameters):**
```typescript
{
  date?: string;                    // Appointment date (YYYY-MM-DD), defaults to today
  advisor?: string;                 // Filter by advisor name (use "All" for all)
  status?: string;                  // Filter by status (not_arrived, checked_in, in_progress, completed, cancelled, or "All")
  search?: string;                  // Search by customer name, VIN, vehicle, or RO number
}
```

**Expected Output:**
```typescript
{
  appointments: Array<{
    id: number;
    appointment_date: string;       // YYYY-MM-DD
    appointment_time: string;        // e.g., "7:00 AM"
    service_type: string;           // Regular Maintenance, Full Service, Quick Service, etc.
    estimated_duration: string;      // e.g., "45 min", "2 hours"
    vehicle_vin: string;
    vehicle_year: number;
    vehicle_make: string;
    vehicle_model: string;
    vehicle_mileage: string;         // e.g., "35,000 mi"
    vehicle_icon_color: string;      // blue, red, gray
    customer_name: string;
    advisor: string;
    status: string;                  // not_arrived, checked_in, in_progress, completed, cancelled
    ro_number?: string;
    code?: string;                   // e.g., "T500"
    customer_id?: number;
    phone?: string;
    email?: string;
    loyalty_tier?: string;           // Platinum, Gold, Silver
    preferred_services: string[];   // Array of preferred service types
    service_history_count: number;
    last_visit_date?: string;       // YYYY-MM-DD
  }>;
  needs_action_count: number;       // Count of appointments needing action
}
```

**Features:**
- Service appointment retrieval with customer information
- Date-based filtering (defaults to today)
- Advisor and status filtering
- Search functionality (customer name, VIN, vehicle, RO number)
- Customer loyalty tier and preferences
- Service history tracking
- Needs action count calculation

---

### 12. Check-In API - `/api/v1/engage/check-in/{appointment_id}` ✅
**File:** `backend/app/api/routes.py`  
**Method:** POST  
**Status:** ✅ Implemented

**Expected Input:**
- appointment_id: int (path parameter) - ID of the appointment to check in

**Expected Output:**
```typescript
{
  success: boolean;
  id: number;                       // Appointment ID
  status: string;                   // Updated status (checked_in)
  message?: string;                 // Error message if unsuccessful
}
```

**Features:**
- Quick check-in functionality
- Status update to "checked_in"
- Error handling for invalid appointment IDs

---

### 13. Demo Scenarios API - `/api/v1/demo/scenarios` ✅
**File:** `backend/app/api/routes.py`  
**Method:** GET  
**Status:** ✅ Implemented

**Expected Input:**
- None (no query parameters)

**Expected Output:**
```typescript
{
  scenarios: Array<{
    id: string;                        // Scenario identifier
    title: string;                     // Scenario title
    question: string;                   // Example question
    category: string;                   // Scenario category
  }>;
}
```

**Features:**
- Pre-built demo scenarios
- Testing support
- Scenario metadata

---

## 🔧 Backend Tools & Agents

### LangChain Orchestrator ✅
**File:** `backend/app/agents/langchain_orchestrator.py`  
**Status:** ✅ Implemented

**Features:**
- Multi-agent orchestration
- Tool selection and routing
- SQL query generation
- Root cause analysis
- Chart configuration generation
- Session management

**Tools Available:**
- `generate_sql_query` - SQL generation from natural language
- `analyze_kpi_data` - General data analysis
- `analyze_fni_revenue_drop` - F&I revenue drop analysis
- `analyze_logistics_delays` - Logistics delay analysis
- `analyze_plant_downtime` - Plant downtime analysis
- `get_weekly_fni_trends` - Weekly F&I trends
- `get_enhanced_kpi_data` - Enhanced KPI data
- `get_filtered_fni_data` - Filtered F&I data
- `get_invite_campaign_data` - Invite campaign data
- `get_invite_monthly_trends` - Invite monthly trends
- `get_invite_enhanced_kpi_data` - Invite enhanced KPI data
- `analyze_chart_change_request` - Chart type change analysis

---

## 📊 Frontend Components

### Invite Dashboard ✅
**File:** `fontend/src/components/dashboard/InviteDashboard.tsx`  
**Status:** ✅ Implemented

**Features:**
- Top programs by revenue visualization
- Revenue by category visualization
- Dynamic chart type switching (bar, pie, line)
- Floating chat bot integration
- Real-time data updates

---

### Floating Chat Bot ✅
**File:** `fontend/src/components/ui/FloatingChatBot.tsx`  
**Status:** ✅ Implemented

**Features:**
- Floating chat interface
- Session management
- Chart change requests
- Natural language queries
- Real-time responses

---

## 🎯 Demo Scenarios

### 1. F&I Revenue Drop in Midwest ✅
**Status:** ✅ Implemented  
**API:** `/api/v1/chat`  
**Query:** "Why did F&I revenue drop across Midwest dealers this week?"

**Expected Flow:**
1. Detects F&I + Midwest keywords
2. Generates SQL with WHERE and LIMIT clauses
3. Calls `analyze_fni_revenue_drop` tool
4. Returns detailed RCA with dealer names, percentages, recommendations

---

### 2. Logistics Delays ✅
**Status:** ✅ Implemented  
**API:** `/api/v1/chat`  
**Query:** "Who delayed — carrier, route, or weather?"

**Expected Flow:**
1. Detects logistics/delay keywords
2. Generates SQL for delayed shipments
3. Calls `analyze_logistics_delays` tool
4. Returns delay attribution breakdown

---

### 3. Plant Downtime ✅
**Status:** ✅ Implemented  
**API:** `/api/v1/chat`  
**Query:** "Which plants showed downtime and why?"

**Expected Flow:**
1. Detects plant/downtime keywords
2. Generates SQL for downtime events
3. Calls `analyze_plant_downtime` tool
4. Returns plant-by-plant breakdown with root causes

---

## 📝 Notes

- All APIs use FastAPI with Pydantic models for type validation
- Database queries use SQLAlchemy async sessions
- LangChain orchestrator handles tool selection and execution
- Session management for conversation continuity
- Chart configurations generated dynamically based on data structure

---

## 🔄 Recent Changes

- ✅ Reverted model name to `openai/gpt-4` (from free model)
- ✅ Removed timeout settings (reverted to defaults)
- ✅ Added API documentation with expected input/output types
- ✅ Created feature tracking document
- ✅ **Invite Dashboard**: Removed hardcoded data, now using direct REST API endpoint `/api/v1/dashboard/invite`
  - Updated `inviteDashboardService.getInviteDashboard()` to transform backend response
  - Removed hardcoded `programPerformanceData` and `monthlyData` arrays
  - Primary data source: Direct REST API endpoint
  - Fallback: Chat API tools (if REST API fails)
  - Improved monthly trends query ordering in backend
- ✅ **Cox Automotive Branding**: Added comprehensive branding throughout the application
  - Updated Sidebar with Cox Automotive logo and branding
  - Updated Header with Cox Automotive logo
  - Created Footer component with Cox Automotive branding, brands, and links
  - Updated all page titles and subtitles to include "Cox Automotive"
  - Added Cox Automotive branding to Invite Dashboard header
  - Updated chat interface welcome message with Cox branding
  - Updated FloatingChatBot with Cox Automotive branding
  - Added "Powered by Jaiinfoway" references where appropriate
  - Updated metadata and page titles
- ✅ **Plant Downtime Analysis Page**: Completed end-to-end implementation
  - Created `plantDashboard.ts` API service with TanStack Query integration
  - Replaced all mock data with real backend data from `/api/v1/dashboard/plant`
  - Added FloatingChatBot widget with chart switching capability
  - Implemented dynamic chart type switching (bar, pie, line, area) for both charts
  - Added chart context for bot interaction
  - Updated backend service to return correct data structure with unplanned downtime
  - Added loading states, error handling, and empty state messages
  - Dynamic root cause analysis based on actual data
- ✅ **KPI Alerts Page**: Completed end-to-end implementation
  - Already using TanStack Query via `useAlerts()` hook
  - Added FloatingChatBot widget with alerts context
  - Enhanced backend `get_alerts()` to include previous period comparison
  - Bot can answer questions about alerts, root causes, and alert details
  - Page context includes alert summaries, critical/warning breakdowns, and category analysis
  - Bot can explain why alerts happened and provide recommendations
- ✅ **Data Catalog Page**: Completed end-to-end implementation
  - Already using TanStack Query via `dataCatalogService.getTables()`
  - Added FloatingChatBot widget with catalog context
  - Page context includes all tables, columns, categories, regions, and KPI categories
  - Selected table information passed to bot for detailed queries
  - Bot can answer questions about:
    - Available tables and their descriptions
    - Table columns and data types
    - How to query specific tables
    - Table relationships and structure
    - Sample SQL queries
    - Data catalog navigation
  - Enhanced FloatingChatBot to handle catalog context alongside alerts and charts
- ✅ **Inspect Page (Repair Orders Dashboard)**: Completed end-to-end implementation
  - Created `/inspect` route with Repair Orders management dashboard
  - Backend API: `/api/v1/inspect/repair-orders` with filtering support
  - Database model: `RepairOrder` with all required fields
  - Seed data: 61 repair orders distributed across 5 statuses
  - Implemented 5 status panels matching QSourceGroup design:
    - I - ROs Awaiting Dispatch (with "Close Old ROs" and "Export" buttons)
    - II - ROs in Inspection (with "Export" button)
    - III - ROs Pending Approval (with "Export" button, color-coded rows)
    - IV - ROs in Repair (with "Export" button)
    - V - ROs Pending Review (with "Close All" and "Export" buttons)
  - Header controls:
    - "Legend" button
    - "Go to RO..." search field (filters ROs in real-time)
    - Total ROs count display (updates with filters)
    - Filters: RO TYPE, SHOP TYPE, WAITER dropdowns (all filter backend data)
  - Table columns: P (Priority), RO (Repair Order ID), Tag, Promised, E (Indicator), Customer, Adv (Advisor), Tech (Technician), MT (Metric Time), PT (Process Time)
  - Color coding: Green highlights for urgent ROs, red for overdue, alternating row colors
  - TanStack Query integration with 30-second auto-refetch
  - Added FloatingChatBot with RO context
  - Bot can answer questions about:
    - Repair orders and their status
    - RO workflow and processes
    - Inspection tools (pictures, video, real-time status updates)
    - Customer and technician information
    - Process times and metrics
  - Loading states and error handling implemented
- ✅ **Engage Page (Customer Experience Management)**: Completed implementation with dummy data
  - Created `/engage` route with Customer Experience Management focus
  - **Header**: Updated to "Customer Experience Management" with subtitle "Personalized service experience to speed up the check-in process"
  - **Header Controls**:
    - Date navigation (previous/next day, today button)
    - "All Advisors" dropdown filter
    - "Status" dropdown filter (Not Arrived, Checked In, In Progress, Completed, Cancelled)
    - "Needs Action" button with count badge
    - **Quick Search**: Search by customer name, VIN, vehicle, or RO number
  - **Timeline View**: Appointments organized by time slots with enhanced customer information
  - **Enhanced Appointment Cards**:
    - Vehicle (year, make, model) with color-coded icon (blue, red, gray)
    - **Customer Information**:
      - Customer name with user icon
      - Phone number and email (with icons)
      - Loyalty tier badge (Platinum, Gold, Silver)
      - Service history count and last visit date
      - Preferred services displayed as badges
    - VIN, mileage, advisor information
    - Service type and estimated duration
    - Status badge with icons (Not Arrived, Checked In, In Progress, etc.)
    - RO number for active appointments
    - **Quick Check-In Button**: One-click check-in for "Not Arrived" appointments
  - **Quick Check-In Modal**:
    - Customer information section (name, phone, email, loyalty tier)
    - Vehicle information section (year, make, model, VIN, mileage)
    - Service details (service type, estimated duration, assigned advisor)
    - **Personalized Experience Section**:
      - Service history with visit count and last visit date
      - Preferred services displayed prominently
    - Complete check-in action button
  - **Features**:
    - Personalized service experience based on customer history
    - Fast check-in process with pre-filled information
    - Customer loyalty tier recognition
    - Service preferences display
    - Real-time search and filtering
    - Color-coded status indicators with icons
  - Appointments sorted chronologically by time
  - Color-coded status backgrounds
  - Added FloatingChatBot with enhanced schedule context
  - Bot can answer questions about:
    - Daily appointments and schedule
    - Customer check-in process
    - Customer loyalty tiers and preferences
    - Service history and personalized recommendations
    - Vehicle service schedules
    - Customer arrivals and status
    - Advisor assignments
    - Appointment management
  - **Backend Integration**: ✅ Completed
    - API endpoint: `/api/v1/engage/appointments` (GET)
    - Check-in endpoint: `/api/v1/engage/check-in/{appointment_id}` (POST)
    - Database models: `Customer` and enhanced `ServiceAppointment`
    - Seed data: 8 customers and 8 service appointments
    - Service methods: `get_service_appointments()`, `check_in_appointment()`, `get_appointment_needs_action_count()`
    - Full end-to-end integration with TanStack Query

---

## 🚀 Next Steps

- [ ] Add more dashboard APIs as needed
- [ ] Implement additional analysis tools
- [ ] Add more demo scenarios
- [ ] Enhance frontend visualizations
- [ ] Add unit tests for APIs

