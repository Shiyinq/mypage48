import { writable, get } from 'svelte/store';
import { memoriesApi } from '$lib/apis/memories';
import { logger } from '$lib/utils/logger';
import { CACHE_EXPIRATION_MS, isCacheExpired } from '$lib/utils/cache';
import type { FilterType } from '$lib/components/memories';
import type { TopTwoShotResponse, MemoryItem } from '$lib/types';

// --- Gallery Store ---
interface GalleryState {
	list: MemoryItem[];
	pagination: { page: number; hasMore: boolean };
	filter: FilterType;
	cache: Record<
		FilterType,
		{ list: MemoryItem[]; pagination: { page: number; hasMore: boolean }; lastUpdated: number }
	>; // Cache by filter
}


function createGalleryStore() {
	const initialState: GalleryState = {
		list: [],
		pagination: { page: 0, hasMore: true },
		filter: 'ALL',
		cache: {
			ALL: { list: [], pagination: { page: 0, hasMore: true }, lastUpdated: 0 }, // Init cache structure
			TICKET: { list: [], pagination: { page: 0, hasMore: true }, lastUpdated: 0 },
			'2SHOT': { list: [], pagination: { page: 0, hasMore: true }, lastUpdated: 0 }
		}
	};

	const { subscribe, set, update } = writable<GalleryState>(initialState);

	return {
		subscribe,
		load: async (page: number, filter: FilterType) => {
			const state = get({ subscribe });

			// If switching filters, check cache first
			if (filter !== state.filter) {
				const cached = state.cache[filter];

				if (!isCacheExpired(cached.lastUpdated) && cached.list.length > 0) {
					update((s) => ({
						...s,
						filter,
						list: cached.list,
						pagination: cached.pagination
					}));
					return;
				}
				// If no cache or expired, reset list for new filter
				update((s) => ({ ...s, filter, list: [], pagination: { page: 0, hasMore: true } }));
			}

			// Should we load?
			// If page 1, always load (unless we just restored from cache above, but logic there prevents this fallthrough effectively if we structure carefully)
			// Ideally, we force load if page 1 and explicit call, OR if infinite scroll (page > 1)

			try {
				const res = await memoriesApi.getMemories(page, 20, filter);
				const now = Date.now();

				update((s) => {
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
							[filter]: { list: newList, pagination: newPagination, lastUpdated: now }
						}
					};
				});
			} catch (e) {
				logger.error('Failed to load memories', e, { context: 'GalleryStore' });
				throw e;
			}
		},
		reset: () => set(initialState)
	};
}

export const galleryStore = createGalleryStore();

// --- Top 2-Shot Store ---
// --- Top 2-Shot Store ---
interface TopTwoShotState {
	data: TopTwoShotResponse | null;
	lastUpdated: number;
}

function createTopTwoShotStore() {
	const initialState: TopTwoShotState = {
		data: null,
		lastUpdated: 0
	};

	const { subscribe, set, update } = writable<TopTwoShotState>(initialState);

	return {
		subscribe,
		load: async () => {
			const state = get({ subscribe });
			// Cache check: if loaded, don't reload.
			if (state.data && !isCacheExpired(state.lastUpdated)) return;

			try {
				const res = await memoriesApi.getTopTwoShot();
				update((s) => ({
					...s,
					data: res,
					lastUpdated: Date.now()
				}));
			} catch (e) {
				logger.error('Failed to load top 2-shot', e, { context: 'TopTwoShotStore' });
				throw e;
			}
		},
		reset: () => set(initialState)
	};
}

export const topTwoShotStore = createTopTwoShotStore();
