'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import type { ChatMessage, WebSocketMessage } from '@/types/message';

interface UseChatReturn {
  messages: ChatMessage[];
  sendMessage: (content: string) => void;
  isTyping: boolean;
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  clearMessages: () => void;
}

export function useChat(conversationId: string | null): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const wsPath = conversationId ? `/api/v1/ws/chat/${conversationId}` : '';
  const { isConnected, lastMessage, send, connect, disconnect } = useWebSocket(
    wsPath,
    !!conversationId
  );

  useEffect(() => {
    if (!lastMessage) return;

    switch (lastMessage.type) {
      case 'message': {
        const payload = lastMessage.payload as {
          id?: string;
          content?: string;
          sender_type?: string;
          sender_name?: string;
          citations?: ChatMessage['citations'];
          created_at?: string;
        };
        const newMessage: ChatMessage = {
          id: payload.id || crypto.randomUUID(),
          role: payload.sender_type === 'customer' ? 'user' : 'assistant',
          content: payload.content || '',
          sender_name: payload.sender_name,
          sender_type: payload.sender_type as ChatMessage['sender_type'],
          citations: payload.citations,
          timestamp: payload.created_at || new Date().toISOString(),
        };
        setMessages((prev) => [...prev, newMessage]);
        setIsTyping(false);
        break;
      }
      case 'typing': {
        setIsTyping(true);
        if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
        typingTimeoutRef.current = setTimeout(() => setIsTyping(false), 3000);
        break;
      }
      case 'error': {
        const errorPayload = lastMessage.payload as { detail?: string };
        const errorMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'system',
          content: errorPayload.detail || 'An error occurred',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
        break;
      }
    }
  }, [lastMessage]);

  const sendMessage = useCallback(
    (content: string) => {
      if (!content.trim()) return;

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        sender_type: 'customer',
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);

      const wsMessage: WebSocketMessage = {
        type: 'message',
        payload: { content },
      };
      send(wsMessage);
    },
    [send]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    sendMessage,
    isTyping,
    isConnected,
    connect,
    disconnect,
    clearMessages,
  };
}
