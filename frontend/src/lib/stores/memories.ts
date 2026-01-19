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
	error: string | null;
}

export const isGalleryLoading = writable(false);

function createGalleryStore() {
	const initialState: GalleryState = {
		list: [],
		pagination: { page: 0, hasMore: true },
		filter: 'ALL',
		cache: {
			ALL: { list: [], pagination: { page: 0, hasMore: true }, lastUpdated: 0 }, // Init cache structure
			TICKET: { list: [], pagination: { page: 0, hasMore: true }, lastUpdated: 0 },
			'2SHOT': { list: [], pagination: { page: 0, hasMore: true }, lastUpdated: 0 }
		},
		error: null
	};

	const { subscribe, set, update } = writable<GalleryState>(initialState);

	return {
		subscribe,
		load: async (page: number, filter: FilterType) => {
			const state = get({ subscribe });

			// Check cache first for page 1
			if (page === 1) {
				const cached = state.cache[filter];
				if (!isCacheExpired(cached.lastUpdated) && cached.list.length > 0) {
					// If switching filters, restore from cache
					if (filter !== state.filter) {
						update((s) => ({
							...s,
							filter,
							list: cached.list,
							pagination: cached.pagination,
							error: null
						}));
					}
					// If same filter (re-visiting), just return as we have valid data
					return;
				}
			}

			// If switching filters (and no valid cache hit above), reset list
			if (filter !== state.filter) {
				update((s) => ({ ...s, filter, list: [], pagination: { page: 0, hasMore: true } }));
			}

			// Should we load?
			// If page 1, always load (unless we just restored from cache above, but logic there prevents this fallthrough effectively if we structure carefully)
			// Ideally, we force load if page 1 and explicit call, OR if infinite scroll (page > 1)

			// Set loading true. For pagination, we might want to distinguish initial load vs load more,
			// but for now consistent 'loading' flag is good, UI can check list length to see if it's 'load more'
			update((s) => ({ ...s, error: null }));
			isGalleryLoading.set(true);

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
						},
						error: null
					};
				});
			} catch (e) {
				logger.error('Failed to load memories', e, { context: 'GalleryStore' });
				update((s) => ({ ...s, error: 'Failed to load memories' }));
				throw e;
			} finally {
				isGalleryLoading.set(false);
			}
		},
		reset: () => {
			set(initialState);
			isGalleryLoading.set(false);
		}
	};
}

export const galleryStore = createGalleryStore();

// --- Top 2-Shot Store ---
interface TopTwoShotState {
	data: TopTwoShotResponse | null;
	lastUpdated: number;
	error: string | null;
}

export const isTopTwoShotLoading = writable(false);

function createTopTwoShotStore() {
	const initialState: TopTwoShotState = {
		data: null,
		lastUpdated: 0,
		error: null
	};

	const { subscribe, set, update } = writable<TopTwoShotState>(initialState);

	return {
		subscribe,
		load: async () => {
			const state = get({ subscribe });
			// Cache check: if loaded, don't reload.
			if (state.data && !isCacheExpired(state.lastUpdated)) return;

			update((s) => ({ ...s, error: null }));
			isTopTwoShotLoading.set(true);

			try {
				const res = await memoriesApi.getTopTwoShot();
				update((s) => ({
					...s,
					data: res,
					lastUpdated: Date.now(),
					error: null
				}));
			} catch (e) {
				logger.error('Failed to load top 2-shot', e, { context: 'TopTwoShotStore' });
				update((s) => ({ ...s, error: 'Failed to load top 2-shot' }));
				throw e;
			} finally {
				isTopTwoShotLoading.set(false);
			}
		},
		reset: () => {
			set(initialState);
			isTopTwoShotLoading.set(false);
		}
	};
}

export const topTwoShotStore = createTopTwoShotStore();
