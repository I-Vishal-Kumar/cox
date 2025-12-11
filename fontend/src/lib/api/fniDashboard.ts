import { apiClient } from './config';
import { extractJSONFromChatResponse, getToolResult, ChatResponse as ParsedChatResponse } from '@/lib/helpers/chatResponseParser';

export interface FNIDealerData {
  dealer_name: string;
  region: string;
  dealer_code: string;
  this_week_revenue: number;
  last_week_revenue: number;
  current_penetration: number;
  previous_penetration: number;
  this_week_transactions: number;
  last_week_transactions: number;
}

export interface FNIManagerData {
  finance_manager: string;
  dealer_name: string;
  avg_penetration: number;
  transactions: number;
  total_revenue: number;
}

export interface FNIDashboardResponse {
  dealer_comparison: FNIDealerData[];
  manager_breakdown: FNIManagerData[];
  analysis_date: string;
}

export interface WeeklyTrendData {
  week: string;
  midwest: number;
  northeast: number;
  southeast: number;
  west: number;
}

// Use the ChatResponse interface from the parser
type ChatResponse = ParsedChatResponse;

export interface EnhancedKPIData {
  total_revenue_this_week: number;
  total_revenue_last_week: number;
  avg_penetration_this_week: number;
  avg_penetration_last_week: number;
  total_transactions_this_week: number;
  total_transactions_last_week: number;
}

// Transform backend data to match frontend structure
export const transformDealerData = (dealer: FNIDealerData) => ({
  dealer: dealer.dealer_name,
  this_week: dealer.this_week_revenue || 0,
  last_week: dealer.last_week_revenue || 0,
  change: dealer.last_week_revenue 
    ? ((dealer.this_week_revenue - dealer.last_week_revenue) / dealer.last_week_revenue) * 100
    : 0,
  penetration: Math.round(dealer.current_penetration || 0),
});

export const transformManagerData = (manager: FNIManagerData) => ({
  manager: manager.finance_manager,
  dealer: manager.dealer_name,
  penetration: manager.avg_penetration,
  transactions: manager.transactions,
  revenue: manager.total_revenue,
});

// Parse JSON response using the centralized parser
const parseJSONResponse = (response: ChatResponse): any => {
  try {
    console.log('Raw chat response:', response);
    
    // Use the centralized parser to extract JSON from the last AI message
    const data = extractJSONFromChatResponse(response);
    console.log('Parsed JSON data:', data);
    
    return data;
  } catch (error) {
    console.warn('Could not extract JSON from AI message, this is normal for non-JSON responses');
    console.log('Response was:', response);
    return null;
  }
};

export const fniDashboardService = {
  getFNIDashboard: (region?: string): Promise<FNIDashboardResponse> => {
    const params = region ? `?region=${encodeURIComponent(region)}` : '';
    return apiClient.get(`/dashboard/fni${params}`);
  },

  getWeeklyTrends: async (): Promise<WeeklyTrendData[]> => {
    try {
      console.log('Requesting weekly trends from chat API...');
      
      const response = await apiClient.post<ChatResponse>('/chat', {
        message: "Get weekly F&I revenue trends for the last 4 weeks - return as JSON",
        conversation_id: `dashboard_weekly_trends_${Date.now()}`
      });

      console.log('Chat API response received:', response);

      // Try to get data from the final AI message (JSON-only mode)
      let trendsData = parseJSONResponse(response);
      
      // Fallback: try to get data from the tool result directly
      if (!trendsData || !Array.isArray(trendsData)) {
        console.log('Trying fallback: extracting from tool result...');
        trendsData = getToolResult(response, 'get_weekly_fni_trends');
      }
      
      console.log('Final trends data:', trendsData);
      
      if (trendsData && Array.isArray(trendsData)) {
        return trendsData;
      }

      console.warn('No valid trends data found, returning empty array');
      // Fallback to empty array if no data
      return [];
    } catch (error) {
      console.error('Error fetching weekly trends:', error);
      // Return empty array on error - component will handle gracefully
      return [];
    }
  },

  getEnhancedKPIData: async (): Promise<EnhancedKPIData | null> => {
    try {
      console.log('Requesting enhanced KPI data from chat API...');
      
      const response = await apiClient.post<ChatResponse>('/chat', {
        message: "Get enhanced KPI data for this week with previous period comparison - give me JSON",
        conversation_id: `dashboard_enhanced_kpi_${Date.now()}`
      });

      console.log('Enhanced KPI API response received:', response);

      // Try to get data from the final AI message (JSON-only mode)
      let kpiData = parseJSONResponse(response);
      
      // Fallback: try to get data from the tool result directly
      if (!kpiData || typeof kpiData !== 'object') {
        console.log('Trying fallback: extracting from tool result...');
        kpiData = getToolResult(response, 'get_enhanced_kpi_data');
      }
      
      console.log('Final KPI data:', kpiData);
      
      if (kpiData && typeof kpiData === 'object') {
        return kpiData as EnhancedKPIData;
      }

      console.warn('No valid KPI data found');
      return null;
    } catch (error) {
      console.error('Error fetching enhanced KPI data:', error);
      return null;
    }
  },

  getFilteredFNIData: async (filters: {
    region?: string;
    period?: string;
    dealers?: string[];
    managers?: string[];
  }): Promise<FNIDashboardResponse | null> => {
    try {
      console.log('Requesting filtered F&I data from chat API...');
      
      // Build the filter query
      let filterQuery = "Get F&I data";
      
      if (filters.period) {
        filterQuery += ` for ${filters.period}`;
      }
      
      if (filters.region) {
        filterQuery += ` for ${filters.region} region`;
      }
      
      if (filters.dealers && filters.dealers.length > 0) {
        filterQuery += ` for dealers ${filters.dealers.join(', ')}`;
      }
      
      if (filters.managers && filters.managers.length > 0) {
        filterQuery += ` for managers ${filters.managers.join(', ')}`;
      }
      
      filterQuery += " - format as JSON";
      
      const response = await apiClient.post<ChatResponse>('/chat', {
        message: filterQuery,
        conversation_id: `dashboard_filtered_fni_${Date.now()}`
      });

      console.log('Filtered F&I API response received:', response);

      // Try to get data from the final AI message (JSON-only mode)
      let filteredData = parseJSONResponse(response);
      
      // Fallback: try to get data from the tool result directly
      if (!filteredData || typeof filteredData !== 'object') {
        console.log('Trying fallback: extracting from tool result...');
        filteredData = getToolResult(response, 'get_filtered_fni_data');
      }
      
      console.log('Final filtered data:', filteredData);
      
      if (filteredData && typeof filteredData === 'object') {
        return filteredData as FNIDashboardResponse;
      }

      console.warn('No valid filtered data found');
      return null;
    } catch (error) {
      console.error('Error fetching filtered F&I data:', error);
      return null;
    }
  },
};