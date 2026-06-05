import { news } from '$lib/apis/news';
import type { News, PaginationMeta } from '$lib/types';
import { isCacheExpired } from '$lib/utils/cache';
import { logger } from '$lib/utils/logger';
import { createRequestDedup } from '$lib/utils/requestDedup';

/**
 * News store - migrated to Svelte 5 Shared Rune State.
 * Manages the fetching and pagination of news articles.
 */

interface NewsPageCache {
	list: News[];
	pagination: PaginationMeta;
	lastUpdated: number;
}

interface NewsState {
	list: News[];
	pagination: PaginationMeta;
	error: string | null;
	lastUpdated: number;
	isLoading: boolean;
	cache: Record<string, NewsPageCache>;
}

export interface NewsFilter {
	startDate?: string;
	endDate?: string;
}

const getInitialState = (): NewsState => ({
	list: [],
	pagination: {
		current_page: 1,
		last_page: 1,
		total_data: 0,
		per_page: 12,
		next_page: null
	},
	error: null,
	lastUpdated: 0,
	isLoading: false,
	cache: {}
});

const state = $state<NewsState>(getInitialState());
export const newsFilter = $state<NewsFilter>({});
const newsDedup = createRequestDedup();

function createNewsStore() {
	let currentRequestId = 0;

	return {
		get list() {
			return state.list;
		},
		get pagination() {
			return state.pagination;
		},
		get error() {
			return state.error;
		},
		get isLoading() {
			return state.isLoading;
		},

		reset: () => {
			const freshState = getInitialState();
			state.list = freshState.list;
			state.pagination = freshState.pagination;
			state.error = freshState.error;
			state.lastUpdated = freshState.lastUpdated;
			state.isLoading = freshState.isLoading;
			state.cache = freshState.cache;
			currentRequestId++;
			newsDedup.clear();
		},

		load: async (page = 1, limit = 12, forceRefresh = false, filter?: NewsFilter) => {
			const now = Date.now();
			const requestId = ++currentRequestId;
			const currentFilter = filter || newsFilter;
			const filterKey = JSON.stringify(currentFilter);
			const cacheKey = `${page}-${filterKey}`;

			// Check multi-page cache first
			const cachedPage = state.cache[cacheKey];
			if (cachedPage && !forceRefresh && !isCacheExpired(cachedPage.lastUpdated)) {
				// Immediate cache hit: update current state and return
				state.list = cachedPage.list;
				state.pagination = cachedPage.pagination;
				state.lastUpdated = cachedPage.lastUpdated;
				state.isLoading = false;
				state.error = null;
				return;
			}

			// If no valid cache or forceRefresh, proceed with loading
			state.error = null;
			state.isLoading = true;

			// REPLACE rather than mutate to avoid bleeding state into cache
			state.pagination = {
				...state.pagination,
				current_page: page
			};

			try {
				const res = await newsDedup.execute(`news-${cacheKey}`, async () => {
					return await news.getNews(page, limit, currentFilter.startDate, currentFilter.endDate);
				});

				// Race condition check: only update if this is still the latest request
				if (requestId !== currentRequestId) {
					logger.warn(`Ignoring stale news response for page ${page}`);
					return;
				}

				const standardizedMeta: PaginationMeta = {
					current_page: res.meta.page,
					last_page: res.meta.total_page,
					total_data: res.meta.count_total,
					per_page: res.meta.limit_per_page,
					next_page: res.meta.page < res.meta.total_page ? res.meta.page + 1 : null
				};

				state.list = res.data;
				state.pagination = standardizedMeta;
				state.error = null;
				state.lastUpdated = now;

				// Update multi-page cache
				state.cache[cacheKey] = {
					list: res.data,
					pagination: standardizedMeta,
					lastUpdated: now
				};
			} catch (e) {
				if (requestId === currentRequestId) {
					logger.error('Failed to load news', e);
					state.error = 'Failed to load news';
				}
			} finally {
				if (requestId === currentRequestId) {
					state.isLoading = false;
				}
			}
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: NewsState) => void) => {
			$effect.root(() => {
				$effect(() => {
					fn(state);
				});
			});
			return () => {};
		}
	};
}

export const newsStore = createNewsStore();

// Derived Stores (Migration Aliases)
export const newsList = {
	get value() {
		return state.list;
	},
	subscribe: (cb: (val: News[]) => void) => {
		$effect.root(() => {
			$effect(() => cb(state.list));
		});
		return () => {};
	}
};

export const newsLoading = {
	get value() {
		return state.isLoading;
	},
	subscribe: (cb: (val: boolean) => void) => {
		$effect.root(() => {
			$effect(() => cb(state.isLoading));
		});
		return () => {};
	}
};

export const newsPagination = {
	get value() {
		return state.pagination;
	},
	subscribe: (cb: (val: PaginationMeta) => void) => {
		$effect.root(() => {
			$effect(() => cb(state.pagination));
		});
		return () => {};
	}
};

export const newsError = {
	get value() {
		return state.error;
	},
	subscribe: (cb: (val: string | null) => void) => {
		$effect.root(() => {
			$effect(() => cb(state.error));
		});
		return () => {};
	}
};
