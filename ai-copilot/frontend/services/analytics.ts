import { api } from '@/lib/api';
import type { AnalyticsDashboard, AgentPerformanceMetric } from '@/types';

export async function getDashboard(): Promise<AnalyticsDashboard> {
  return api.get<AnalyticsDashboard>('/api/v1/analytics/dashboard');
}

export async function getAgentMetrics(): Promise<AgentPerformanceMetric[]> {
  return api.get<AgentPerformanceMetric[]>('/api/v1/analytics/agents');
}

export async function getCallMetrics(): Promise<Record<string, unknown>> {
  return api.get<Record<string, unknown>>('/api/v1/analytics/calls');
}
