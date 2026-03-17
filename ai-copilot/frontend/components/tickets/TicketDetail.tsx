'use client';

import { useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/Avatar';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { ChatMessage } from '@/components/chat/ChatMessage';
import { ChatInput } from '@/components/chat/ChatInput';
import {
  Clock,
  AlertTriangle,
  User,
  Tag,
  Brain,
  ArrowRight,
} from 'lucide-react';
import { formatDate, formatRelativeTime } from '@/lib/utils';
import type { Ticket, TicketStatus, Priority } from '@/types/ticket';
import type { Message, ChatMessage as ChatMessageType } from '@/types/message';

interface TicketDetailProps {
  ticket: Ticket;
  messages?: Message[];
  aiSummary?: { summary: string; key_points: string[]; sentiment: string; suggested_actions: string[] };
  onStatusChange?: (status: TicketStatus) => void;
  onPriorityChange?: (priority: Priority) => void;
  onAssign?: (agentId: string) => void;
  onReply?: (content: string) => void;
}

const statusVariant: Record<string, 'green' | 'yellow' | 'blue' | 'gray'> = {
  open: 'green',
  pending: 'yellow',
  resolved: 'blue',
  closed: 'gray',
};

const priorityVariant: Record<string, 'gray' | 'blue' | 'yellow' | 'red'> = {
  low: 'gray',
  medium: 'blue',
  high: 'yellow',
  urgent: 'red',
};

export function TicketDetail({
  ticket,
  messages = [],
  aiSummary,
  onStatusChange,
  onPriorityChange,
  onReply,
}: TicketDetailProps) {
  const chatMessages: ChatMessageType[] = messages.map((m) => ({
    id: m.id,
    role: m.sender_type === 'customer' ? 'user' : 'assistant',
    content: m.content,
    sender_name: m.sender_name,
    sender_type: m.sender_type,
    citations: m.citations,
    timestamp: m.created_at,
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main content */}
      <div className="lg:col-span-2 space-y-6">
        {/* Header */}
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Badge variant={statusVariant[ticket.status] || 'gray'} dot>
              {ticket.status}
            </Badge>
            <Badge variant={priorityVariant[ticket.priority] || 'gray'}>
              {ticket.priority}
            </Badge>
          </div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">
            {ticket.subject}
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Created {formatDate(ticket.created_at)}
          </p>
        </div>

        {/* AI Summary */}
        {aiSummary && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-primary-500" />
                <h3 className="text-sm font-semibold text-neutral-900 dark:text-white">
                  AI Summary
                </h3>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-neutral-700 dark:text-neutral-300 mb-3">
                {aiSummary.summary}
              </p>
              {aiSummary.key_points.length > 0 && (
                <div className="mb-3">
                  <h4 className="text-xs font-semibold text-neutral-500 uppercase mb-1.5">Key Points</h4>
                  <ul className="space-y-1">
                    {aiSummary.key_points.map((point, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                        <ArrowRight className="w-3.5 h-3.5 text-primary-500 mt-0.5 shrink-0" />
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {aiSummary.suggested_actions.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-neutral-500 uppercase mb-1.5">Suggested Actions</h4>
                  <div className="flex flex-wrap gap-2">
                    {aiSummary.suggested_actions.map((action, i) => (
                      <Badge key={i} variant="blue">{action}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Messages thread */}
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-white">
              Conversation
            </h3>
          </CardHeader>
          <CardContent className="space-y-4 max-h-[500px] overflow-y-auto scrollbar-thin">
            {chatMessages.length > 0 ? (
              chatMessages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))
            ) : (
              <p className="text-sm text-neutral-500 text-center py-8">
                No messages yet
              </p>
            )}
          </CardContent>
        </Card>

        {/* Reply */}
        {onReply && (
          <Card>
            <ChatInput onSend={onReply} placeholder="Type your reply..." />
          </Card>
        )}
      </div>

      {/* Sidebar */}
      <div className="space-y-6">
        {/* Customer info */}
        {ticket.customer && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-neutral-400" />
                <h3 className="text-sm font-semibold text-neutral-900 dark:text-white">Customer</h3>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3">
                <Avatar name={ticket.customer.name} size="md" />
                <div>
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">
                    {ticket.customer.name}
                  </p>
                  <p className="text-xs text-neutral-500">{ticket.customer.email}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* SLA */}
        {ticket.sla_deadline && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-warning-500" />
                <h3 className="text-sm font-semibold text-neutral-900 dark:text-white">SLA Timer</h3>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm font-medium text-neutral-900 dark:text-white">
                Due {formatRelativeTime(ticket.sla_deadline)}
              </p>
              <p className="text-xs text-neutral-500">{formatDate(ticket.sla_deadline)}</p>
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-white">Actions</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            {onStatusChange && (
              <Select
                label="Status"
                value={ticket.status}
                onChange={(e) => onStatusChange(e.target.value as TicketStatus)}
                options={[
                  { value: 'open', label: 'Open' },
                  { value: 'pending', label: 'Pending' },
                  { value: 'resolved', label: 'Resolved' },
                  { value: 'closed', label: 'Closed' },
                ]}
              />
            )}
            {onPriorityChange && (
              <Select
                label="Priority"
                value={ticket.priority}
                onChange={(e) => onPriorityChange(e.target.value as Priority)}
                options={[
                  { value: 'low', label: 'Low' },
                  { value: 'medium', label: 'Medium' },
                  { value: 'high', label: 'High' },
                  { value: 'urgent', label: 'Urgent' },
                ]}
              />
            )}
          </CardContent>
        </Card>

        {/* Tags */}
        {ticket.tags && ticket.tags.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Tag className="w-4 h-4 text-neutral-400" />
                <h3 className="text-sm font-semibold text-neutral-900 dark:text-white">Tags</h3>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {ticket.tags.map((tag) => (
                  <Badge key={tag} variant="gray">{tag}</Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
