import { apiClient } from './config';

// ==================== TYPES ====================

export interface CategoryScores {
  sales: number | null;
  service: number | null;
  fni: number | null;
  logistics: number | null;
  manufacturing: number | null;
}

export interface KPICounts {
  total: number;
  on_target: number;
  at_risk: number;
  critical: number;
}

export interface RiskItem {
  metric: string;
  severity: string;
  change_percent: number;
  category: string;
  region: string;
  root_cause: string;
}

export interface PerformerItem {
  metric: string;
  category: string;
  region: string;
  value: number;
  target: number;
  performance: string;
}

export interface Recommendation {
  priority: string;
  category: string;
  action: string;
  expected_impact: string;
}

export interface HealthScoreResponse {
  score_date: string;
  overall_score: number;
  category_scores: CategoryScores;
  kpi_counts: KPICounts;
  top_risks: RiskItem[];
  top_performers: PerformerItem[];
  recommendations: Recommendation[];
  generated_at: string;
}

export interface HealthScoreHistoryItem {
  date: string;
  overall_score: number;
  sales_score: number | null;
  service_score: number | null;
  fni_score: number | null;
  logistics_score: number | null;
  manufacturing_score: number | null;
  kpis_on_target: number;
  kpis_at_risk: number;
  kpis_critical: number;
}

export interface Forecast {
  metric_name: string;
  category: string;
  forecast_date: string;
  predicted_value: number;
  lower_bound: number;
  upper_bound: number;
  confidence_level: number;
  actual_value: number | null;
  at_risk: boolean;
  risk_reason: string | null;
  model_used: string;
}

export interface ForecastsResponse {
  forecasts: Forecast[];
}

export interface DriverDecomposition {
  metric_name: string;
  analysis_date: string;
  category: string;
  total_change: number;
  total_change_percent: number;
  drivers: {
    price: { impact: number | null; details?: any };
    volume: { impact: number | null };
    mix: { impact: number | null; details?: any };
    regional: { impact: number | null; details?: any };
    seasonality: { impact: number | null; details?: any };
    other: { impact: number | null };
  };
  primary_driver: string;
  insights: string[];
}

export interface ScanResult {
  status: string;
  scan_type: string;
  anomalies_detected: number;
  alerts_created: number;
  health_score: number;
  forecasts_generated: number;
  completed_at?: string;
  error?: string;
}

export interface ScanHistoryItem {
  id: number;
  scan_type: string;
  status: string;
  scheduled_at: string;
  started_at: string | null;
  completed_at: string | null;
  anomalies_detected: number;
  alerts_created: number;
  health_score_generated: boolean;
  forecasts_generated: number;
  error_message: string | null;
}

export interface KPIDashboardResponse {
  health_score: HealthScoreResponse;
  active_alerts: any[];
  forecasts: Forecast[];
  recommendations: Recommendation[];
  last_updated: string;
}

// ==================== API SERVICE ====================

export const kpiMonitoringService = {
  // Health Score
  getHealthScore: (): Promise<HealthScoreResponse> =>
    apiClient.get('/kpi/health-score'),

  generateHealthScore: (): Promise<HealthScoreResponse> =>
    apiClient.post('/kpi/health-score/generate'),

  getHealthScoreHistory: (days: number = 30): Promise<{ history: HealthScoreHistoryItem[] }> =>
    apiClient.get(`/kpi/health-score/history?days=${days}`),

  // Forecasts
  getForecasts: (metricName?: string, days: number = 7): Promise<ForecastsResponse> => {
    let url = `/kpi/forecasts?days=${days}`;
    if (metricName) {
      url += `&metric_name=${encodeURIComponent(metricName)}`;
    }
    return apiClient.get(url);
  },

  generateForecasts: (daysAhead: number = 7): Promise<{ forecasts_generated: number; forecasts: any[] }> =>
    apiClient.post(`/kpi/forecasts/generate?days_ahead=${daysAhead}`),

  // Driver Decomposition
  getDecomposition: (metricName: string, region?: string): Promise<DriverDecomposition> => {
    let url = `/kpi/decomposition/${encodeURIComponent(metricName)}`;
    if (region) {
      url += `?region=${encodeURIComponent(region)}`;
    }
    return apiClient.get(url);
  },

  analyzeDecomposition: (metricName: string, region?: string): Promise<{ metric_name: string; analysis_date: string; decomposition: any }> => {
    let url = `/kpi/decomposition/analyze?metric_name=${encodeURIComponent(metricName)}`;
    if (region) {
      url += `&region=${encodeURIComponent(region)}`;
    }
    return apiClient.post(url);
  },

  // Scheduled Scanning
  triggerScan: (scanType: string = 'manual'): Promise<ScanResult> =>
    apiClient.post(`/kpi/scan/trigger?scan_type=${scanType}`),

  getScanHistory: (limit: number = 10): Promise<{ scans: ScanHistoryItem[] }> =>
    apiClient.get(`/kpi/scan/history?limit=${limit}`),

  getSchedulerStatus: (): Promise<{ running: boolean; next_hourly_scan: string; next_daily_scan: string }> =>
    apiClient.get('/kpi/scan/status'),

  // Combined Dashboard
  getDashboard: (): Promise<KPIDashboardResponse> =>
    apiClient.get('/kpi/dashboard'),
};
