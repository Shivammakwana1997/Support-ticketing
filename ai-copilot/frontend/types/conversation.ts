import type { Customer, Agent } from './user';
import type { Channel } from './ticket';

export type ConversationStatus = 'open' | 'pending' | 'closed';

export interface Conversation {
  id: string;
  customer_id: string;
  customer?: Customer;
  assigned_agent_id?: string;
  assigned_agent?: Agent;
  channel: Channel;
  status: ConversationStatus;
  subject?: string;
  last_message_at?: string;
  last_message_preview?: string;
  unread_count: number;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CreateConversationRequest {
  channel: Channel;
  subject?: string;
  initial_message?: string;
}

export interface UpdateConversationRequest {
  status?: ConversationStatus;
  assigned_agent_id?: string;
}

export interface ConversationFilters {
  status?: ConversationStatus;
  assigned_agent_id?: string;
  channel?: Channel;
  search?: string;
  page?: number;
  page_size?: number;
}
