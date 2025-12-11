import { useQuery } from '@tanstack/react-query';
import { demoScenariosService } from '@/lib/api/demoScenarios';

export const useDemoScenarios = () => {
  return useQuery({
    queryKey: ['demoScenarios'],
    queryFn: demoScenariosService.getScenarios,
    select: (data) => data.scenarios,
  });
};