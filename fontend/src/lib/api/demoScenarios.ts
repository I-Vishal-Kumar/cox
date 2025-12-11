import { apiClient } from './config';

export interface DemoScenario {
  id: string;
  title: string;
  question: string;
  category: string;
}

export interface DemoScenariosResponse {
  scenarios: DemoScenario[];
}

export const demoScenariosService = {
  getScenarios: (): Promise<DemoScenariosResponse> =>
    apiClient.get('/demo/scenarios'),
};