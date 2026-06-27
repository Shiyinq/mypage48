import { events } from '$lib/apis/events';
import type { Event, EventDetail, CalendarEvent, PaginationMeta } from '$lib/types';
import { isCacheExpired } from '$lib/utils/cache';
import { logger } from '$lib/utils/logger';
import { createRequestDedup } from '$lib/utils/requestDedup';

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
		filter: {
			startDate?: string;
			endDate?: string;
		};
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
	detailCache: Record<string, EventDetail>;
	isDetailLoading: boolean;
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
		defaultCache: null,
		filter: {
			startDate: undefined,
			endDate: undefined
		}
	},
	calendar: {
		list: [],
		error: null,
		lastUpdated: 0,
		isLoading: false,
		year: 0,
		month: 0,
		cache: {}
	},
	detailCache: {},
	isDetailLoading: false
};

const state = $state<EventsState>(initialState);
const dedup = createRequestDedup();

// Maps legacy image-based event types to modern types.
const legacyMapping: Record<string, string> = {
	'icon.cat1.png': 'SHOW',
	'icon.cat2.png': 'EVENT',
	'icon.cat3.png': 'GENERAL',
	'icon.cat4.png': 'GENERAL',
	'icon.cat5.png': 'BIRTHDAY',
	'icon.cat7.png': 'BIRTHDAY',
	'icon.cat8.png': 'GENERAL',
	'icon.cat9.png': 'EVENT',
	'icon.cat10.png': 'BIRTHDAY',
	'icon.cat11.png': 'SHOW',
	'icon.cat12.png': 'SHOW',
	'icon.cat13.png': 'SHOW',
	'icon.cat14.png': 'SHOW',
	'icon.cat15.png': 'SHOW',
	'icon.cat17.png': 'SHOW',
	'icon.cat18.png': 'SHOW',
	'icon.cat19.png': 'SHOW',
	'icon.cat20.png': 'SHOW',
	'icon.cat21.png': 'SHOW',
	'icon.cat23.png': 'SHOW',
	'icon.cat99.png': 'GENERAL'
};

function translateLegacyEvent<T extends Event | CalendarEvent>(event: T): T {
	const labelLower = event.label?.toLowerCase().trim() || '';

	let mappedType: string | undefined;
	for (const [key, value] of Object.entries(legacyMapping)) {
		if (labelLower.includes(key)) {
			mappedType = value;
			break;
		}
	}

	if (mappedType) {
		const updatedEvent = {
			...event,
			type: mappedType,
			label: mappedType
		};

		if (mappedType === 'BIRTHDAY' && 'isBirthday' in updatedEvent) {
			(updatedEvent as CalendarEvent).isBirthday = true;
		}

		return updatedEvent as T;
	}

	// Fallback for any other unexpected legacy paths
	if (labelLower.includes('/images/icon.cat') || labelLower.includes('.png')) {
		return {
			...event,
			type: 'SHOW',
			label: 'SHOW'
		} as T;
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
		get detailCache() {
			return state.detailCache;
		},
		get isDetailLoading() {
			return state.isDetailLoading;
		},

		reset: () => {
			Object.assign(state, initialState);
			dedup.clear();
		},

		loadDetail: async (id: string, forceRefresh = false) => {
			if (!forceRefresh && state.detailCache[id]) {
				return state.detailCache[id];
			}

			const key = `detail:${id}`;
			return dedup.execute(key, async () => {
				state.isDetailLoading = true;
				try {
					const detail = await events.getEventById(id);
					// Apply legacy translation for detail view as well
					const translatedDetail = translateLegacyEvent(
						detail as unknown as Event
					) as unknown as typeof detail;
					state.detailCache[id] = translatedDetail;
					return translatedDetail;
				} catch (e) {
					logger.error('Failed to load event detail', e);
					throw e;
				} finally {
					state.isDetailLoading = false;
				}
			});
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

			// Deduplicate concurrent requests
			const key = `upcoming:${forceRefresh}`;
			return dedup.execute(key, async () => {
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
			});
		},

		loadHistory: async (
			page = 1,
			forceRefresh = false,
			customFilter?: { startDate?: string; endDate?: string }
		) => {
			const currentFilter = customFilter || state.history.filter;

			// Short-circuit with cached data for page 1 if no custom filter
			if (
				!forceRefresh &&
				page === 1 &&
				!currentFilter.startDate &&
				!currentFilter.endDate &&
				state.history.defaultCache &&
				!isCacheExpired(state.history.defaultCache.lastUpdated)
			) {
				state.history.list = state.history.defaultCache.list;
				state.history.pagination = state.history.defaultCache.pagination;
				state.history.error = null;
				return;
			}

			// Generate a cache key that includes filter state
			let cacheKey = `history:${page}`;
			if (currentFilter.startDate || currentFilter.endDate) {
				cacheKey += `:${currentFilter.startDate || ''}:${currentFilter.endDate || ''}`;
			}

			// Deduplicate concurrent requests for the same page and filter
			return dedup.execute(cacheKey, async () => {
				const now = Date.now();
				state.history.error = null;
				state.history.isLoading = true;

				try {
					const res = await events.getEvents(
						page,
						20,
						currentFilter.startDate,
						currentFilter.endDate
					);
					const translatedData = res.data.map(translateLegacyEvent);

					state.history.list = translatedData;
					state.history.pagination = res.meta;
					state.history.lastUpdated = now;
					state.history.error = null;

					// Only cache page 1 of unfiltered results
					if (page === 1 && !currentFilter.startDate && !currentFilter.endDate) {
						state.history.defaultCache = {
							list: translatedData,
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
			});
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

			// Deduplicate concurrent requests for the same year/month
			const dedupKey = `calendar:${cacheKey}:${forceRefresh}`;
			return dedup.execute(dedupKey, async () => {
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
			});
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: EventsState) => void) => {
			fn(state);
			const cleanup = $effect.root(() => {
				$effect(() => {
					fn(state);
				});
			});
			return cleanup;
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
		return $effect.root(() => {
			$effect(() => cb(state.upcoming.list));
		});
	}
};

export const upcomingLoading = {
	get value() {
		return state.upcoming.isLoading;
	},
	subscribe: (cb: (val: boolean) => void) => {
		cb(state.upcoming.isLoading);
		return $effect.root(() => {
			$effect(() => cb(state.upcoming.isLoading));
		});
	}
};

export const historyEvents = {
	get value() {
		return state.history.list;
	},
	subscribe: (cb: (val: Event[]) => void) => {
		cb(state.history.list);
		return $effect.root(() => {
			$effect(() => cb(state.history.list));
		});
	}
};

export const historyPagination = {
	get value() {
		return state.history.pagination;
	},
	subscribe: (cb: (val: PaginationMeta) => void) => {
		cb(state.history.pagination);
		return $effect.root(() => {
			$effect(() => cb(state.history.pagination));
		});
	}
};

export const historyLoading = {
	get value() {
		return state.history.isLoading;
	},
	subscribe: (cb: (val: boolean) => void) => {
		cb(state.history.isLoading);
		return $effect.root(() => {
			$effect(() => cb(state.history.isLoading));
		});
	}
};

export const historyFilter = state.history.filter;

export const calendarEvents = {
	get value() {
		return state.calendar.list;
	},
	subscribe: (cb: (val: CalendarEvent[]) => void) => {
		cb(state.calendar.list);
		return $effect.root(() => {
			$effect(() => cb(state.calendar.list));
		});
	}
};

export const calendarLoading = {
	get value() {
		return state.calendar.isLoading;
	},
	subscribe: (cb: (val: boolean) => void) => {
		cb(state.calendar.isLoading);
		return $effect.root(() => {
			$effect(() => cb(state.calendar.isLoading));
		});
	}
};

export const calendarError = {
	get value() {
		return state.calendar.error;
	},
	subscribe: (cb: (val: string | null) => void) => {
		cb(state.calendar.error);
		return $effect.root(() => {
			$effect(() => cb(state.calendar.error));
		});
	}
};

export const upcomingError = {
	get value() {
		return state.upcoming.error;
	},
	subscribe: (cb: (val: string | null) => void) => {
		cb(state.upcoming.error);
		return $effect.root(() => {
			$effect(() => cb(state.upcoming.error));
		});
	}
};

export const historyError = {
	get value() {
		return state.history.error;
	},
	subscribe: (cb: (val: string | null) => void) => {
		cb(state.history.error);
		return $effect.root(() => {
			$effect(() => cb(state.history.error));
		});
	}
};

export const isUpcomingEventsLoading = upcomingLoading;
export const isHistoryEventsLoading = historyLoading;
export const isCalendarEventsLoading = calendarLoading;
