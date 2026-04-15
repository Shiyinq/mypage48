import { ticketsApi } from '$lib/apis/tickets';
import { logger } from '$lib/utils/logger';
import { isCacheExpired } from '$lib/utils/cache';
import type { Ticket, PaginationMeta, TicketFilters } from '$lib/types';

/**
 * Tickets store - migrated to Svelte 5 Shared Rune State.
 * Manages user ticket inventory, filtering, and CRUD operations.
 */

interface TicketsState {
	list: Ticket[];
	pagination: PaginationMeta;
	filters: TicketFilters;
	defaultCache: { list: Ticket[]; pagination: PaginationMeta; lastUpdated: number } | null;
	titlesCache: string[] | null;
	lastUpdated: number;
	error: string | null;
	isLoading: boolean;
}

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
	error: null,
	isLoading: false
};

const state = $state<TicketsState>(initialState);

function createTicketsStore() {
	return {
		get list() {
			return state.list;
		},
		get pagination() {
			return state.pagination;
		},
		get filters() {
			return state.filters;
		},
		get error() {
			return state.error;
		},
		get isLoading() {
			return state.isLoading;
		},
		get lastUpdated() {
			return state.lastUpdated;
		},

		load: async (page = 1, filters: TicketFilters = {}) => {
			const nowVal = Date.now();
			const isDefaultFilter = Object.keys(filters).length === 0;

			if (
				page === 1 &&
				isDefaultFilter &&
				state.defaultCache &&
				!isCacheExpired(state.defaultCache.lastUpdated)
			) {
				state.list = state.defaultCache.list;
				state.pagination = state.defaultCache.pagination;
				state.filters = filters;
				state.error = null;
				return;
			}

			state.filters = filters;
			state.error = null;
			state.isLoading = true;

			try {
				const cleanFilters = Object.fromEntries(
					Object.entries(filters).filter(([, v]) => v !== null && v !== undefined && v !== '')
				);

				const res = await ticketsApi.getMyTickets(page, 20, cleanFilters);

				const newItems = res.data.filter(
					(newItem) => !state.list.some((existingItem) => existingItem._id === newItem._id)
				);

				state.list = page === 1 ? res.data : [...state.list, ...newItems];
				state.pagination = res.meta;
				state.lastUpdated = nowVal;
				state.error = null;

				if (page === 1 && isDefaultFilter) {
					state.defaultCache = {
						list: res.data,
						pagination: res.meta,
						lastUpdated: nowVal
					};
				}
			} catch (e) {
				logger.error('Failed to load tickets', e, { context: 'TicketsStore' });
				state.error = 'Failed to load tickets';
				throw e;
			} finally {
				state.isLoading = false;
			}
		},

		deleteTicket: async (ticketId: string) => {
			const oldList = [...state.list];
			const oldCache = state.defaultCache ? { ...state.defaultCache } : null;

			state.list = state.list.filter((t) => t._id !== ticketId);
			state.pagination.total_data = Math.max(0, state.pagination.total_data - 1);

			// Update default cache too to reflect state immediately
			if (state.defaultCache) {
				state.defaultCache.list = state.defaultCache.list.filter((t) => t._id !== ticketId);
				state.defaultCache.pagination.total_data = state.pagination.total_data;
			}

			try {
				await ticketsApi.deleteTicket(ticketId);
			} catch (e) {
				state.list = oldList;
				state.defaultCache = oldCache;
				logger.error('Failed to delete ticket', e);
				throw e;
			}
		},

		create: async (payload: Partial<Ticket>) => {
			state.isLoading = true;
			try {
				const newTicket = await ticketsApi.createTicket(payload);
				const nowVal = Date.now();
				state.list = [newTicket, ...state.list];
				state.lastUpdated = nowVal;
				if (state.defaultCache) {
					state.defaultCache = {
						...state.defaultCache,
						list: [newTicket, ...state.defaultCache.list],
						lastUpdated: nowVal
					};
				}
				state.pagination.total_data += 1;
				return newTicket;
			} catch (e) {
				state.error = 'Failed to create ticket';
				throw e;
			} finally {
				state.isLoading = false;
			}
		},

		updateTicket: async (ticketId: string, payload: Partial<Ticket>) => {
			const updated = await ticketsApi.updateTicket(ticketId, payload);
			const nowVal = Date.now();
			state.list = state.list.map((t) => (t._id === ticketId ? updated : t));
			state.lastUpdated = nowVal;
			if (state.defaultCache) {
				state.defaultCache.list = state.defaultCache.list.map((t) =>
					t._id === ticketId ? updated : t
				);
				state.defaultCache.lastUpdated = nowVal;
			}
			return updated;
		},

		updateNote: async (ticketId: string, note: string) => {
			const updated = await ticketsApi.updateTicket(ticketId, { notes: note });
			const nowVal = Date.now();
			state.list = state.list.map((t) => (t._id === ticketId ? updated : t));
			state.lastUpdated = nowVal;
			if (state.defaultCache) {
				state.defaultCache.list = state.defaultCache.list.map((t) =>
					t._id === ticketId ? updated : t
				);
				state.defaultCache.lastUpdated = nowVal;
			}
		},

		getAvailableTitles: async () => {
			if (state.titlesCache) return state.titlesCache;
			const titles = await ticketsApi.getTicketTitles();
			state.titlesCache = titles;
			return titles;
		},

		reset: () => {
			Object.assign(state, initialState);
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (
			fn: (val: {
				list: Ticket[];
				pagination: PaginationMeta;
				filters: TicketFilters;
				error: string | null;
			}) => void
		) => {
			fn({
				list: state.list,
				pagination: state.pagination,
				filters: state.filters,
				error: state.error
			});
			$effect.root(() => {
				$effect(() => {
					fn({
						list: state.list,
						pagination: state.pagination,
						filters: state.filters,
						error: state.error
					});
				});
			});
			return () => {};
		}
	};
}

export const ticketsStore = createTicketsStore();

// Compatibility Aliases
export const tickets = {
	get value() {
		return state.list;
	},
	subscribe: (cb: (val: Ticket[]) => void) => {
		cb(state.list);
		$effect.root(() => {
			$effect(() => cb(state.list));
		});
		return () => {};
	}
};

export const ticketsPagination = {
	get value() {
		return state.pagination;
	},
	subscribe: (cb: (val: PaginationMeta) => void) => {
		cb(state.pagination);
		$effect.root(() => {
			$effect(() => cb(state.pagination));
		});
		return () => {};
	}
};

export const ticketsFilters = {
	get value() {
		return state.filters;
	},
	subscribe: (cb: (val: TicketFilters) => void) => {
		cb(state.filters);
		$effect.root(() => {
			$effect(() => cb(state.filters));
		});
		return () => {};
	}
};

export const ticketsLoading = {
	get value() {
		return state.isLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(state.isLoading);
		$effect.root(() => {
			$effect(() => fn(state.isLoading));
		});
		return () => {};
	}
};

export const isTicketsLoading = ticketsLoading;

export const ticketsError = {
	get value() {
		return state.error;
	},
	subscribe: (cb: (val: string | null) => void) => {
		cb(state.error);
		$effect.root(() => {
			$effect(() => cb(state.error));
		});
		return () => {};
	}
};
