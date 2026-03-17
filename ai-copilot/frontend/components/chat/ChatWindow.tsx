'use client';

import { useEffect, useRef, useState } from 'react';
import { Bot, X, Wifi, WifiOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import type { ChatMessage as ChatMessageType } from '@/types/message';

interface ChatWindowProps {
  onClose?: () => void;
  conversationId?: string;
  messages?: ChatMessageType[];
  onSendMessage?: (content: string) => void;
  isTyping?: boolean;
  isConnected?: boolean;
  agentName?: string;
  fullPage?: boolean;
}

export function ChatWindow({
  onClose,
  messages: externalMessages,
  onSendMessage,
  isTyping = false,
  isConnected = true,
  agentName = 'AI Assistant',
  fullPage = false,
}: ChatWindowProps) {
  const [localMessages, setLocalMessages] = useState<ChatMessageType[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your AI support assistant. How can I help you today?",
      sender_name: 'AI Assistant',
      sender_type: 'ai',
      timestamp: new Date().toISOString(),
    },
  ]);

  const messages = externalMessages || localMessages;
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = (content: string) => {
    if (onSendMessage) {
      onSendMessage(content);
    } else {
      const userMsg: ChatMessageType = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        sender_type: 'customer',
        timestamp: new Date().toISOString(),
      };
      setLocalMessages((prev) => [...prev, userMsg]);

      setTimeout(() => {
        const aiMsg: ChatMessageType = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: "Thank you for your message. I'm looking into this for you. Is there anything specific you'd like me to help with?",
          sender_name: 'AI Assistant',
          sender_type: 'ai',
          timestamp: new Date().toISOString(),
        };
        setLocalMessages((prev) => [...prev, aiMsg]);
      }, 1500);
    }
  };

  return (
    <div
      className={cn(
        'flex flex-col bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 overflow-hidden',
        fullPage
          ? 'h-full rounded-none'
          : 'w-96 h-[540px] rounded-2xl shadow-2xl'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full gradient-primary flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-white">
              {agentName}
            </h3>
            <div className="flex items-center gap-1.5">
              {isConnected ? (
                <>
                  <Wifi className="w-3 h-3 text-accent-500" />
                  <span className="text-xs text-accent-600 dark:text-accent-400">Online</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3 text-neutral-400" />
                  <span className="text-xs text-neutral-500">Reconnecting...</span>
                </>
              )}
            </div>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 dark:hover:text-neutral-300 dark:hover:bg-neutral-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {isTyping && (
          <div className="flex items-center gap-2 text-sm text-neutral-500">
            <div className="flex gap-1">
              <span className="w-2 h-2 rounded-full bg-neutral-400 animate-pulse-soft" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-neutral-400 animate-pulse-soft" style={{ animationDelay: '200ms' }} />
              <span className="w-2 h-2 rounded-full bg-neutral-400 animate-pulse-soft" style={{ animationDelay: '400ms' }} />
            </div>
            <span>{agentName} is typing...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={!isConnected} />
    </div>
  );
}
