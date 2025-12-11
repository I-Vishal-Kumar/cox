import { useQuery } from '@tanstack/react-query';
import { dataCatalogService, transformTable } from '@/lib/api/dataCatalog';

export const useDataCatalog = () => {
  return useQuery({
    queryKey: ['dataCatalog'],
    queryFn: dataCatalogService.getTables,
    select: (data) => data.tables.map(transformTable),
  });
};