import { api } from '@/lib/api';
import type { Conversation, ConversationFilters, CreateConversationRequest, UpdateConversationRequest } from '@/types/conversation';
import type { Message, SendMessageRequest } from '@/types/message';
import type { PaginatedResponse } from '@/types';

export async function getConversations(filters?: ConversationFilters): Promise<PaginatedResponse<Conversation>> {
  return api.get<PaginatedResponse<Conversation>>('/api/v1/conversations', filters as Record<string, string | number | boolean | undefined>);
}

export async function getConversation(id: string): Promise<Conversation> {
  return api.get<Conversation>(`/api/v1/conversations/${id}`);
}

export async function createConversation(data: CreateConversationRequest): Promise<Conversation> {
  return api.post<Conversation>('/api/v1/conversations', data);
}

export async function updateConversation(id: string, data: UpdateConversationRequest): Promise<Conversation> {
  return api.patch<Conversation>(`/api/v1/conversations/${id}`, data);
}

export async function getMessages(conversationId: string): Promise<Message[]> {
  return api.get<Message[]>(`/api/v1/conversations/${conversationId}/messages`);
}

export async function addMessage(conversationId: string, data: SendMessageRequest): Promise<Message> {
  return api.post<Message>(`/api/v1/conversations/${conversationId}/messages`, data);
}
