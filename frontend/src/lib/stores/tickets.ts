import { writable, get } from 'svelte/store';
import type { Ticket, TicketFilters, PaginationState } from '$lib/types';
import { ticketsApi } from '$lib/apis/tickets';
import { logger } from '$lib/utils/logger';
import { CACHE_EXPIRATION_MS, isCacheExpired } from '$lib/utils/cache';

// Tickets Store Types
interface TicketsState {
	list: Ticket[];
	pagination: PaginationState;
	filters: TicketFilters;
	defaultCache: { list: Ticket[]; pagination: PaginationState; lastUpdated: number } | null;
	titlesCache: string[] | null;
	lastUpdated: number;
}



function createTicketsStore() {
	const initialState: TicketsState = {
		list: [],
		pagination: { page: 0, hasMore: true },
		filters: {},
		defaultCache: null,
		titlesCache: null,
		lastUpdated: 0
	};

	const { subscribe, set, update } = writable<TicketsState>(initialState);

	return {
		subscribe,
		set,
		update,
		load: async (page: number, filters: TicketFilters = {}) => {
			const state = get({ subscribe });
			const isDefaultLoad = Object.keys(filters).length === 0;

			// Optimistic Cache Check for Default Load (Page 1)
			if (page === 1 && isDefaultLoad && state.defaultCache) {
				if (!isCacheExpired(state.defaultCache.lastUpdated)) {
					update((s) => ({
						...s,
						list: state.defaultCache!.list,
						pagination: state.defaultCache!.pagination,
						filters: {}
					}));
					return;
				}
			}

			try {
				const res = await ticketsApi.getMyTickets(page, 20, filters);
				const now = Date.now();

				update((s) => {
					const newList = page === 1 ? res.data : [...s.list, ...res.data];
					const newPagination = {
						page,
						hasMore: res.meta.current_page < res.meta.last_page
					};

					const newState = {
						...s,
						list: newList,
						pagination: newPagination,
						filters,
						lastUpdated: now
					};

					if (isDefaultLoad) {
						newState.defaultCache = {
							list: newList,
							pagination: newPagination,
							lastUpdated: now
						};
					}

					return newState;
				});
			} catch (e) {
				logger.error('Failed to load tickets', e, { context: 'TicketsStore' });
				throw e;
			}
		},
		deleteTicket: async (ticketId: string) => {
			await ticketsApi.deleteTicket(ticketId);

			update((s) => {
				const newList = s.list.filter((t) => t._id !== ticketId && t.ticket_id !== ticketId);
				const now = Date.now();
				let newCache = s.defaultCache;
				if (newCache) {
					newCache = {
						...newCache,
						list: newCache.list.filter((t) => t._id !== ticketId && t.ticket_id !== ticketId),
						lastUpdated: now
					};
				}

				return {
					...s,
					list: newList,
					defaultCache: newCache,
					lastUpdated: now
				};
			});
		},

		create: async (payload: Partial<Ticket>) => {
			const newTicket = await ticketsApi.createTicket(payload);
			const now = Date.now();
			update((s) => ({
				...s,
				list: [newTicket, ...s.list],
				lastUpdated: now,
				defaultCache: s.defaultCache
					? {
						...s.defaultCache,
						list: [newTicket, ...s.defaultCache.list],
						lastUpdated: now
					}
					: null
			}));
			return newTicket;
		},

		updateTicket: async (ticketId: string, payload: Partial<Ticket>) => {
			const updated = await ticketsApi.updateTicket(ticketId, payload);
			const now = Date.now();
			update((s) => ({
				...s,
				list: s.list.map((t) => (t._id === ticketId ? updated : t)),
				lastUpdated: now,
				defaultCache: s.defaultCache
					? {
						...s.defaultCache,
						list: s.defaultCache.list.map((t) => (t._id === ticketId ? updated : t)),
						lastUpdated: now
					}
					: null
			}));
			return updated;
		},

		updateNote: async (ticketId: string, note: string) => {
			await ticketsApi.updateTicket(ticketId, { notes: note });
			const now = Date.now();
			update((s) => ({
				...s,
				list: s.list.map((t) => (t._id === ticketId ? { ...t, notes: note } : t)),
				lastUpdated: now,
				defaultCache: s.defaultCache
					? {
						...s.defaultCache,
						list: s.defaultCache.list.map((t) => (t._id === ticketId ? { ...t, notes: note } : t)),
						lastUpdated: now
					}
					: null
			}));
		},

		getAvailableTitles: async () => {
			const state = get({ subscribe });
			if (state.titlesCache) {
				return state.titlesCache;
			}
			const titles = await ticketsApi.getTicketTitles();
			update((s) => ({ ...s, titlesCache: titles }));
			return titles;
		},

		reset: () => set(initialState)
	};
}

export const ticketsStore = createTicketsStore();

// Derived stores for backward compatibility
export const tickets = {
	subscribe: (cb: (val: Ticket[]) => void) => ticketsStore.subscribe((val) => cb(val.list))
};
export const ticketsPagination = {
	subscribe: (cb: (val: PaginationState) => void) =>
		ticketsStore.subscribe((val) => cb(val.pagination))
};
export const ticketsFilters = {
	subscribe: (cb: (val: TicketFilters) => void) => ticketsStore.subscribe((val) => cb(val.filters))
};
