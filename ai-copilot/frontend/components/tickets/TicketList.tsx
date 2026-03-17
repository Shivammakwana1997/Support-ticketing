'use client';

import { useState } from 'react';
import { Search, Filter, Plus, SortAsc } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import { EmptyState } from '@/components/ui/EmptyState';
import { Spinner } from '@/components/ui/Spinner';
import { TicketCard } from './TicketCard';
import type { Ticket, TicketStatus, Priority } from '@/types/ticket';

interface TicketListProps {
  tickets: Ticket[];
  isLoading?: boolean;
  onTicketClick?: (ticket: Ticket) => void;
  onCreateTicket?: () => void;
  onFilterChange?: (filters: { status?: TicketStatus; priority?: Priority; search?: string }) => void;
  page?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
}

export function TicketList({
  tickets,
  isLoading,
  onTicketClick,
  onCreateTicket,
  onFilterChange,
  page = 1,
  totalPages = 1,
  onPageChange,
}: TicketListProps) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    onFilterChange?.({ search: e.target.value, status: statusFilter as TicketStatus, priority: priorityFilter as Priority });
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
    onFilterChange?.({ status: e.target.value as TicketStatus, priority: priorityFilter as Priority, search });
  };

  const handlePriorityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPriorityFilter(e.target.value);
    onFilterChange?.({ priority: e.target.value as Priority, status: statusFilter as TicketStatus, search });
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
          <input
            type="text"
            value={search}
            onChange={handleSearchChange}
            placeholder="Search tickets..."
            className="w-full h-10 pl-9 pr-3 rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 input-focus"
          />
        </div>
        <div className="flex items-center gap-3">
          <Select
            options={[
              { value: '', label: 'All Status' },
              { value: 'open', label: 'Open' },
              { value: 'pending', label: 'Pending' },
              { value: 'resolved', label: 'Resolved' },
              { value: 'closed', label: 'Closed' },
            ]}
            value={statusFilter}
            onChange={handleStatusChange}
          />
          <Select
            options={[
              { value: '', label: 'All Priority' },
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
              { value: 'urgent', label: 'Urgent' },
            ]}
            value={priorityFilter}
            onChange={handlePriorityChange}
          />
          {onCreateTicket && (
            <Button onClick={onCreateTicket} leftIcon={<Plus className="w-4 h-4" />}>
              New Ticket
            </Button>
          )}
        </div>
      </div>

      {/* Ticket List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : tickets.length === 0 ? (
        <EmptyState
          icon={<Filter className="w-8 h-8" />}
          title="No tickets found"
          description="Try adjusting your filters or create a new ticket."
          actionLabel={onCreateTicket ? 'Create Ticket' : undefined}
          onAction={onCreateTicket}
        />
      ) : (
        <div className="space-y-3">
          {tickets.map((ticket) => (
            <TicketCard
              key={ticket.id}
              ticket={ticket}
              onClick={() => onTicketClick?.(ticket)}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4">
          <p className="text-sm text-neutral-500">
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(page - 1)}
              disabled={page <= 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(page + 1)}
              disabled={page >= totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
