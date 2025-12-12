import { apiClient } from './config';

export interface RepairOrder {
  id: number;
  ro: string;
  p: string;
  tag: string;
  promised: string;
  promised_date: string;
  e: string;
  customer: string;
  adv: string;
  tech: string;
  mt: string;
  pt: string;
  status: 'awaiting_dispatch' | 'in_inspection' | 'pending_approval' | 'in_repair' | 'pending_review';
  ro_type?: string;
  shop_type?: string;
  waiter?: string;
  is_overdue?: boolean;
  is_urgent?: boolean;
}

export interface RepairOrdersResponse {
  repair_orders: RepairOrder[];
}

export interface InspectDashboardParams {
  ro_type?: string;
  shop_type?: string;
  waiter?: string;
  search?: string;
}

export const inspectDashboardService = {
  getRepairOrders: async (params?: InspectDashboardParams): Promise<RepairOrdersResponse> => {
    const queryParams = new URLSearchParams();
    if (params?.ro_type) queryParams.append('ro_type', params.ro_type);
    if (params?.shop_type) queryParams.append('shop_type', params.shop_type);
    if (params?.waiter) queryParams.append('waiter', params.waiter);
    if (params?.search) queryParams.append('search', params.search);
    
    const queryString = queryParams.toString();
    const url = `/inspect/repair-orders${queryString ? `?${queryString}` : ''}`;
    return apiClient.get(url);
  },
};

