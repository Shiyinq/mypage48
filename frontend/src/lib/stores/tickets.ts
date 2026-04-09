import { writable, get } from 'svelte/store';
import { ticketsApi } from '$lib/apis/tickets';
import { logger } from '$lib/utils/logger';
import { CACHE_EXPIRATION_MS, isCacheExpired } from '$lib/utils/cache';
import type { Ticket, PaginationMeta, TicketFilters } from '$lib/types';

interface TicketsState {
	list: Ticket[];
	pagination: PaginationMeta;
	filters: TicketFilters;
	defaultCache: { list: Ticket[]; pagination: PaginationMeta; lastUpdated: number } | null;
	titlesCache: string[] | null;
	lastUpdated: number;
	error: string | null;
}

export const isTicketsLoading = writable(false);

function createTicketsStore() {
	const initialState: TicketsState = {
		list: [],
		pagination: {
			current_page: 1,
			last_page: 1,
			total_data: 0,
			per_page: 20,
			next_page: null
		},
		filters: {},
		defaultCache: null,
		titlesCache: null,
		lastUpdated: 0,
		error: null
	};

	const { subscribe, set, update } = writable<TicketsState>(initialState);

	return {
		subscribe,
		update,
		load: async (page = 1, filters: TicketFilters = {}) => {
			const state = get({ subscribe });
			const now = Date.now();
			const isDefaultFilter = Object.keys(filters).length === 0;

			// Optimistic Check for Page 1 with no filters
			if (page === 1 && isDefaultFilter && state.defaultCache) {
				if (!isCacheExpired(state.defaultCache.lastUpdated)) {
					update((s) => ({
						...s,
						list: s.defaultCache!.list,
						pagination: s.defaultCache!.pagination,
						filters,
						error: null
					}));
					return;
				}
			}

			// Don't reload if we have data and it's fresh (and filters match)
			// Simplification: only rely on explicit load call triggering fetch unless cached above
			// But we need to update filters in state
			update((s) => ({
				...s,
				filters,
				error: null,
				list: s.list // Keep old list instead of clearing to avoid UI flickering
			}));
			isTicketsLoading.set(true);

			try {
				// Clean filters
				const cleanFilters = Object.fromEntries(
					Object.entries(filters).filter(([, v]) => v !== null && v !== undefined && v !== '')
				);

				const res = await ticketsApi.getMyTickets(page, 20, cleanFilters);

				update((s) => {
					// Filter out duplicates based on _id
					const newItems = res.data.filter(
						(newItem) => !s.list.some((existingItem) => existingItem._id === newItem._id)
					);
					const newState = {
						...s,
						list: page === 1 ? res.data : [...s.list, ...newItems],
						pagination: res.meta,
						lastUpdated: now,
						error: null
					};

					// Update default cache if applicable
					if (page === 1 && isDefaultFilter) {
						newState.defaultCache = {
							list: res.data,
							pagination: res.meta,
							lastUpdated: now
						};
					}

					return newState;
				});
			} catch (e) {
				logger.error('Failed to load tickets', e, { context: 'TicketsStore' });
				update((s) => ({ ...s, error: 'Failed to load tickets' }));
				throw e;
			} finally {
				isTicketsLoading.set(false);
			}
		},
		deleteTicket: async (ticketId: string) => {
			// Optimistic delete
			const state = get({ subscribe });
			const oldList = state.list;
			const oldCache = state.defaultCache;

			update((s) => ({
				...s,
				list: s.list.filter((t) => t._id !== ticketId),
				pagination: {
					...s.pagination,
					total_data: Math.max(0, s.pagination.total_data - 1)
				}
			}));

			try {
				await ticketsApi.deleteTicket(ticketId);
				// If success, maybe we should invalidate cache to be safe or keep optimistic
				// Just let it be.
			} catch (e) {
				// Revert
				update((s) => ({ ...s, list: oldList, defaultCache: oldCache }));
				logger.error('Failed to delete ticket', e);
				throw e;
			}
		},

		create: async (payload: Partial<Ticket>) => {
			isTicketsLoading.set(true);
			try {
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
						: null,
					pagination: {
						...s.pagination,
						total_data: s.pagination.total_data + 1
					}
				}));
				return newTicket;
			} catch (e) {
				update((s) => ({ ...s, error: 'Failed to create ticket' }));
				throw e;
			} finally {
				isTicketsLoading.set(false);
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
				const updated = await ticketsApi.updateTicket(ticketId, { notes: note });
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

		reset: () => {
			set(initialState);
			isTicketsLoading.set(false);
		}
	};
}

export const ticketsStore = createTicketsStore();

// Derived stores for backward compatibility
export const tickets = {
	subscribe: (cb: (val: Ticket[]) => void) => ticketsStore.subscribe((val) => cb(val.list))
};
export const ticketsPagination = {
	subscribe: (cb: (val: PaginationMeta) => void) =>
		ticketsStore.subscribe((val) => cb(val.pagination))
};
export const ticketsFilters = {
	subscribe: (cb: (val: TicketFilters) => void) => ticketsStore.subscribe((val) => cb(val.filters))
};
export const ticketsLoading = isTicketsLoading; // Alias
export const ticketsError = {
	subscribe: (cb: (val: string | null) => void) => ticketsStore.subscribe((val) => cb(val.error))
};
