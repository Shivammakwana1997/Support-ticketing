import type { Customer, Agent } from './user';

export type TicketStatus = 'open' | 'pending' | 'resolved' | 'closed';
export type Priority = 'low' | 'medium' | 'high' | 'urgent';
export type Channel = 'chat' | 'email' | 'whatsapp' | 'sms' | 'slack' | 'teams' | 'voice' | 'video';

export interface Ticket {
  id: string;
  subject: string;
  description: string;
  status: TicketStatus;
  priority: Priority;
  channel: Channel;
  customer_id: string;
  customer?: Customer;
  assigned_agent_id?: string;
  assigned_agent?: Agent;
  conversation_id?: string;
  tags: string[];
  sla_deadline?: string;
  first_response_at?: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTicketRequest {
  subject: string;
  description: string;
  priority?: Priority;
  channel?: Channel;
  tags?: string[];
}

export interface UpdateTicketRequest {
  status?: TicketStatus;
  priority?: Priority;
  assigned_agent_id?: string;
  tags?: string[];
}

export interface TicketSummary {
  summary: string;
  key_points: string[];
  sentiment: string;
  suggested_actions: string[];
}

export interface TicketFilters {
  status?: TicketStatus;
  priority?: Priority;
  assigned_agent_id?: string;
  channel?: Channel;
  search?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}
