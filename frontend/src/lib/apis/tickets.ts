import { client } from './client';
import type { Ticket, TicketPaginationResponse } from '../types';

export const ticketsApi = {
	createTicket: async (ticket: Partial<Ticket>) => {
		return await client<Ticket>('/theater/tickets', {
			method: 'POST',
			body: ticket
		});
	},

	getMyTickets: async (page = 1, limit = 20) => {
		return await client<TicketPaginationResponse>(`/theater/tickets?page=${page}&limit=${limit}`, {
			method: 'GET'
		});
	},

	getTicket: async (ticketId: string) => {
		return await client<Ticket>(`/theater/tickets/${ticketId}`, {
			method: 'GET'
		});
	},

	updateTicket: async (ticketId: string, ticket: Partial<Ticket>) => {
		return await client<Ticket>(`/theater/tickets/${ticketId}`, {
			method: 'PUT',
			body: ticket
		});
	},

	deleteTicket: async (ticketId: string) => {
		return await client<void>(`/theater/tickets/${ticketId}`, {
			method: 'DELETE'
		});
	}
};
