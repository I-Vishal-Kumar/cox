import { apiClient } from './config';

export interface LogisticsOverallStats {
  total_shipments: number;
  delayed_shipments: number;
  delay_rate: number;
}

export interface LogisticsCarrierData {
  carrier: string;
  total_shipments: number;
  delayed_count: number;
  avg_dwell_time: number;
  delay_rate: number;
}

export interface LogisticsRouteData {
  route: string;
  carrier: string;
  total_shipments: number;
  delayed_count: number;
  delay_reason: string;
}

export interface LogisticsDelayReason {
  delay_reason: string;
  count: number;
}

export interface DwellTimeComparison {
  period: string;
  [carrier: string]: string | number;
}

export interface LogisticsDashboardResponse {
  overall_stats: LogisticsOverallStats;
  carrier_breakdown: LogisticsCarrierData[];
  route_analysis: LogisticsRouteData[];
  delay_reasons: LogisticsDelayReason[];
  dwell_time_comparison?: DwellTimeComparison[];
}

// Transform backend data to match frontend structure
export const transformCarrierData = (carrier: LogisticsCarrierData) => ({
  carrier: carrier.carrier,
  total: carrier.total_shipments,
  delayed: carrier.delayed_count,
  delay_rate: carrier.delay_rate,
  avg_dwell: carrier.avg_dwell_time,
});

export const transformRouteData = (route: LogisticsRouteData) => ({
  route: route.route,
  carrier: route.carrier,
  delayed: route.delayed_count,
  total: route.total_shipments,
  reason: route.delay_reason || 'Unknown',
});

export const transformDelayReasons = (reasons: LogisticsDelayReason[]) => {
  const colors = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6'];
  return reasons.map((reason, index) => ({
    name: reason.delay_reason,
    value: reason.count,
    color: colors[index % colors.length],
  }));
};

export const logisticsDashboardService = {
  getLogisticsDashboard: (): Promise<LogisticsDashboardResponse> =>
    apiClient.get('/dashboard/logistics'),
};