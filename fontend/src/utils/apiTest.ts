// Simple API test utility for development
import { demoScenariosService } from '@/lib/api/demoScenarios';
import { alertsService } from '@/lib/api/alerts';
import { dataCatalogService } from '@/lib/api/dataCatalog';

export const testApiEndpoints = async () => {
  console.log('🧪 Testing API endpoints...');
  
  try {
    // Test demo scenarios
    console.log('📋 Testing demo scenarios...');
    const scenarios = await demoScenariosService.getScenarios();
    console.log('✅ Demo scenarios:', scenarios.scenarios.length, 'scenarios loaded');
    
    // Test alerts
    console.log('🚨 Testing alerts...');
    const alerts = await alertsService.getAlerts();
    console.log('✅ Alerts:', alerts.alerts.length, 'alerts loaded');
    
    // Test data catalog
    console.log('📊 Testing data catalog...');
    const catalog = await dataCatalogService.getTables();
    console.log('✅ Data catalog:', catalog.tables.length, 'tables loaded');
    
    console.log('🎉 All API endpoints working!');
    return true;
  } catch (error) {
    console.error('❌ API test failed:', error);
    return false;
  }
};

// Export for use in development console
if (typeof window !== 'undefined') {
  (window as any).testApi = testApiEndpoints;
}