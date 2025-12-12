import { apiClient } from './config';

export interface PlantSummary {
  plant_name: string;
  plant_code: string;
  total_downtime: number;
  events: number;
  unplanned: number;
}

export interface DowntimeDetail {
  plant_name: string;
  plant_code: string;
  line_number: string;
  downtime_hours: number;
  reason_category: string;
  reason_detail: string;
  is_planned: boolean;
  supplier: string | null;
  event_date: string;
}

export interface CauseBreakdown {
  name: string;
  value: number;
  color: string;
}

export interface PlantDashboardResponse {
  plant_summary: PlantSummary[];
  downtime_details: DowntimeDetail[];
  cause_breakdown: CauseBreakdown[];
  overall_stats: {
    total_downtime: number;
    total_events: number;
    unplanned_downtime: number;
    plants_affected: number;
  };
}

// Transform backend data to match frontend structure
export const transformPlantSummary = (plant: any): PlantSummary => ({
  plant_name: plant.plant_name || '',
  plant_code: plant.plant_code || '',
  total_downtime: Number(plant.total_downtime || 0),
  events: Number(plant.events || 0),
  unplanned: Number(plant.unplanned || 0),
});

export const transformDowntimeDetail = (detail: any): DowntimeDetail => ({
  plant_name: detail.plant_name || '',
  plant_code: detail.plant_code || '',
  line_number: detail.line_number || '',
  downtime_hours: Number(detail.downtime_hours || 0),
  reason_category: detail.reason_category || '',
  reason_detail: detail.reason_detail || '',
  is_planned: Boolean(detail.is_planned || false),
  supplier: detail.supplier || null,
  event_date: detail.event_date || '',
});

// Category colors for charts
const CATEGORY_COLORS: Record<string, string> = {
  Maintenance: '#3b82f6',
  Quality: '#ef4444',
  Supply: '#f59e0b',
  Equipment: '#10b981',
};

export const transformCauseBreakdown = (details: DowntimeDetail[]): CauseBreakdown[] => {
  const breakdown = details.reduce((acc, detail) => {
    const category = detail.reason_category || 'Other';
    if (!acc[category]) {
      acc[category] = 0;
    }
    acc[category] += detail.downtime_hours;
    return acc;
  }, {} as Record<string, number>);

  return Object.entries(breakdown).map(([name, value]) => ({
    name,
    value: Number(value.toFixed(1)),
    color: CATEGORY_COLORS[name] || '#6b7280',
  }));
};

export const plantDashboardService = {
  getPlantDashboard: async (): Promise<PlantDashboardResponse> => {
    try {
      const response = await apiClient.get('/dashboard/plant');
      
      // Transform backend response
      const plantSummary = (response.plant_summary || []).map(transformPlantSummary);
      // Backend returns "detailed_events" but we expect "downtime_details"
      const downtimeDetails = ((response.downtime_details || response.detailed_events) || []).map(transformDowntimeDetail);
      const causeBreakdown = transformCauseBreakdown(downtimeDetails);
      
      // Calculate overall stats
      const totalDowntime = plantSummary.reduce((sum, p) => sum + p.total_downtime, 0);
      const totalEvents = downtimeDetails.length;
      const unplannedDowntime = downtimeDetails
        .filter(d => !d.is_planned)
        .reduce((sum, d) => sum + d.downtime_hours, 0);
      const plantsAffected = new Set(plantSummary.map(p => p.plant_code)).size;
      
      return {
        plant_summary: plantSummary,
        downtime_details: downtimeDetails,
        cause_breakdown: causeBreakdown,
        overall_stats: {
          total_downtime: Number(totalDowntime.toFixed(1)),
          total_events: totalEvents,
          unplanned_downtime: Number(unplannedDowntime.toFixed(1)),
          plants_affected: plantsAffected,
        },
      };
    } catch (error) {
      console.error('Error fetching plant dashboard:', error);
      throw error;
    }
  },
};

