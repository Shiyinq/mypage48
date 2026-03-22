import { writable, get } from 'svelte/store';
import { events } from '$lib/apis/events';
import type { Event, CalendarEvent, PaginationMeta } from '$lib/types';
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
	calendar: {
		list: CalendarEvent[];
		error: string | null;
		lastUpdated: number;
		year: number;
		month: number;
		cache: Record<string, { list: CalendarEvent[]; lastUpdated: number }>;
	};
}

export const isUpcomingEventsLoading = writable(false);
export const isHistoryEventsLoading = writable(false);
export const isCalendarEventsLoading = writable(false);

// Maps legacy image-based event types (formerly stored in "label") to modern "type" fields.
// In newer data, "label" is used for performer indicators (e.g., JKT48, TRAINEE).
const legacyMapping: Record<string, string> = {
	'/images/icon.cat2.png': 'EVENT',
	'/images/icon.cat9.png': 'EVENT',
	'/images/icon.cat1.png': 'SHOW',
	'/images/icon.cat17.png': 'SHOW',
	'/images/icon.cat19.png': 'SHOW',
	'/images/icon.cat13.png': 'SHOW',
	'/images/icon.cat11.png': 'SHOW',
	'/images/icon.cat12.png': 'SHOW',
	'/images/icon.cat14.png': 'SHOW',
	'/images/icon.cat15.png': 'SHOW',
	'/images/icon.cat18.png': 'SHOW',
	'/images/icon.cat20.png': 'SHOW',
	'/images/icon.cat21.png': 'SHOW',
	'/images/icon.cat23.png': 'SHOW',
	'/images/icon.cat8.png': 'GENERAL',
	'/images/icon.cat3.png': 'GENERAL',
	'/images/icon.cat4.png': 'GENERAL',
	'/images/icon.cat99.png': 'GENERAL',
	'/images/icon.cat5.png': 'BIRTHDAY',
	'/images/icon.cat10.png': 'BIRTHDAY',
	'/images/icon.cat7.png': 'BIRTHDAY'
};

function translateLegacyEvent<T extends Event | CalendarEvent>(event: T): T {
	const labelLower = event.label?.toLowerCase().trim() || '';
	if (legacyMapping[labelLower]) {
		const mappedType = legacyMapping[labelLower];
		const updatedEvent = {
			...event,
			type: mappedType,
			label: undefined
		};

		// Ensure isBirthday is set for legacy birthday icons
		if (mappedType === 'BIRTHDAY') {
			if ('isBirthday' in updatedEvent) {
				(updatedEvent as CalendarEvent).isBirthday = true;
			}
		}

		return updatedEvent as T;
	}
	return event;
}

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
		},
		calendar: {
			list: [],
			error: null,
			lastUpdated: 0,
			year: 0,
			month: 0,
			cache: {}
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
				const translatedData = res.data.map(translateLegacyEvent);
				update((s) => ({
					...s,
					upcoming: {
						list: translatedData,
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

			// Temporarily disabled cache to avoid stale data during migration
			/* if (page === 1 && !forceRefresh && state.history.defaultCache) {
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
			} */

			update((s) => ({ ...s, history: { ...s.history, error: null } }));
			isHistoryEventsLoading.set(true);

			try {
				const res = await events.getEvents(page, 20); // API defaults, matches UI limit
				const translatedData = res.data.map(translateLegacyEvent);

				update((s) => {
					const newState = {
						...s,
						history: {
							...s.history,
							list: translatedData,
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
		},

		loadCalendar: async (year: number, month: number, forceRefresh = false) => {
			const state = get({ subscribe });
			const now = Date.now();
			const cacheKey = `${year}-${month}`;

			// 1. Check current view match (fastest)
			if (
				!forceRefresh &&
				state.calendar.year === year &&
				state.calendar.month === month &&
				state.calendar.list.length > 0 &&
				!isCacheExpired(state.calendar.lastUpdated)
			) {
				return;
			}

			// 2. Check cache for this specific month
			if (
				!forceRefresh &&
				state.calendar.cache[cacheKey] &&
				!isCacheExpired(state.calendar.cache[cacheKey].lastUpdated)
			) {
				const cached = state.calendar.cache[cacheKey];
				update((s) => ({
					...s,
					calendar: {
						...s.calendar,
						list: cached.list,
						error: null,
						lastUpdated: cached.lastUpdated,
						year,
						month
					}
				}));
				return;
			}

			// Clear the list if the requested month/year is different to avoid stale events
			const shouldClear = state.calendar.year !== year || state.calendar.month !== month;

			update((s) => ({
				...s,
				calendar: {
					...s.calendar,
					error: null,
					list: shouldClear ? [] : s.calendar.list,
					year,
					month
				}
			}));

			isCalendarEventsLoading.set(true);

			try {
				const res = await events.getCalendarEvents(year, month);
				const translatedData = res.map(translateLegacyEvent);

				// Check if the current state still matches the request
				// This prevents race conditions where a previous request finishes after a new one started
				const currentState = get({ subscribe });
				if (currentState.calendar.year !== year || currentState.calendar.month !== month) {
					return;
				}

				update((s) => ({
					...s,
					calendar: {
						...s.calendar,
						list: translatedData,
						error: null,
						lastUpdated: now,
						year,
						month,
						cache: {
							...s.calendar.cache,
							[cacheKey]: {
								list: translatedData,
								lastUpdated: now
							}
						}
					}
				}));
			} catch (e) {
				logger.error('Failed to load calendar events', e);
				update((s) => ({
					...s,
					calendar: { ...s.calendar, error: 'Failed to load calendar events' }
				}));
			} finally {
				isCalendarEventsLoading.set(false);
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

// Calendar Derived Stores
export const calendarEvents = {
	subscribe: (cb: (val: CalendarEvent[]) => void) => eventsStore.subscribe((val) => cb(val.calendar.list))
};

export const calendarLoading = isCalendarEventsLoading;

export const calendarError = {
	subscribe: (cb: (val: string | null) => void) =>
		eventsStore.subscribe((val) => cb(val.calendar.error))
};

export const upcomingError = {
	subscribe: (cb: (val: string | null) => void) =>
		eventsStore.subscribe((val) => cb(val.upcoming.error))
};

export const historyError = {
	subscribe: (cb: (val: string | null) => void) =>
		eventsStore.subscribe((val) => cb(val.history.error))
};
