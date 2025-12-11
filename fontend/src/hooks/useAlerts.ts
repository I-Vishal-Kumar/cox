import { useQuery } from '@tanstack/react-query';
import { alertsService, transformAlert } from '@/lib/api/alerts';

export const useAlerts = () => {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: alertsService.getAlerts,
    select: (data) => data.alerts.map(transformAlert),
    refetchInterval: 30000, // Refetch every 30 seconds for live alerts
  });
};