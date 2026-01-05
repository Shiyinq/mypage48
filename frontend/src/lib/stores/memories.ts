import { writable, get } from 'svelte/store';
import { memoriesApi } from '$lib/apis/memories';
import type { FilterType } from '$lib/components/memories';
import type { TopTwoShotResponse, MemoryItem } from '$lib/types';

// --- Gallery Store ---
interface GalleryState {
    list: MemoryItem[];
    pagination: { page: number; hasMore: boolean };
    filter: FilterType;
    cache: Record<FilterType, { list: MemoryItem[]; pagination: { page: number; hasMore: boolean } }>; // Cache by filter
}

function createGalleryStore() {
    const initialState: GalleryState = {
        list: [],
        pagination: { page: 0, hasMore: true },
        filter: 'ALL',
        cache: {
            ALL: { list: [], pagination: { page: 0, hasMore: true } }, // Init cache structure
            TICKET: { list: [], pagination: { page: 0, hasMore: true } },
            '2SHOT': { list: [], pagination: { page: 0, hasMore: true } }
        } as any
    };

    const { subscribe, set, update } = writable<GalleryState>(initialState);

    return {
        subscribe,
        load: async (page: number, filter: FilterType) => {
            const state = get({ subscribe });

            // If switching filters, check cache first
            if (filter !== state.filter) {
                const cached = state.cache[filter];
                if (cached && cached.list.length > 0) {
                    update(s => ({
                        ...s,
                        filter,
                        list: cached.list,
                        pagination: cached.pagination
                    }));
                    return;
                }
                // If no cache, reset list for new filter
                update(s => ({ ...s, filter, list: [], pagination: { page: 0, hasMore: true } }));
            }

            // Should we load?
            // If page 1, always load (unless we just restored from cache above, but logic there prevents this fallthrough effectively if we structure carefully)
            // Ideally, we force load if page 1 and explicit call, OR if infinite scroll (page > 1)

            try {
                const res = await memoriesApi.getMemories(page, 20, filter);

                update(s => {
                    const newList = page === 1 ? res.data : [...s.list, ...res.data];
                    const newPagination = {
                        page,
                        hasMore: res.meta.current_page < res.meta.last_page
                    };

                    return {
                        ...s,
                        list: newList,
                        pagination: newPagination,
                        filter, // Ensure filter is set
                        cache: {
                            ...s.cache,
                            [filter]: { list: newList, pagination: newPagination }
                        }
                    };
                });
            } catch (e) {
                console.error("Failed to load memories", e);
                throw e;
            }
        },
        reset: () => set(initialState)
    };
}

export const galleryStore = createGalleryStore();


// --- Top 2-Shot Store ---
function createTopTwoShotStore() {
    const { subscribe, set } = writable<TopTwoShotResponse | null>(null);

    return {
        subscribe,
        load: async () => {
            // Cache check: if loaded, don't reload. Simple.
            if (get({ subscribe })) return;

            try {
                const res = await memoriesApi.getTopTwoShot();
                set(res);
            } catch (e) {
                console.error("Failed to load top 2-shot", e);
                throw e;
            }
        },
        reset: () => set(null)
    };
}

export const topTwoShotStore = createTopTwoShotStore();
