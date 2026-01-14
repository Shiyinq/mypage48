import { writable, get } from 'svelte/store';
import { events } from '$lib/apis/events';
import type { Event, PaginationMeta } from '$lib/types';
import { isCacheExpired } from '$lib/utils/cache';
import { logger } from '$lib/utils/logger';

interface EventsState {
    upcoming: {
        list: Event[];
        loading: boolean;
        error: string | null;
        lastUpdated: number;
    };
    history: {
        list: Event[];
        pagination: PaginationMeta;
        loading: boolean;
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

function createEventsStore() {
    const initialState: EventsState = {
        upcoming: {
            list: [],
            loading: false,
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
            loading: false,
            error: null,
            lastUpdated: 0,
            defaultCache: null
        }
    };

    const { subscribe, set, update } = writable<EventsState>(initialState);

    return {
        subscribe,
        reset: () => set(initialState),

        loadUpcoming: async (forceRefresh = false) => {
            const state = get({ subscribe });
            const now = Date.now();

            if (!forceRefresh && state.upcoming.list.length > 0 && !isCacheExpired(state.upcoming.lastUpdated)) {
                return;
            }

            update(s => ({ ...s, upcoming: { ...s.upcoming, loading: true, error: null } }));

            try {
                const res = await events.getCurrentEvents(1, 100); // Fetch mostly all current events
                update(s => ({
                    ...s,
                    upcoming: {
                        list: res.data,
                        loading: false,
                        error: null,
                        lastUpdated: now
                    }
                }));
            } catch (e) {
                logger.error('Failed to load upcoming events', e);
                update(s => ({
                    ...s,
                    upcoming: { ...s.upcoming, loading: false, error: 'Failed to load upcoming events' }
                }));
            }
        },

        loadHistory: async (page = 1, forceRefresh = false) => {
            const state = get({ subscribe });
            const now = Date.now();

            // Optimistic Check for Page 1
            if (page === 1 && !forceRefresh && state.history.defaultCache) {
                if (!isCacheExpired(state.history.defaultCache.lastUpdated)) {
                    update(s => ({
                        ...s,
                        history: {
                            ...s.history,
                            list: s.history.defaultCache!.list,
                            pagination: s.history.defaultCache!.pagination,
                            loading: false,
                            error: null
                        }
                    }));
                    return;
                }
            }

            update(s => ({ ...s, history: { ...s.history, loading: true, error: null } }));

            try {
                const res = await events.getEvents(page, 20); // API defaults, matches UI limit

                update(s => {
                    const newState = {
                        ...s,
                        history: {
                            ...s.history,
                            list: res.data,
                            pagination: res.meta,
                            loading: false,
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
                update(s => ({
                    ...s,
                    history: { ...s.history, loading: false, error: 'Failed to load event history' }
                }));
            }
        }
    };
}

export const eventsStore = createEventsStore();

// Derived Stores
export const upcomingEvents = {
    subscribe: (cb: (val: Event[]) => void) => eventsStore.subscribe(val => cb(val.upcoming.list))
};

export const upcomingLoading = {
    subscribe: (cb: (val: boolean) => void) => eventsStore.subscribe(val => cb(val.upcoming.loading))
};

export const historyEvents = {
    subscribe: (cb: (val: Event[]) => void) => eventsStore.subscribe(val => cb(val.history.list))
};

export const historyPagination = {
    subscribe: (cb: (val: PaginationMeta) => void) => eventsStore.subscribe(val => cb(val.history.pagination))
};

export const historyLoading = {
    subscribe: (cb: (val: boolean) => void) => eventsStore.subscribe(val => cb(val.history.loading))
};

export const upcomingError = {
    subscribe: (cb: (val: string | null) => void) => eventsStore.subscribe(val => cb(val.upcoming.error))
};

export const historyError = {
    subscribe: (cb: (val: string | null) => void) => eventsStore.subscribe(val => cb(val.history.error))
};
