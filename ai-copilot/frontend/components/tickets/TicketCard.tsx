import { cn, formatRelativeTime } from '@/lib/utils';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/Avatar';
import { Clock, MessageSquare } from 'lucide-react';
import type { Ticket } from '@/types/ticket';

interface TicketCardProps {
  ticket: Ticket;
  onClick?: () => void;
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

export function TicketCard({ ticket, onClick }: TicketCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'p-4 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl transition-all duration-150',
        onClick && 'cursor-pointer hover:shadow-md hover:border-primary-200 dark:hover:border-primary-800'
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5">
            <Badge variant={statusVariant[ticket.status] || 'gray'} dot>
              {ticket.status}
            </Badge>
            <Badge variant={priorityVariant[ticket.priority] || 'gray'}>
              {ticket.priority}
            </Badge>
            {ticket.channel && (
              <span className="text-xs text-neutral-400 capitalize">{ticket.channel}</span>
            )}
          </div>
          <h3 className="text-sm font-semibold text-neutral-900 dark:text-white truncate">
            {ticket.subject}
          </h3>
          {ticket.description && (
            <p className="text-sm text-neutral-500 dark:text-neutral-400 truncate mt-0.5">
              {ticket.description}
            </p>
          )}
          <div className="flex items-center gap-4 mt-3 text-xs text-neutral-400">
            {ticket.customer && (
              <div className="flex items-center gap-1.5">
                <Avatar name={ticket.customer.name} size="sm" />
                <span>{ticket.customer.name}</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              <span>{formatRelativeTime(ticket.created_at)}</span>
            </div>
          </div>
        </div>
        {ticket.assigned_agent && (
          <div className="flex items-center gap-2 shrink-0">
            <Avatar
              name={ticket.assigned_agent.user?.name || 'Agent'}
              size="sm"
              status={ticket.assigned_agent.status === 'available' ? 'online' : 'offline'}
            />
          </div>
        )}
      </div>
      {ticket.tags && ticket.tags.length > 0 && (
        <div className="flex items-center gap-1.5 mt-3 flex-wrap">
          {ticket.tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
