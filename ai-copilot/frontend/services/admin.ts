import { api } from '@/lib/api';
import type { Agent } from '@/types/user';
import type { AIConfig, ApiKeyInfo, CreateApiKeyRequest, CreateApiKeyResponse, UsageStats } from '@/types';

export async function getAgents(): Promise<Agent[]> {
  return api.get<Agent[]>('/api/v1/admin/agents');
}

export async function updateAgent(id: string, data: Partial<Agent>): Promise<Agent> {
  return api.patch<Agent>(`/api/v1/admin/agents/${id}`, data);
}

export async function getAIConfig(): Promise<AIConfig> {
  return api.get<AIConfig>('/api/v1/admin/config/ai');
}

export async function updateAIConfig(data: Partial<AIConfig>): Promise<AIConfig> {
  return api.patch<AIConfig>('/api/v1/admin/config/ai', data);
}

export async function getAPIKeys(): Promise<ApiKeyInfo[]> {
  return api.get<ApiKeyInfo[]>('/api/v1/admin/api-keys');
}

export async function createAPIKey(data: CreateApiKeyRequest): Promise<CreateApiKeyResponse> {
  return api.post<CreateApiKeyResponse>('/api/v1/admin/api-keys', data);
}

export async function deleteAPIKey(id: string): Promise<void> {
  return api.delete(`/api/v1/admin/api-keys/${id}`);
}

export async function getUsage(): Promise<UsageStats> {
  return api.get<UsageStats>('/api/v1/admin/usage');
}
