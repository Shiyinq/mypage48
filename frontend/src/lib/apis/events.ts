import { client } from './client';
import type { EventPaginationResponse, CalendarEvent } from '$lib/types';

export const events = {
	getEvents: async (page = 1, limit = 20, startDate?: string, endDate?: string) => {
		const query = new URLSearchParams({
			page: page.toString(),
			limit: limit.toString()
		});
		if (startDate) query.append('start_date', startDate);
		if (endDate) query.append('end_date', endDate);

		return await client<EventPaginationResponse>(`/events?${query.toString()}`);
	},
	getCurrentEvents: async (page = 1, limit = 20) => {
		return await client<EventPaginationResponse>(`/events/current?page=${page}&limit=${limit}`);
	},
	getCalendarEvents: async (year: number, month: number) => {
		return await client<CalendarEvent[]>(`/events/calendar?year=${year}&month=${month}`);
	}
};
