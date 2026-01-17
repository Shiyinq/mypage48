import { client } from './client';
import type { EventPaginationResponse, CalendarEvent } from '$lib/types';

export const events = {
	getEvents: async (page = 1, limit = 20) => {
		return await client<EventPaginationResponse>(`/events/?page=${page}&limit=${limit}`);
	},
	getCurrentEvents: async (page = 1, limit = 20) => {
		return await client<EventPaginationResponse>(`/events/current?page=${page}&limit=${limit}`);
	},
	getCalendarEvents: async (year: number, month: number) => {
		return await client<CalendarEvent[]>(`/events/calendar?year=${year}&month=${month}`);
	}
};
