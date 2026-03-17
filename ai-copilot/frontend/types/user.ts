export type UserRole = 'admin' | 'agent' | 'viewer' | 'api' | 'user';
export type AgentStatus = 'available' | 'busy' | 'offline';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: string;
  user_id: string;
  user: User;
  status: AgentStatus;
  skills: string[];
  max_concurrent_conversations: number;
  active_conversations_count: number;
  average_rating?: number;
  total_resolved: number;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: string;
  external_id?: string;
  name: string;
  email: string;
  phone?: string;
  avatar_url?: string;
  metadata?: Record<string, unknown>;
  first_seen_at: string;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}
