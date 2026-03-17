export * from './user';
export * from './ticket';
export * from './conversation';
export * from './message';
export * from './knowledge';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface DashboardStats {
  open_tickets: number;
  active_conversations: number;
  avg_response_time: number;
  avg_resolution_time: number;
  csat_score: number;
  ai_resolution_rate: number;
  total_messages_today: number;
  active_agents: number;
}

export interface AIConfig {
  model: string;
  temperature: number;
  max_tokens: number;
  top_k: number;
  similarity_threshold: number;
  system_prompt?: string;
}

export interface ApiKeyInfo {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at?: string;
  is_active: boolean;
}

export interface CreateApiKeyRequest {
  name: string;
}

export interface CreateApiKeyResponse {
  id: string;
  name: string;
  key: string;
  created_at: string;
}

export interface UsageStats {
  total_api_calls: number;
  total_tokens_used: number;
  total_conversations: number;
  total_tickets: number;
  period_start: string;
  period_end: string;
}

export interface AnalyticsDashboard {
  csat_over_time: TimeSeriesPoint[];
  resolution_time_over_time: TimeSeriesPoint[];
  sentiment_distribution: ChartDataPoint[];
  channel_breakdown: ChartDataPoint[];
  agent_performance: AgentPerformanceMetric[];
  ai_vs_human_resolution: ChartDataPoint[];
}

export interface TimeSeriesPoint {
  date: string;
  value: number;
}

export interface ChartDataPoint {
  name: string;
  value: number;
  color?: string;
}

export interface AgentPerformanceMetric {
  agent_id: string;
  agent_name: string;
  tickets_resolved: number;
  avg_response_time: number;
  avg_resolution_time: number;
  csat_score: number;
  active_conversations: number;
}
