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
	loading: boolean;
	error: string | null;
}

function createTicketsStore() {
	const initialState: TicketsState = {
		list: [],
		pagination: { page: 0, hasMore: true },
		filters: {},
		defaultCache: null,
		titlesCache: null,
		lastUpdated: 0,
		loading: false,
		error: null
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
						filters: {},
						loading: false,
						error: null
					}));
					return;
				}
			}

			// Don't set loading true if we are just loading more pages to avoid flickering whole list
			// But for initial load (page 1) we might want it.
			// Let's set loading true generally, the UI can decide how to use it.
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const res = await ticketsApi.getMyTickets(page, 20, filters);
				const now = Date.now();

				update((s) => {
					const newList = page === 1 ? res.data : [...s.list, ...res.data];
					const newPagination = {
						page,
						hasMore: res.meta.current_page < res.meta.last_page
					};

					const newState: TicketsState = {
						...s,
						list: newList,
						pagination: newPagination,
						filters,
						lastUpdated: now,
						loading: false,
						error: null
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
				update((s) => ({ ...s, loading: false, error: 'Failed to load tickets' }));
				throw e;
			}
		},
		deleteTicket: async (ticketId: string) => {
			update((s) => ({ ...s, loading: true }));
			try {
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
						lastUpdated: now,
						loading: false
					};
				});
			} catch (e) {
				update((s) => ({ ...s, loading: false, error: 'Failed to delete ticket' }));
				throw e;
			}
		},

		create: async (payload: Partial<Ticket>) => {
			update((s) => ({ ...s, loading: true }));
			try {
				const newTicket = await ticketsApi.createTicket(payload);
				const now = Date.now();
				update((s) => ({
					...s,
					list: [newTicket, ...s.list],
					lastUpdated: now,
					loading: false,
					defaultCache: s.defaultCache
						? {
							...s.defaultCache,
							list: [newTicket, ...s.defaultCache.list],
							lastUpdated: now
						}
						: null
				}));
				return newTicket;
			} catch (e) {
				update((s) => ({ ...s, loading: false, error: 'Failed to create ticket' }));
				throw e;
			}
		},

		updateTicket: async (ticketId: string, payload: Partial<Ticket>) => {
			// Optimistically not setting global loading for item update to avoid UI flicker
			// Or we could added a separate 'processingId' state if needed.
			// For now, let's keep it simple and just update data.
			try {
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
			} catch (e) {
				throw e;
			}
		},

		updateNote: async (ticketId: string, note: string) => {
			try {
				await ticketsApi.updateTicket(ticketId, { notes: note });
				const now = Date.now();
				update((s) => ({
					...s,
					list: s.list.map((t) => (t._id === ticketId ? { ...t, notes: note } : t)),
					lastUpdated: now,
					defaultCache: s.defaultCache
						? {
							...s.defaultCache,
							list: s.defaultCache.list.map((t) =>
								t._id === ticketId ? { ...t, notes: note } : t
							),
							lastUpdated: now
						}
						: null
				}));
			} catch (e) {
				throw e;
			}
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
export const ticketsLoading = {
	subscribe: (cb: (val: boolean) => void) => ticketsStore.subscribe((val) => cb(val.loading))
};
export const ticketsError = {
	subscribe: (cb: (val: string | null) => void) => ticketsStore.subscribe((val) => cb(val.error))
};
