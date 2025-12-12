import { apiClient } from './config';

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

export interface BackendAlert {
  id: string;
  severity: string;
  metric_name?: string;  // Backend returns metric_name
  metric?: string;       // Fallback for old format
  message: string;
  timestamp: string;
  current_value?: number;
  previous_value?: number;
  change_percent?: number;
  root_cause?: string;
  category?: string;
}

export interface AlertsResponse {
  alerts: BackendAlert[];
}

// Transform backend alert to frontend format
export const transformAlert = (alert: BackendAlert): Alert => ({
  id: alert.id || `${alert.metric_name || alert.metric}_${alert.timestamp}`,
  metric_name: alert.metric_name || alert.metric || 'Unknown Metric',
  current_value: alert.current_value || 0,
  previous_value: alert.previous_value || 0,
  change_percent: alert.change_percent || 0,
  severity: alert.severity as 'critical' | 'warning' | 'info',
  message: alert.message || `${alert.metric_name || alert.metric} alert`,
  timestamp: alert.timestamp,
  root_cause: alert.root_cause || 'Analysis pending',
  category: alert.category || 'General',
});

export const alertsService = {
  getAlerts: (): Promise<AlertsResponse> =>
    apiClient.get('/kpi/alerts'),
  detectAnomalies: (): Promise<{ anomalies_detected: number; alerts_stored: number; timestamp: string }> =>
    apiClient.post('/kpi/alerts/detect'),
  seedAnomalies: (): Promise<{ alerts_created: number; timestamp: string }> =>
    apiClient.post('/kpi/alerts/seed'),
  dismissAlert: (alertId: string, dismissedBy?: string): Promise<{ success: boolean; message: string }> =>
    apiClient.post(`/kpi/alerts/${alertId}/dismiss`, null, { params: { dismissed_by: dismissedBy || 'user' } }),
  getAlertDetails: (alertId: string): Promise<{ alert: any }> =>
    apiClient.get(`/kpi/alerts/${alertId}`),
};