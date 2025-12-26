import { client } from './client';
import type { Ticket } from '../types';

export const theater = {
    createTicket: async (ticket: Partial<Ticket>) => {
        return await client<Ticket>('/theater/tickets', {
            method: 'POST',
            body: ticket,
        });
    },

    getMyTickets: async () => {
        return await client<Ticket[]>('/theater/tickets', {
            method: 'GET',
        });
    },

    getTicket: async (ticketId: string) => {
        return await client<Ticket>(`/theater/tickets/${ticketId}`, {
            method: 'GET',
        });
    },

    updateTicket: async (ticketId: string, ticket: Partial<Ticket>) => {
        return await client<Ticket>(`/theater/tickets/${ticketId}`, {
            method: 'PUT',
            body: ticket,
        });
    },

    deleteTicket: async (ticketId: string) => {
        return await client<void>(`/theater/tickets/${ticketId}`, {
            method: 'DELETE',
        });
    },
};
