export type SenderType = 'customer' | 'agent' | 'system' | 'ai';

export interface Message {
  id: string;
  conversation_id: string;
  sender_type: SenderType;
  sender_id?: string;
  sender_name?: string;
  content: string;
  metadata?: Record<string, unknown>;
  citations?: Citation[];
  created_at: string;
}

export interface Citation {
  document_id: string;
  document_title: string;
  chunk_text: string;
  relevance_score: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sender_name?: string;
  sender_type?: SenderType;
  citations?: Citation[];
  timestamp: string;
  isTyping?: boolean;
}

export interface SendMessageRequest {
  content: string;
  sender_type?: SenderType;
}

export interface WebSocketMessage {
  type: 'message' | 'typing' | 'status' | 'error';
  payload: Record<string, unknown>;
}

export interface CopilotSuggestion {
  suggested_reply: string;
  confidence: number;
  sources: Citation[];
}

export interface CopilotSummary {
  summary: string;
  key_points: string[];
  sentiment: string;
  suggested_actions: string[];
}
