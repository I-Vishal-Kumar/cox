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
  metric: string;
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
  id: alert.id,
  metric_name: alert.metric,
  current_value: alert.current_value || 0,
  previous_value: alert.previous_value || 0,
  change_percent: alert.change_percent || 0,
  severity: alert.severity as 'critical' | 'warning' | 'info',
  message: alert.message,
  timestamp: alert.timestamp,
  root_cause: alert.root_cause || 'Analysis pending',
  category: alert.category || 'General',
});

export const alertsService = {
  getAlerts: (): Promise<AlertsResponse> =>
    apiClient.get('/kpi/alerts'),
};