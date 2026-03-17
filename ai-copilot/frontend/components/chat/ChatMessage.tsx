import { cn, formatShortDate } from '@/lib/utils';
import { Avatar } from '@/components/ui/Avatar';
import { Bot, FileText } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '@/types/message';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <p className="text-xs text-neutral-500 bg-neutral-100 dark:bg-neutral-800 px-3 py-1 rounded-full">
          {message.content}
        </p>
      </div>
    );
  }

  return (
    <div className={cn('flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row')}>
      {/* Avatar */}
      {isUser ? (
        <Avatar name="You" size="sm" />
      ) : (
        <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center shrink-0">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}

      {/* Message content */}
      <div className={cn('flex flex-col max-w-[75%]', isUser ? 'items-end' : 'items-start')}>
        {/* Sender name */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-medium text-neutral-500">
            {isUser ? 'You' : message.sender_name || 'AI Assistant'}
          </span>
          <span className="text-xs text-neutral-400">
            {formatShortDate(message.timestamp)}
          </span>
        </div>

        {/* Bubble */}
        <div
          className={cn(
            'px-4 py-2.5 rounded-2xl text-sm leading-relaxed',
            isUser
              ? 'bg-primary-600 text-white rounded-tr-md'
              : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 rounded-tl-md'
          )}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.citations.map((citation, i) => (
              <div
                key={i}
                className="flex items-start gap-2 p-2 rounded-lg bg-primary-50 dark:bg-primary-900/20 text-xs"
              >
                <FileText className="w-3.5 h-3.5 text-primary-500 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-primary-700 dark:text-primary-400">
                    {citation.document_title}
                  </p>
                  <p className="text-primary-600/70 dark:text-primary-400/70 line-clamp-2 mt-0.5">
                    {citation.chunk_text}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
