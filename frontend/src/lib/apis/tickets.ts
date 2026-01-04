import { client } from './client';
import type { Ticket, TicketPaginationResponse } from '../types';

export const ticketsApi = {
	createTicket: async (ticket: Partial<Ticket>) => {
		return await client<Ticket>('/theater/tickets', {
			method: 'POST',
			body: ticket
		});
	},

	getMyTickets: async (page = 1, limit = 20, filters?: import('../types').TicketFilters) => {
		const query = new URLSearchParams({
			page: page.toString(),
			limit: limit.toString()
		});

		if (filters) {
			if (filters.title) query.append('title', filters.title);
			if (filters.hasTwoShot !== undefined)
				query.append('has_two_shot', filters.hasTwoShot.toString());
			if (filters.startDate) query.append('start_date', filters.startDate);
			if (filters.endDate) query.append('end_date', filters.endDate);
			if (filters.days && filters.days.length > 0) {
				filters.days.forEach((day) => query.append('days', day));
			}
		}

		return await client<TicketPaginationResponse>(`/theater/tickets?${query.toString()}`, {
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
	},

	getTicketTitles: async () => {
		return await client<string[]>('/theater/tickets/titles', {
			method: 'GET'
		});
	}
};
