'use client';

import { useState, useRef, useCallback } from 'react';
import { Send, Paperclip } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Type a message...',
  maxLength = 2000,
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = message.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setMessage('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [message, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  };

  return (
    <div className="border-t border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 p-3 shrink-0">
      <div className="flex items-end gap-2">
        <button
          className="p-2 rounded-lg text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 dark:hover:text-neutral-300 dark:hover:bg-neutral-700 transition-colors shrink-0"
          title="Attach file"
        >
          <Paperclip className="w-5 h-5" />
        </button>
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            maxLength={maxLength}
            rows={1}
            className="w-full px-3 py-2 rounded-lg bg-neutral-100 dark:bg-neutral-700 text-sm text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20 resize-none disabled:opacity-50"
          />
          {message.length > maxLength * 0.8 && (
            <span className="absolute bottom-1 right-2 text-[10px] text-neutral-400">
              {message.length}/{maxLength}
            </span>
          )}
        </div>
        <button
          onClick={handleSend}
          disabled={!message.trim() || disabled}
          className={cn(
            'p-2 rounded-lg transition-colors shrink-0',
            message.trim() && !disabled
              ? 'bg-primary-600 text-white hover:bg-primary-700'
              : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-400'
          )}
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
