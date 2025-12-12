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

// Infer column type from column name
const inferColumnType = (columnName: string): string => {
  const name = columnName.toLowerCase();
  if (name.includes('id') || name.includes('_id')) return 'INTEGER';
  if (name.includes('date') || name.includes('time') || name.includes('timestamp')) return 'DATE/TIME';
  if (name.includes('rate') || name.includes('percent') || name.includes('ratio')) return 'DECIMAL';
  if (name.includes('revenue') || name.includes('amount') || name.includes('price') || name.includes('cost')) return 'DECIMAL';
  if (name.includes('count') || name.includes('number') || name === 'id') return 'INTEGER';
  if (name.includes('name') || name.includes('code') || name.includes('status') || name.includes('category')) return 'TEXT';
  if (name.includes('email') || name.includes('phone')) return 'TEXT';
  return 'TEXT';
};

// Generate column description from column name
const inferColumnDescription = (columnName: string, tableName: string): string => {
  const name = columnName.toLowerCase();
  if (name.includes('id') && name !== 'id') {
    return `Foreign key reference to ${name.replace('_id', '')} table`;
  }
  if (name.includes('date') || name.includes('time')) {
    return 'Date and time information';
  }
  if (name.includes('revenue') || name.includes('amount')) {
    return 'Monetary value';
  }
  if (name.includes('rate') || name.includes('percent')) {
    return 'Percentage or ratio value';
  }
  if (name.includes('count') || name.includes('number')) {
    return 'Numeric count or quantity';
  }
  return `${columnName.replace(/_/g, ' ')} field`;
};

// Infer category from table name and description
const inferCategory = (tableName: string, description: string): string => {
  const name = tableName.toLowerCase();
  const desc = description.toLowerCase();
  
  if (name.includes('dealer') || name.includes('dealership')) return 'Reference';
  if (name.includes('fni') || name.includes('finance') || name.includes('insurance')) return 'Transactions';
  if (name.includes('shipment') || name.includes('logistics') || name.includes('carrier') || name.includes('route')) return 'Logistics';
  if (name.includes('plant') || name.includes('downtime') || name.includes('manufacturing')) return 'Manufacturing';
  if (name.includes('marketing') || name.includes('campaign') || name.includes('invite')) return 'Marketing';
  if (name.includes('kpi') || name.includes('metric') || name.includes('analytics')) return 'Analytics';
  if (desc.includes('transaction') || desc.includes('revenue') || desc.includes('sales')) return 'Transactions';
  if (desc.includes('reference') || desc.includes('information')) return 'Reference';
  
  return 'General';
};

// Transform backend table to frontend format
export const transformTable = (table: BackendTable): DataTable => ({
  name: table.name,
  description: table.description,
  columns: table.columns.map(col => ({
    name: col,
    type: inferColumnType(col),
    description: inferColumnDescription(col, table.name),
  })),
  rowCount: table.row_count,
  lastUpdated: new Date().toISOString(),
  category: inferCategory(table.name, table.description),
});

export const dataCatalogService = {
  getTables: (): Promise<DataCatalogResponse> =>
    apiClient.get('/data-catalog/tables'),
};