import { apiClient } from './config';

export interface TableColumn {
  name: string;
  type: string;
  description: string;
}

export interface DataTable {
  name: string;
  description: string;
  columns: TableColumn[];
  rowCount: string;
  lastUpdated: string;
  category: string;
}

export interface BackendTable {
  name: string;
  description: string;
  columns: string[];
  row_count: string;
}

export interface DataCatalogResponse {
  tables: BackendTable[];
  regions: string[];
  kpi_categories: string[];
}

// Transform backend table to frontend format
export const transformTable = (table: BackendTable): DataTable => ({
  name: table.name,
  description: table.description,
  columns: table.columns.map(col => ({
    name: col,
    type: 'unknown',
    description: '',
  })),
  rowCount: table.row_count,
  lastUpdated: new Date().toISOString(),
  category: 'General',
});

export const dataCatalogService = {
  getTables: (): Promise<DataCatalogResponse> =>
    apiClient.get('/data-catalog/tables'),
};