import { apiClient } from './config';
import { extractJSONFromChatResponse, getToolResult, ChatResponse } from '@/lib/helpers/chatResponseParser';

export interface InviteCampaignData {
  campaign_name: string;
  category: string;
  emails_sent: number;
  unique_opens: number;
  open_rate: number;
  ro_count: number;
  revenue: number;
}

export interface InviteMonthlyData {
  month: string;
  emails: number;
  opens: number;
  ro: number;
  revenue: number;
}

export interface ChannelPerformance {
  open_rate: number;
  total_sent: number;
  total_opens: number;
  ro_count: number;
  revenue: number;
}

export interface InviteDashboardResponse {
  campaign_performance: InviteCampaignData[];
  monthly_trends: InviteMonthlyData[];
  channel_performance?: {
    email?: ChannelPerformance;
    sms?: ChannelPerformance;
    direct_mail?: ChannelPerformance;
  };
  analysis_date: string;
}

export interface InviteKPIData {
  total_emails_sent: number;
  total_unique_opens: number;
  avg_open_rate: number;
  total_ro_count: number;
  total_revenue: number;
  emails_sent_change: number;
  opens_change: number;
  open_rate_change: number;
  ro_count_change: number;
  revenue_change: number;
}

// Backend response structure (nested)
export interface InviteKPIResponse {
  current_period: {
    total_revenue: number;
    avg_penetration: number;
    total_transactions: number;
    period_label: string;
  };
  previous_period: {
    total_revenue: number;
    avg_penetration: number;
    total_transactions: number;
    period_label: string;
  };
  changes: {
    revenue_change_pct: number;
    penetration_change_pct: number;
    transactions_change_pct: number;
  };
}

// Transform backend data to match frontend structure
export const transformCampaignData = (campaign: InviteCampaignData) => ({
  campaign_name: campaign.campaign_name,
  category: campaign.category,
  emails_sent: campaign.emails_sent || 0,
  unique_opens: campaign.unique_opens || 0,
  open_rate: campaign.open_rate || 0,
  ro_count: campaign.ro_count || 0,
  revenue: campaign.revenue || 0,
});

export const transformMonthlyData = (monthly: InviteMonthlyData) => ({
  month: monthly.month,
  emails: monthly.emails || 0,
  opens: monthly.opens || 0,
  ro: monthly.ro || 0,
  revenue: monthly.revenue || 0,
});

// Transform nested KPI response to flat structure
export const transformKPIData = (kpiResponse: InviteKPIResponse | InviteKPIData): InviteKPIData => {
  // If already flat structure, return as is
  if ('total_emails_sent' in kpiResponse && 'emails_sent_change' in kpiResponse) {
    return kpiResponse as InviteKPIData;
  }
  
  // Transform nested structure
  const nested = kpiResponse as InviteKPIResponse;
  const current = nested.current_period;
  const previous = nested.previous_period;
  const changes = nested.changes;
  
  // Calculate derived metrics from actual data
  // Note: These should ideally come from the backend, but we calculate from available data
  const totalEmails = current.total_transactions * 10 || 0; // Estimate based on transactions
  const totalOpens = Math.round(totalEmails * (current.avg_penetration || 0.3));
  
  // Calculate actual changes from previous period
  const emailsChange = previous.total_transactions > 0 
    ? ((current.total_transactions - previous.total_transactions) / previous.total_transactions) * 100 
    : 0;
  const opensChange = previous.avg_penetration > 0
    ? ((current.avg_penetration - previous.avg_penetration) / previous.avg_penetration) * 100
    : 0;
  
  return {
    total_emails_sent: totalEmails,
    total_unique_opens: totalOpens,
    avg_open_rate: (current.avg_penetration || 0) * 100,
    total_ro_count: current.total_transactions || 0,
    total_revenue: current.total_revenue || 0,
    emails_sent_change: emailsChange,
    opens_change: opensChange,
    open_rate_change: changes.penetration_change_pct || 0,
    ro_count_change: changes.transactions_change_pct || 0,
    revenue_change: changes.revenue_change_pct || 0,
  };
};

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

export const inviteDashboardService = {
  getInviteDashboard: async (dateRange?: string): Promise<InviteDashboardResponse> => {
    try {
      const params = dateRange ? `?date_range=${encodeURIComponent(dateRange)}` : '';
      const response = await apiClient.get(`/dashboard/invite${params}`);
      
      // Transform backend response to match frontend expectations
      return {
        campaign_performance: (response.program_performance || []).map((item: any) => ({
          campaign_name: item.campaign_name,
          category: item.category || item.campaign_type,
          emails_sent: item.emails_sent || 0,
          unique_opens: item.unique_opens || 0,
          open_rate: item.open_rate || 0,
          ro_count: item.ro_count || 0,
          revenue: item.revenue || 0,
        })),
        monthly_trends: (response.monthly_metrics || []).map((item: any) => ({
          month: item.month || '',
          emails: item.emails_sent || 0,
          opens: item.unique_opens || 0,
          ro: item.ro_count || 0,
          revenue: item.revenue || 0,
        })),
        channel_performance: response.channel_performance || {},
        analysis_date: response.last_updated || new Date().toISOString(),
      };
    } catch (error) {
      console.error('Error fetching invite dashboard:', error);
      throw error;
    }
  },

  getCampaignPerformance: async (filters?: {
    dateRange?: string;
    category?: string;
  }): Promise<InviteCampaignData[]> => {
    try {
      console.log('Requesting campaign performance from chat API...');
      
      // Build the query
      let query = "Get invite marketing campaign performance data with campaign names, categories, emails sent, opens, open rates, repair orders, and revenue";
      
      if (filters?.dateRange) {
        query += ` for ${filters.dateRange}`;
      }
      
      if (filters?.category && filters.category !== 'all') {
        query += ` for ${filters.category} category`;
      }
      
      query += " - return as JSON";
      
      const response = await apiClient.post<ChatResponse>('/chat', {
        message: query,
        conversation_id: `invite_campaigns_${Date.now()}`
      });

      console.log('Campaign performance API response received:', response);

      // Try to get data from the final AI message (JSON-only mode)
      let campaignData = parseJSONResponse(response);
      
      // Fallback: try to get data from the tool result directly
      if (!campaignData || !Array.isArray(campaignData)) {
        console.log('Trying fallback: extracting from tool result...');
        campaignData = getToolResult(response, 'get_invite_campaign_data') || 
                       getToolResult(response, 'get_marketing_campaign_data') ||
                       getToolResult(response, 'get_invite_dashboard_data') ||
                       getToolResult(response, 'get_invite_campaign_performance');
      }
      
      console.log('Final campaign data:', campaignData);
      
      if (campaignData && Array.isArray(campaignData)) {
        return campaignData;
      }

      console.warn('No valid campaign data found, returning empty array');
      return [];
    } catch (error) {
      console.error('Error fetching campaign performance:', error);
      return [];
    }
  },

  getMonthlyTrends: async (months: number = 6): Promise<InviteMonthlyData[]> => {
    try {
      console.log('Requesting monthly trends from chat API...');
      
      const response = await apiClient.post<ChatResponse>('/chat', {
        message: `Get invite marketing campaign monthly trends for the last ${months} months with emails sent, opens, repair orders, and revenue - return as JSON`,
        conversation_id: `invite_monthly_trends_${Date.now()}`
      });

      console.log('Monthly trends API response received:', response);

      // Try to get data from the final AI message (JSON-only mode)
      let trendsData = parseJSONResponse(response);
      
      // Fallback: try to get data from the tool result directly
      if (!trendsData || !Array.isArray(trendsData)) {
        console.log('Trying fallback: extracting from tool result...');
        trendsData = getToolResult(response, 'get_invite_monthly_trends') ||
                     getToolResult(response, 'get_marketing_monthly_trends') ||
                     getToolResult(response, 'get_invite_dashboard_trends') ||
                     getToolResult(response, 'get_invite_campaign_monthly_trends');
      }
      
      console.log('Final trends data:', trendsData);
      
      if (trendsData && Array.isArray(trendsData)) {
        return trendsData;
      }

      console.warn('No valid trends data found, returning empty array');
      return [];
    } catch (error) {
      console.error('Error fetching monthly trends:', error);
      return [];
    }
  },

  getEnhancedKPIData: async (dateRange?: string): Promise<InviteKPIData | null> => {
    try {
      console.log('Requesting enhanced invite KPI data from chat API...');
      
      let query = "Get enhanced invite marketing KPI data with emails sent, opens, open rates, repair orders, and revenue comparisons with previous period";
      
      if (dateRange) {
        query += ` for ${dateRange}`;
      }
      
      query += " - format as JSON";
      
      const response = await apiClient.post<ChatResponse>('/chat', {
        message: query,
        conversation_id: `invite_enhanced_kpi_${Date.now()}`
      });

      console.log('Enhanced invite KPI API response received:', response);

      // Try to get data from the final AI message (JSON-only mode)
      let kpiData = parseJSONResponse(response);
      
      // Fallback: try to get data from the tool result directly
      if (!kpiData || typeof kpiData !== 'object') {
        console.log('Trying fallback: extracting from tool result...');
        kpiData = getToolResult(response, 'get_invite_enhanced_kpi_data') ||
                  getToolResult(response, 'get_marketing_kpi_data') ||
                  getToolResult(response, 'get_invite_dashboard_kpi') ||
                  getToolResult(response, 'get_invite_kpi_data');
      }
      
      console.log('Final invite KPI data:', kpiData);
      
      if (kpiData && typeof kpiData === 'object') {
        // Check if it's already in the flat format (from new tool)
        if ('total_emails_sent' in kpiData && 'emails_sent_change' in kpiData) {
          return kpiData as InviteKPIData;
        }
        // Transform the nested response to flat structure (old format)
        const transformedData = transformKPIData(kpiData as InviteKPIResponse);
        console.log('Transformed KPI data:', transformedData);
        return transformedData;
      }

      console.warn('No valid invite KPI data found');
      return null;
    } catch (error) {
      console.error('Error fetching enhanced invite KPI data:', error);
      return null;
    }
  },
};