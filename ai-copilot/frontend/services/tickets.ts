import { api } from '@/lib/api';
import type { Ticket, TicketFilters, CreateTicketRequest, UpdateTicketRequest, TicketSummary } from '@/types/ticket';
import type { Message, SendMessageRequest } from '@/types/message';
import type { PaginatedResponse } from '@/types';

export async function getTickets(filters?: TicketFilters): Promise<PaginatedResponse<Ticket>> {
  return api.get<PaginatedResponse<Ticket>>('/api/v1/tickets', filters as Record<string, string | number | boolean | undefined>);
}

export async function getTicket(id: string): Promise<Ticket> {
  return api.get<Ticket>(`/api/v1/tickets/${id}`);
}

export async function createTicket(data: CreateTicketRequest): Promise<Ticket> {
  return api.post<Ticket>('/api/v1/tickets', data);
}

export async function updateTicket(id: string, data: UpdateTicketRequest): Promise<Ticket> {
  return api.patch<Ticket>(`/api/v1/tickets/${id}`, data);
}

export async function getTicketMessages(id: string): Promise<Message[]> {
  return api.get<Message[]>(`/api/v1/tickets/${id}/messages`);
}

export async function addTicketMessage(id: string, data: SendMessageRequest): Promise<Message> {
  return api.post<Message>(`/api/v1/tickets/${id}/messages`, data);
}

export async function getTicketSummary(id: string): Promise<TicketSummary> {
  return api.get<TicketSummary>(`/api/v1/tickets/${id}/summary`);
}

export async function routeTicket(id: string): Promise<Ticket> {
  return api.post<Ticket>(`/api/v1/tickets/${id}/route`);
}
