# Design Document

## Overview

This design implements the integration between the Cox Automotive frontend and backend systems, replacing hardcoded data with live API calls using TanStack Query for efficient data management. The implementation focuses on three immediately available integrations: chat demo scenarios, KPI alerts, and data catalog tables.

## Architecture

### High-Level Architecture
```
Frontend Components → TanStack Query → API Services → Backend Endpoints
                   ↓
              Loading/Error States (Tailwind CSS)
```

### Data Flow
1. **Component Mount**: Component requests data through TanStack Query hook
2. **Query Execution**: TanStack Query calls API service function
3. **API Request**: Service function makes HTTP request to backend
4. **Data Transformation**: Response data is transformed to match frontend structure
5. **State Management**: TanStack Query manages loading, success, and error states
6. **Component Render**: Component renders with live data and appropriate UI states

## Components and Interfaces

### TanStack Query Setup

#### Query Client Configuration
```typescript
// lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      refetchOnWindowFocus: false,
    },
  },
});
```

#### Provider Setup
```typescript
// app/layout.tsx or _app.tsx
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/queryClient';

export default function RootLayout({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

### API Services Layer

#### Base API Configuration
```typescript
// lib/api/config.ts
export const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = {
  get: async <T>(endpoint: string): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
  },
  
  post: async <T>(endpoint: string, data: any): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
  },
};
```

#### Demo Scenarios Service
```typescript
// lib/api/demoScenarios.ts
export interface DemoScenario {
  id: string;
  title: string;
  question: string;
  category: string;
}

export const demoScenariosService = {
  getScenarios: (): Promise<{ scenarios: DemoScenario[] }> =>
    apiClient.get('/demo/scenarios'),
};
```

#### KPI Alerts Service
```typescript
// lib/api/alerts.ts
export interface Alert {
  id: string;
  metric_name: string;
  current_value?: number;
  previous_value?: number;
  change_percent?: number;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
  root_cause?: string;
  category?: string;
}

export const alertsService = {
  getAlerts: (): Promise<{ alerts: Alert[] }> =>
    apiClient.get('/kpi/alerts'),
};
```

#### Data Catalog Service
```typescript
// lib/api/dataCatalog.ts
export interface TableColumn {
  name: string;
  type: string;
  description: string;
}

export interface DataTable {
  name: string;
  description: string;
  columns: TableColumn[];
  rowCount: string;
  lastUpdated: string;
  category: string;
}

export const dataCatalogService = {
  getTables: (): Promise<{ tables: DataTable[] }> =>
    apiClient.get('/data-catalog/tables'),
};
```

### Custom Hooks

#### Demo Scenarios Hook
```typescript
// hooks/useDemoScenarios.ts
import { useQuery } from '@tanstack/react-query';
import { demoScenariosService } from '@/lib/api/demoScenarios';

export const useDemoScenarios = () => {
  return useQuery({
    queryKey: ['demoScenarios'],
    queryFn: demoScenariosService.getScenarios,
    select: (data) => data.scenarios,
  });
};
```

#### KPI Alerts Hook
```typescript
// hooks/useAlerts.ts
import { useQuery } from '@tanstack/react-query';
import { alertsService } from '@/lib/api/alerts';

export const useAlerts = () => {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: alertsService.getAlerts,
    select: (data) => data.alerts.map(transformAlert),
    refetchInterval: 30000, // Refetch every 30 seconds for live alerts
  });
};

const transformAlert = (alert: any) => ({
  id: alert.id,
  metric_name: alert.metric || alert.metric_name,
  current_value: alert.current_value || 0,
  previous_value: alert.previous_value || 0,
  change_percent: alert.change_percent || 0,
  severity: alert.severity,
  message: alert.message,
  timestamp: alert.timestamp,
  root_cause: alert.root_cause || 'Analysis pending',
  category: alert.category || 'General',
});
```

#### Data Catalog Hook
```typescript
// hooks/useDataCatalog.ts
import { useQuery } from '@tanstack/react-query';
import { dataCatalogService } from '@/lib/api/dataCatalog';

export const useDataCatalog = () => {
  return useQuery({
    queryKey: ['dataCatalog'],
    queryFn: dataCatalogService.getTables,
    select: (data) => data.tables.map(transformTable),
  });
};

const transformTable = (table: any) => ({
  name: table.name,
  description: table.description,
  columns: Array.isArray(table.columns) 
    ? table.columns.map(col => typeof col === 'string' 
        ? { name: col, type: 'unknown', description: '' }
        : col)
    : [],
  rowCount: table.row_count || table.rowCount || '0',
  lastUpdated: table.lastUpdated || new Date().toISOString(),
  category: table.category || 'General',
});
```

## Data Models

### Frontend Data Structures
```typescript
// types/api.ts
export interface DemoScenario {
  id: string;
  title: string;
  question: string;
  category: string;
}

export interface Alert {
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

export interface DataTable {
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

### API Response Types
```typescript
// types/apiResponses.ts
export interface DemoScenariosResponse {
  scenarios: DemoScenario[];
}

export interface AlertsResponse {
  alerts: {
    id: string;
    severity: string;
    metric: string;
    message: string;
    timestamp: string;
  }[];
}

export interface DataCatalogResponse {
  tables: {
    name: string;
    description: string;
    columns: string[];
    row_count: string;
  }[];
  regions: string[];
  kpi_categories: string[];
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: TanStack Query Loading State Management
*For any* API call made through TanStack Query, the loading state should be true during the request and false when completed (success or error)
**Validates: Requirements 1.2**

### Property 2: API Caching Consistency
*For any* API call made twice within the cache time window, the second call should return cached data without making a network request
**Validates: Requirements 1.3**

### Property 3: Error Handling Universality
*For any* API call that fails, TanStack Query should provide error information that enables user-friendly error message display
**Validates: Requirements 1.4, 6.2**

### Property 4: Automatic Refetch Behavior
*For any* stale data according to TanStack Query configuration, accessing the component should trigger an automatic refetch
**Validates: Requirements 1.5**

### Property 5: Loading UI Consistency
*For any* component using TanStack Query, loading states should display appropriate skeleton loaders styled with Tailwind CSS
**Validates: Requirements 2.2, 3.2, 4.2, 6.1**

### Property 6: Data Rendering Consistency
*For any* successful API response, the data should be properly transformed and displayed in the component's UI
**Validates: Requirements 2.3, 3.3, 4.3**

### Property 7: Alert Data Transformation
*For any* alert data received from the backend, missing fields should be filled with sensible default values
**Validates: Requirements 3.4**

### Property 8: Column Data Transformation
*For any* table data with string array columns, they should be transformed to objects with name, type, and description properties
**Validates: Requirements 4.4**

### Property 9: API Request Configuration
*For any* API call made through the service layer, it should include proper headers and use the configured base URL
**Validates: Requirements 5.4**

### Property 10: Retry Mechanism Availability
*For any* recoverable error, the system should provide retry mechanisms that allow users to attempt the operation again
**Validates: Requirements 6.3**

### Property 11: Empty State Handling
*For any* API response that returns empty data, the system should display appropriate empty state UI
**Validates: Requirements 6.4**

### Property 12: API-Only Data Sources
*For any* component that previously used hardcoded data, after implementation it should only render data that originates from API responses
**Validates: Requirements 7.4, 7.5**

## Error Handling

### API Error Scenarios
1. **Network Errors**: Connection failures, timeouts
2. **HTTP Errors**: 4xx client errors, 5xx server errors
3. **Data Format Errors**: Unexpected response structure
4. **Transformation Errors**: Data conversion failures

### Error Handling Strategy
```typescript
// utils/errorHandling.ts
export const handleApiError = (error: Error) => {
  if (error.message.includes('fetch')) {
    return 'Network connection failed. Please check your internet connection.';
  }
  if (error.message.includes('404')) {
    return 'The requested data was not found.';
  }
  if (error.message.includes('500')) {
    return 'Server error occurred. Please try again later.';
  }
  return 'An unexpected error occurred. Please try again.';
};
```

### Fallback Strategies
1. **Cached Data**: TanStack Query serves stale data when available
2. **Empty States**: Graceful empty state displays when no data
3. **Retry Mechanisms**: Automatic retry with exponential backoff
4. **User-Initiated Retry**: Manual retry buttons in error states

## Testing Strategy

### Unit Testing
- Test API service functions with mocked responses
- Test data transformation utilities with various input formats
- Test custom hooks with React Testing Library and TanStack Query testing utilities
- Test error handling scenarios with simulated API failures

### Property-Based Testing
- Property tests will use React Testing Library with TanStack Query testing utilities
- Each property-based test will run a minimum of 100 iterations
- Tests will generate random API responses to verify transformation consistency
- Error scenarios will be tested with random failure conditions

**Property-Based Testing Library**: React Testing Library with @tanstack/react-query testing utilities

### Integration Testing
- Test complete data flow from component mount to data display
- Test loading states and transitions
- Test error recovery and retry mechanisms
- Test cache behavior and data freshness

### UI Component Testing
- Test loading skeleton displays with Tailwind CSS classes
- Test error state rendering and retry button functionality
- Test successful data rendering in existing component layouts
- Test responsive design with various data sizes