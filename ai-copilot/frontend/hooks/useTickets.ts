'use client';

import { useState, useCallback, useEffect } from 'react';
import type { Ticket, TicketFilters, CreateTicketRequest, UpdateTicketRequest } from '@/types/ticket';
import type { PaginatedResponse } from '@/types';
import * as ticketService from '@/services/tickets';

interface UseTicketsReturn {
  tickets: Ticket[];
  total: number;
  totalPages: number;
  page: number;
  isLoading: boolean;
  error: string | null;
  filters: TicketFilters;
  setFilters: (filters: TicketFilters) => void;
  setPage: (page: number) => void;
  createTicket: (data: CreateTicketRequest) => Promise<Ticket>;
  updateTicket: (id: string, data: UpdateTicketRequest) => Promise<Ticket>;
  refetch: () => Promise<void>;
}

export function useTickets(initialFilters?: TicketFilters): UseTicketsReturn {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(initialFilters?.page || 1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<TicketFilters>(initialFilters || {});

  const fetchTickets = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response: PaginatedResponse<Ticket> = await ticketService.getTickets({
        ...filters,
        page,
      });
      setTickets(response.items);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tickets');
    } finally {
      setIsLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const createTicket = useCallback(async (data: CreateTicketRequest): Promise<Ticket> => {
    const ticket = await ticketService.createTicket(data);
    await fetchTickets();
    return ticket;
  }, [fetchTickets]);

  const updateTicket = useCallback(async (id: string, data: UpdateTicketRequest): Promise<Ticket> => {
    const ticket = await ticketService.updateTicket(id, data);
    setTickets((prev) => prev.map((t) => (t.id === id ? ticket : t)));
    return ticket;
  }, []);

  return {
    tickets,
    total,
    totalPages,
    page,
    isLoading,
    error,
    filters,
    setFilters,
    setPage,
    createTicket,
    updateTicket,
    refetch: fetchTickets,
  };
}
