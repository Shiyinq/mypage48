import { memoriesApi } from '$lib/apis/memories';
import { logger } from '$lib/utils/logger';
import { isCacheExpired } from '$lib/utils/cache';
import { createRequestDedup } from '$lib/utils/requestDedup';
import type { TopTwoShotResponse, MemoryItem, MemoryFilters } from '$lib/types';

/**
 * Memories store - migrated to Svelte 5 Shared Rune State.
 * Manages the memory gallery and top 2-shot leaderboard.
 */

// --- Gallery Store ---
interface GalleryState {
	list: MemoryItem[];
	pagination: { page: number; hasMore: boolean };
	filter: MemoryFilters;
	cache: Record<
		string,
		{ list: MemoryItem[]; pagination: { page: number; hasMore: boolean }; lastUpdated: number }
	>;
	error: string | null;
	isLoading: boolean;
}

const initialGalleryState: GalleryState = {
	list: [],
	pagination: { page: 0, hasMore: true },
	filter: { type: 'ALL' },
	cache: {
		'{"type":"ALL"}': { list: [], pagination: { page: 0, hasMore: true }, lastUpdated: 0 },
		'{"type":"TICKET"}': { list: [], pagination: { page: 0, hasMore: true }, lastUpdated: 0 },
		'{"type":"2SHOT"}': { list: [], pagination: { page: 0, hasMore: true }, lastUpdated: 0 }
	},
	error: null,
	isLoading: false
};

const galleryState = $state<GalleryState>(initialGalleryState);
const galleryDedup = createRequestDedup();

function createGalleryStore() {
	return {
		get list() {
			return galleryState.list;
		},
		get pagination() {
			return galleryState.pagination;
		},
		get filter() {
			return galleryState.filter;
		},
		get error() {
			return galleryState.error;
		},
		get isLoading() {
			return galleryState.isLoading;
		},
		get cache() {
			return galleryState.cache;
		},
		get lastUpdated() {
			const cacheKey = JSON.stringify(galleryState.filter);
			const cached = galleryState.cache[cacheKey];
			return cached ? cached.lastUpdated : 0;
		},

		load: async (page: number, filter: MemoryFilters) => {
			const cacheKey = JSON.stringify(filter);

			if (page === 1) {
				const cached = galleryState.cache[cacheKey];
				if (cached && !isCacheExpired(cached.lastUpdated) && cached.list.length > 0) {
					if (JSON.stringify(filter) !== JSON.stringify(galleryState.filter)) {
						galleryState.filter = { ...filter };
						galleryState.list = cached.list;
						galleryState.pagination = cached.pagination;
						galleryState.error = null;
					}
					return;
				}
			}

			// Deduplicate concurrent requests with the same page + filter
			const key = JSON.stringify({ page, filter });
			return galleryDedup.execute(key, async () => {
				if (JSON.stringify(filter) !== JSON.stringify(galleryState.filter)) {
					galleryState.filter = { ...filter };
					galleryState.list = [];
					galleryState.pagination = { page: 0, hasMore: true };
				}

				galleryState.error = null;
				galleryState.isLoading = true;

				try {
					const res = await memoriesApi.getMemories(page, 20, filter);
					const now = Date.now();

					const newItems = res.data.filter(
						(newItem) =>
							!galleryState.list.some((existingItem) => existingItem.uniqueId === newItem.uniqueId)
					);
					const newList = page === 1 ? res.data : [...galleryState.list, ...newItems];
					const newPagination = {
						page,
						hasMore: res.meta.current_page < res.meta.last_page
					};

					galleryState.list = newList;
					galleryState.pagination = newPagination;
					galleryState.cache[cacheKey] = {
						list: newList,
						pagination: newPagination,
						lastUpdated: now
					};
					galleryState.error = null;
				} catch (e) {
					logger.error('Failed to load memories', e, { context: 'GalleryStore' });
					galleryState.error = 'Failed to load memories';
					throw e;
				} finally {
					galleryState.isLoading = false;
				}
			});
		},

		reset: () => {
			Object.assign(galleryState, initialGalleryState);
			galleryDedup.clear();
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: GalleryState) => void) => {
			fn(galleryState);
			$effect.root(() => {
				$effect(() => {
					fn(galleryState);
				});
			});
			return () => {};
		}
	};
}

export const galleryStore = createGalleryStore();

// Compatibility alias
export const isGalleryLoading = {
	get value() {
		return galleryState.isLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(galleryState.isLoading);
		$effect.root(() => {
			$effect(() => fn(galleryState.isLoading));
		});
		return () => {};
	}
};

// --- Top 2-Shot Store ---
interface TopTwoShotState {
	data: TopTwoShotResponse | null;
	lastUpdated: number;
	error: string | null;
	isLoading: boolean;
	filter: {
		selectedYear?: number;
		startMonth?: number;
		endMonth?: number;
		isAllData?: boolean;
	};
}

const initialTopTwoShotState: TopTwoShotState = {
	data: null,
	lastUpdated: 0,
	error: null,
	isLoading: false,
	filter: {}
};

const topTwoShotState = $state<TopTwoShotState>(initialTopTwoShotState);
let lastFetchedTwoShotFilterKey = $state('');
const topTwoShotDedup = createRequestDedup();

function createTopTwoShotStore() {
	return {
		get data() {
			return topTwoShotState.data;
		},
		get lastUpdated() {
			return topTwoShotState.lastUpdated;
		},
		get error() {
			return topTwoShotState.error;
		},
		get isLoading() {
			return topTwoShotState.isLoading;
		},

		load: async (filter?: {
			selectedYear?: number;
			startMonth?: number;
			endMonth?: number;
			isAllData?: boolean;
		}) => {
			const currentFilterKey = filter ? JSON.stringify(filter) : '{}';

			if (
				topTwoShotState.data &&
				!isCacheExpired(topTwoShotState.lastUpdated) &&
				lastFetchedTwoShotFilterKey === currentFilterKey
			) {
				return;
			}

			// Deduplicate concurrent requests
			return topTwoShotDedup.execute('top-2shot-' + currentFilterKey, async () => {
				topTwoShotState.error = null;
				topTwoShotState.isLoading = true;

				try {
					const res = await memoriesApi.getTopTwoShot(filter);
					topTwoShotState.data = res;
					topTwoShotState.lastUpdated = Date.now();
					topTwoShotState.error = null;
					if (filter) topTwoShotState.filter = { ...filter };
					lastFetchedTwoShotFilterKey = currentFilterKey;
				} catch (e) {
					logger.error('Failed to load top 2-shot', e, { context: 'TopTwoShotStore' });
					topTwoShotState.error = 'Failed to load top 2-shot';
					throw e;
				} finally {
					topTwoShotState.isLoading = false;
				}
			});
		},

		reset: () => {
			Object.assign(topTwoShotState, initialTopTwoShotState);
			topTwoShotDedup.clear();
			lastFetchedTwoShotFilterKey = '';
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: TopTwoShotState) => void) => {
			fn(topTwoShotState);
			$effect.root(() => {
				$effect(() => {
					fn(topTwoShotState);
				});
			});
			return () => {};
		}
	};
}

export const topTwoShotStore = createTopTwoShotStore();

// Compatibility alias
export const isTopTwoShotLoading = {
	get value() {
		return topTwoShotState.isLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(topTwoShotState.isLoading);
		$effect.root(() => {
			$effect(() => fn(topTwoShotState.isLoading));
		});
		return () => {};
	}
};
