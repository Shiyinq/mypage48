import { writable, get } from 'svelte/store';
import type { Ticket, TicketFilters, PaginationState } from '$lib/types';
import { ticketsApi } from '$lib/apis/tickets';

// Tickets Store Types
interface TicketsState {
    list: Ticket[];
    pagination: PaginationState;
    filters: TicketFilters;
    defaultCache: { list: Ticket[]; pagination: PaginationState } | null;
    titlesCache: string[] | null;
}

function createTicketsStore() {
    const initialState: TicketsState = {
        list: [],
        pagination: { page: 0, hasMore: true },
        filters: {},
        defaultCache: null,
        titlesCache: null
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
                update(s => ({
                    ...s,
                    list: state.defaultCache!.list,
                    pagination: state.defaultCache!.pagination,
                    filters: {}
                }));
                return;
            }

            try {
                const res = await ticketsApi.getMyTickets(page, 20, filters);

                update(s => {
                    const newList = page === 1 ? res.data : [...s.list, ...res.data];
                    const newPagination = {
                        page,
                        hasMore: res.meta.current_page < res.meta.last_page
                    };

                    const newState = {
                        ...s,
                        list: newList,
                        pagination: newPagination,
                        filters
                    };

                    if (isDefaultLoad) {
                        newState.defaultCache = {
                            list: newList,
                            pagination: newPagination
                        };
                    }

                    return newState;
                });
            } catch (e) {
                console.error("Failed to load tickets", e);
                throw e;
            }
        },
        deleteTicket: async (ticketId: string) => {
            await ticketsApi.deleteTicket(ticketId);

            update(s => {
                const newList = s.list.filter(t => t._id !== ticketId && t.ticket_id !== ticketId);
                let newCache = s.defaultCache;
                if (newCache) {
                    newCache = {
                        ...newCache,
                        list: newCache.list.filter(t => t._id !== ticketId && t.ticket_id !== ticketId)
                    };
                }

                return {
                    ...s,
                    list: newList,
                    defaultCache: newCache
                };
            });
        },

        create: async (payload: Partial<Ticket>) => {
            const newTicket = await ticketsApi.createTicket(payload);
            update(s => ({
                ...s,
                list: [newTicket, ...s.list],
                defaultCache: s.defaultCache ? {
                    ...s.defaultCache,
                    list: [newTicket, ...s.defaultCache.list]
                } : null
            }));
            return newTicket;
        },

        updateTicket: async (ticketId: string, payload: Partial<Ticket>) => {
            const updated = await ticketsApi.updateTicket(ticketId, payload);
            update(s => ({
                ...s,
                list: s.list.map(t => t._id === ticketId ? updated : t),
                defaultCache: s.defaultCache ? {
                    ...s.defaultCache,
                    list: s.defaultCache.list.map(t => t._id === ticketId ? updated : t)
                } : null
            }));
            return updated;
        },

        updateNote: async (ticketId: string, note: string) => {
            await ticketsApi.updateTicket(ticketId, { notes: note });
            update(s => ({
                ...s,
                list: s.list.map(t => t._id === ticketId ? { ...t, notes: note } : t),
                defaultCache: s.defaultCache ? {
                    ...s.defaultCache,
                    list: s.defaultCache.list.map(t => t._id === ticketId ? { ...t, notes: note } : t)
                } : null
            }));
        },

        getAvailableTitles: async () => {
            const state = get({ subscribe });
            if (state.titlesCache) {
                return state.titlesCache;
            }
            const titles = await ticketsApi.getTicketTitles();
            update(s => ({ ...s, titlesCache: titles }));
            return titles;
        },

        reset: () => set(initialState)
    };
}

export const ticketsStore = createTicketsStore();

// Derived stores for backward compatibility
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const tickets = { subscribe: (cb: any) => ticketsStore.subscribe(val => cb(val.list)) };
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const ticketsPagination = { subscribe: (cb: any) => ticketsStore.subscribe(val => cb(val.pagination)) };
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const ticketsFilters = { subscribe: (cb: any) => ticketsStore.subscribe(val => cb(val.filters)) };
