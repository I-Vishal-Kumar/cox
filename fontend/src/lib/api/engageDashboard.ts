import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Customer {
  customer_id?: number;
  phone?: string;
  email?: string;
  loyalty_tier?: 'Platinum' | 'Gold' | 'Silver';
  preferred_services: string[];
  service_history_count: number;
  last_visit_date?: string;
}

export interface ServiceAppointment {
  id: number;
  appointment_date: string;
  appointment_time: string;
  service_type: string;
  estimated_duration?: string;
  vehicle_vin: string;
  vehicle_year: number;
  vehicle_make: string;
  vehicle_model: string;
  vehicle_mileage?: string;
  vehicle_icon_color: 'blue' | 'red' | 'gray';
  customer_name: string;
  advisor: string;
  secondary_contact?: string;
  status: 'not_arrived' | 'checked_in' | 'in_progress' | 'completed' | 'cancelled';
  ro_number?: string;
  code?: string;
  notes?: string;
  // Customer fields (from join)
  phone?: string;
  email?: string;
  loyalty_tier?: 'Platinum' | 'Gold' | 'Silver';
  preferred_services: string[];
  service_history_count: number;
  last_visit_date?: string;
}

export interface EngageDashboardParams {
  date?: string; // YYYY-MM-DD
  advisor?: string;
  status?: string;
  search?: string;
}

export interface EngageDashboardResponse {
  appointments: ServiceAppointment[];
  needs_action_count: number;
}

class EngageDashboardService {
  async getAppointments(params: EngageDashboardParams = {}): Promise<EngageDashboardResponse> {
    const queryParams = new URLSearchParams();
    if (params.date) queryParams.append('date', params.date);
    if (params.advisor && params.advisor !== 'All') queryParams.append('advisor', params.advisor);
    if (params.status && params.status !== 'All') queryParams.append('status', params.status);
    if (params.search) queryParams.append('search', params.search);

    const response = await fetch(`${API_BASE_URL}/api/v1/engage/appointments?${queryParams.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch appointments: ${response.statusText}`);
    }
    return response.json();
  }

  async checkInAppointment(appointmentId: number): Promise<{ success: boolean; id: number; status: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/engage/check-in/${appointmentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error(`Failed to check in appointment: ${response.statusText}`);
    }
    return response.json();
  }
}

export const engageDashboardService = new EngageDashboardService();

// React Query hooks
export function useEngageAppointments(params: EngageDashboardParams = {}) {
  return useQuery({
    queryKey: ['engage-appointments', params],
    queryFn: () => engageDashboardService.getAppointments(params),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useCheckInAppointment() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (appointmentId: number) => engageDashboardService.checkInAppointment(appointmentId),
    onSuccess: () => {
      // Invalidate and refetch appointments
      queryClient.invalidateQueries({ queryKey: ['engage-appointments'] });
    },
  });
}

