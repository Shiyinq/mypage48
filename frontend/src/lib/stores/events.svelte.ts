import { events } from '$lib/apis/events';
import type { Event, CalendarEvent, PaginationMeta } from '$lib/types';
import { isCacheExpired } from '$lib/utils/cache';
import { logger } from '$lib/utils/logger';

/**
 * Events store - migrated to Svelte 5 Shared Rune State.
 * Manages upcoming events, event history, and the theater calendar.
 */

interface EventsState {
	upcoming: {
		list: Event[];
		error: string | null;
		lastUpdated: number;
		isLoading: boolean;
	};
	history: {
		list: Event[];
		pagination: PaginationMeta;
		error: string | null;
		lastUpdated: number;
		isLoading: boolean;
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
		isLoading: boolean;
		year: number;
		month: number;
		cache: Record<string, { list: CalendarEvent[]; lastUpdated: number }>;
	};
}

const initialState: EventsState = {
	upcoming: {
		list: [],
		error: null,
		lastUpdated: 0,
		isLoading: false
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
		isLoading: false,
		defaultCache: null
	},
	calendar: {
		list: [],
		error: null,
		lastUpdated: 0,
		isLoading: false,
		year: 0,
		month: 0,
		cache: {}
	}
};

const state = $state<EventsState>(initialState);

// Maps legacy image-based event types to modern types.
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

		if (mappedType === 'BIRTHDAY' && 'isBirthday' in updatedEvent) {
			(updatedEvent as CalendarEvent).isBirthday = true;
		}

		return updatedEvent as T;
	}
	return event;
}

function createEventsStore() {
	return {
		get upcoming() {
			return state.upcoming;
		},
		get history() {
			return state.history;
		},
		get calendar() {
			return state.calendar;
		},

		reset: () => {
			Object.assign(state, initialState);
		},

		loadUpcoming: async (forceRefresh = false) => {
			const now = Date.now();
			if (
				!forceRefresh &&
				state.upcoming.list.length > 0 &&
				!isCacheExpired(state.upcoming.lastUpdated)
			) {
				return;
			}

			state.upcoming.error = null;
			state.upcoming.isLoading = true;

			try {
				const res = await events.getCurrentEvents(1, 100);
				state.upcoming.list = res.data.map(translateLegacyEvent);
				state.upcoming.lastUpdated = now;
				state.upcoming.error = null;
			} catch (e) {
				logger.error('Failed to load upcoming events', e);
				state.upcoming.error = 'Failed to load upcoming events';
			} finally {
				state.upcoming.isLoading = false;
			}
		},

		loadHistory: async (page = 1) => {
			const now = Date.now();
			state.history.error = null;
			state.history.isLoading = true;

			try {
				const res = await events.getEvents(page, 20);
				const translatedData = res.data.map(translateLegacyEvent);

				state.history.list = translatedData;
				state.history.pagination = res.meta;
				state.history.lastUpdated = now;
				state.history.error = null;

				if (page === 1) {
					state.history.defaultCache = {
						list: res.data,
						pagination: res.meta,
						lastUpdated: now
					};
				}
			} catch (e) {
				logger.error('Failed to load event history', e);
				state.history.error = 'Failed to load event history';
			} finally {
				state.history.isLoading = false;
			}
		},

		loadCalendar: async (year: number, month: number, forceRefresh = false) => {
			const now = Date.now();
			const cacheKey = `${year}-${month}`;

			if (
				!forceRefresh &&
				state.calendar.year === year &&
				state.calendar.month === month &&
				state.calendar.list.length > 0 &&
				!isCacheExpired(state.calendar.lastUpdated)
			) {
				return;
			}

			if (
				!forceRefresh &&
				state.calendar.cache[cacheKey] &&
				!isCacheExpired(state.calendar.cache[cacheKey].lastUpdated)
			) {
				const cached = state.calendar.cache[cacheKey];
				state.calendar.list = cached.list;
				state.calendar.lastUpdated = cached.lastUpdated;
				state.calendar.year = year;
				state.calendar.month = month;
				state.calendar.error = null;
				return;
			}

			const shouldClear = state.calendar.year !== year || state.calendar.month !== month;
			state.calendar.year = year;
			state.calendar.month = month;
			state.calendar.error = null;
			if (shouldClear) state.calendar.list = [];
			state.calendar.isLoading = true;

			try {
				const res = await events.getCalendarEvents(year, month);
				const translatedData = res.map(translateLegacyEvent);

				if (state.calendar.year !== year || state.calendar.month !== month) return;

				state.calendar.list = translatedData;
				state.calendar.lastUpdated = now;
				state.calendar.cache[cacheKey] = {
					list: translatedData,
					lastUpdated: now
				};
				state.calendar.error = null;
			} catch (e) {
				logger.error('Failed to load calendar events', e);
				state.calendar.error = 'Failed to load calendar events';
			} finally {
				state.calendar.isLoading = false;
			}
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: EventsState) => void) => {
			fn(state);
			$effect.root(() => {
				$effect(() => {
					fn(state);
				});
			});
			return () => {};
		}
	};
}

export const eventsStore = createEventsStore();

// Derived Stores (Migration Aliases)
export const upcomingEvents = {
	get value() {
		return state.upcoming.list;
	},
	subscribe: (cb: (val: Event[]) => void) => {
		cb(state.upcoming.list);
		$effect.root(() => {
			$effect(() => cb(state.upcoming.list));
		});
		return () => {};
	}
};

export const upcomingLoading = {
	get value() {
		return state.upcoming.isLoading;
	},
	subscribe: (cb: (val: boolean) => void) => {
		cb(state.upcoming.isLoading);
		$effect.root(() => {
			$effect(() => cb(state.upcoming.isLoading));
		});
		return () => {};
	}
};

export const historyEvents = {
	get value() {
		return state.history.list;
	},
	subscribe: (cb: (val: Event[]) => void) => {
		cb(state.history.list);
		$effect.root(() => {
			$effect(() => cb(state.history.list));
		});
		return () => {};
	}
};

export const historyPagination = {
	get value() {
		return state.history.pagination;
	},
	subscribe: (cb: (val: PaginationMeta) => void) => {
		cb(state.history.pagination);
		$effect.root(() => {
			$effect(() => cb(state.history.pagination));
		});
		return () => {};
	}
};

export const historyLoading = {
	get value() {
		return state.history.isLoading;
	},
	subscribe: (cb: (val: boolean) => void) => {
		cb(state.history.isLoading);
		$effect.root(() => {
			$effect(() => cb(state.history.isLoading));
		});
		return () => {};
	}
};

export const calendarEvents = {
	get value() {
		return state.calendar.list;
	},
	subscribe: (cb: (val: CalendarEvent[]) => void) => {
		cb(state.calendar.list);
		$effect.root(() => {
			$effect(() => cb(state.calendar.list));
		});
		return () => {};
	}
};

export const calendarLoading = {
	get value() {
		return state.calendar.isLoading;
	},
	subscribe: (cb: (val: boolean) => void) => {
		cb(state.calendar.isLoading);
		$effect.root(() => {
			$effect(() => cb(state.calendar.isLoading));
		});
		return () => {};
	}
};

export const calendarError = {
	get value() {
		return state.calendar.error;
	},
	subscribe: (cb: (val: string | null) => void) => {
		cb(state.calendar.error);
		$effect.root(() => {
			$effect(() => cb(state.calendar.error));
		});
		return () => {};
	}
};

export const upcomingError = {
	get value() {
		return state.upcoming.error;
	},
	subscribe: (cb: (val: string | null) => void) => {
		cb(state.upcoming.error);
		$effect.root(() => {
			$effect(() => cb(state.upcoming.error));
		});
		return () => {};
	}
};

export const historyError = {
	get value() {
		return state.history.error;
	},
	subscribe: (cb: (val: string | null) => void) => {
		cb(state.history.error);
		$effect.root(() => {
			$effect(() => cb(state.history.error));
		});
		return () => {};
	}
};

export const isUpcomingEventsLoading = upcomingLoading;
export const isHistoryEventsLoading = historyLoading;
export const isCalendarEventsLoading = calendarLoading;
