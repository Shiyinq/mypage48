import { writable, get } from 'svelte/store';
import { events } from '$lib/apis/events';
import type { Event, PaginationMeta } from '$lib/types';
import { isCacheExpired } from '$lib/utils/cache';
import { logger } from '$lib/utils/logger';

interface EventsState {
	upcoming: {
		list: Event[];
		error: string | null;
		lastUpdated: number;
	};
	history: {
		list: Event[];
		pagination: PaginationMeta;
		error: string | null;
		lastUpdated: number;
		// Cache specifically for page 1
		defaultCache: {
			list: Event[];
			pagination: PaginationMeta;
			lastUpdated: number;
		} | null;
	};
}

export const isUpcomingEventsLoading = writable(false);
export const isHistoryEventsLoading = writable(false);

function createEventsStore() {
	const initialState: EventsState = {
		upcoming: {
			list: [],
			error: null,
			lastUpdated: 0
		},
		history: {
			list: [],
			pagination: {
				current_page: 1,
				last_page: 1,
				total_data: 0,
				per_page: 20,
				next_page: null
			},
			error: null,
			lastUpdated: 0,
			defaultCache: null
		}
	};

	const { subscribe, set, update } = writable<EventsState>(initialState);

	return {
		subscribe,
		reset: () => {
			set(initialState);
			isUpcomingEventsLoading.set(false);
			isHistoryEventsLoading.set(false);
		},

		loadUpcoming: async (forceRefresh = false) => {
			const state = get({ subscribe });
			const now = Date.now();

			if (
				!forceRefresh &&
				state.upcoming.list.length > 0 &&
				!isCacheExpired(state.upcoming.lastUpdated)
			) {
				return;
			}

			update((s) => ({ ...s, upcoming: { ...s.upcoming, error: null } }));
			isUpcomingEventsLoading.set(true);

			try {
				const res = await events.getCurrentEvents(1, 100); // Fetch mostly all current events
				update((s) => ({
					...s,
					upcoming: {
						list: res.data,
						error: null,
						lastUpdated: now
					}
				}));
			} catch (e) {
				logger.error('Failed to load upcoming events', e);
				update((s) => ({
					...s,
					upcoming: { ...s.upcoming, error: 'Failed to load upcoming events' }
				}));
			} finally {
				isUpcomingEventsLoading.set(false);
			}
		},

		loadHistory: async (page = 1, forceRefresh = false) => {
			const state = get({ subscribe });
			const now = Date.now();

			// Optimistic Check for page 1
			if (page === 1 && !forceRefresh && state.history.defaultCache) {
				if (!isCacheExpired(state.history.defaultCache.lastUpdated)) {
					update((s) => ({
						...s,
						history: {
							...s.history,
							list: s.history.defaultCache!.list,
							pagination: s.history.defaultCache!.pagination,
							error: null
						}
					}));
					return;
				}
			}

			update((s) => ({ ...s, history: { ...s.history, error: null } }));
			isHistoryEventsLoading.set(true);

			try {
				const res = await events.getEvents(page, 20); // API defaults, matches UI limit

				update((s) => {
					const newState = {
						...s,
						history: {
							...s.history,
							list: res.data,
							pagination: res.meta,
							error: null,
							lastUpdated: now
						}
					};

					if (page === 1) {
						newState.history.defaultCache = {
							list: res.data,
							pagination: res.meta,
							lastUpdated: now
						};
					}

					return newState;
				});
			} catch (e) {
				logger.error('Failed to load event history', e);
				update((s) => ({
					...s,
					history: { ...s.history, error: 'Failed to load event history' }
				}));
			} finally {
				isHistoryEventsLoading.set(false);
			}
		}
	};
}

export const eventsStore = createEventsStore();

// Derived Stores
export const upcomingEvents = {
	subscribe: (cb: (val: Event[]) => void) => eventsStore.subscribe((val) => cb(val.upcoming.list))
};

export const upcomingLoading = isUpcomingEventsLoading; // Alias to new store

export const historyEvents = {
	subscribe: (cb: (val: Event[]) => void) => eventsStore.subscribe((val) => cb(val.history.list))
};

export const historyPagination = {
	subscribe: (cb: (val: PaginationMeta) => void) =>
		eventsStore.subscribe((val) => cb(val.history.pagination))
};

export const historyLoading = isHistoryEventsLoading; // Alias to new store

export const upcomingError = {
	subscribe: (cb: (val: string | null) => void) =>
		eventsStore.subscribe((val) => cb(val.upcoming.error))
};

export const historyError = {
	subscribe: (cb: (val: string | null) => void) =>
		eventsStore.subscribe((val) => cb(val.history.error))
};
