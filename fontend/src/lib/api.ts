// API service for communicating with the backend
import { parseMessageContent } from '@/utils/messageParser';

const API_BASE = 'http://localhost:8000/api/v1';

export interface ChatResponse {
  message: string;
  conversation_id: string;
  query_type: string;
  sql_query?: string;
  data?: Record<string, unknown>[];
  chart_config?: {
    type: string;
    title: string;
    x_axis?: string;
    y_axis?: string;
  };
  recommendations?: string[];
}

export async function sendChatMessage(
  message: string,
  conversationId?: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();
  
  // Parse the message content using utility function
  data.message = parseMessageContent(data.message);

  return data;
}

export async function getInviteDashboard(dealerId?: number) {
  const params = dealerId ? `?dealer_id=${dealerId}` : '';
  const response = await fetch(`${API_BASE}/dashboard/invite${params}`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function getFNIDashboard(region?: string) {
  const params = region ? `?region=${region}` : '';
  const response = await fetch(`${API_BASE}/dashboard/fni${params}`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function getLogisticsDashboard() {
  const response = await fetch(`${API_BASE}/dashboard/logistics`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function getPlantDashboard() {
  const response = await fetch(`${API_BASE}/dashboard/plant`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function getKPIMetrics(
  category?: string,
  region?: string,
  days: number = 30
) {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (region) params.append('region', region);
  params.append('days', days.toString());

  const response = await fetch(`${API_BASE}/kpi/metrics?${params}`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function getKPIAlerts() {
  const response = await fetch(`${API_BASE}/kpi/alerts`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function getDataCatalog() {
  const response = await fetch(`${API_BASE}/data-catalog/tables`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function getDemoScenarios() {
  const response = await fetch(`${API_BASE}/demo/scenarios`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

// Health check
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch('http://localhost:8000/health');
    return response.ok;
  } catch {
    return false;
  }
}
