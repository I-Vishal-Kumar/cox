// API Response Types

export interface ChatResponse {
  message: string;
  conversation_id: string;
  query_type: string;
  sql_query?: string;
  data?: Record<string, unknown>[];
  chart_config?: ChartConfig;
  recommendations?: string[];
}

export interface ChartConfig {
  type: 'bar' | 'line' | 'pie' | 'horizontal_bar';
  title: string;
  x_axis?: string;
  y_axis?: string;
  labels?: string;
  values?: string;
}

export interface KPIAlert {
  id: string;
  metric_name: string;
  current_value: number;
  previous_value?: number;
  change_percent?: number;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  timestamp: string;
  root_cause?: string;
}

export interface ProgramPerformance {
  campaign_name: string;
  category: string;
  emails_sent: number;
  unique_opens: number;
  open_rate: number;
  ro_count: number;
  revenue: number;
}

export interface ProgramSummary {
  total_programs: number;
  total_emails: number;
  total_opens: number;
  avg_open_rate: number;
  total_ros: number;
  total_revenue: number;
}

export interface InviteDashboardData {
  program_summary: ProgramSummary;
  program_performance: ProgramPerformance[];
  monthly_metrics: MonthlyMetric[];
  last_updated: string;
}

export interface MonthlyMetric {
  month: string;
  emails_sent: number;
  unique_opens: number;
  ro_count: number;
  revenue: number;
}

export interface DemoScenario {
  id: string;
  title: string;
  question: string;
  category: string;
}

export interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  data?: Record<string, unknown>[];
  chart_config?: ChartConfig;
  chartConfig?: ChartConfig;
  recommendations?: string[];
  sql_query?: string;
  sqlQuery?: string;
  queryType?: string;
}
// API Integration Types

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

// API Response Types
export interface DemoScenariosResponse {
  scenarios: DemoScenario[];
}

export interface AlertsResponse {
  alerts: Alert[];
}

export interface DataCatalogResponse {
  tables: DataTable[];
  regions: string[];
  kpi_categories: string[];
}