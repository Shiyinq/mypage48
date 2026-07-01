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
	loadedPages: Set<number>;
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
	cache: {},
	loadedPages: new Set()
});

const state = $state<NewsState>(getInitialState());
export const newsFilter = $state<NewsFilter>({});
const newsDedup = createRequestDedup();

function createNewsStore() {
	let currentRequestId = 0;
	let loadGeneration = 0;

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
			state.loadedPages = freshState.loadedPages;
			currentRequestId++;
			newsDedup.clear();
		},

		load: async (page = 1, limit = 12, forceRefresh = false, filter?: NewsFilter) => {
			const now = Date.now();
			const currentFilter = filter || newsFilter;
			const filterKey = JSON.stringify(currentFilter);
			const cacheKey = `${page}-${filterKey}`;

			loadGeneration++;

			// Check multi-page cache first
			const cachedPage = state.cache[cacheKey];
			if (cachedPage && !forceRefresh && !isCacheExpired(cachedPage.lastUpdated)) {
				// Immediate cache hit: update current state and return
				state.list = cachedPage.list;
				state.pagination = cachedPage.pagination;
				state.lastUpdated = cachedPage.lastUpdated;
				state.isLoading = false;
				state.error = null;
				state.loadedPages = new Set([page]);
				return;
			}

			// Capture the request id at the start so we can detect resets
			const requestId = currentRequestId;

			// If no valid cache or forceRefresh, proceed with loading
			state.error = null;
			state.isLoading = true;
			state.loadedPages = new Set([page]);

			// REPLACE rather than mutate to avoid bleeding state into cache
			state.pagination = {
				...state.pagination,
				current_page: page
			};

			try {
				const res = await newsDedup.execute(`news-${cacheKey}`, async () => {
					return await news.getNews(page, limit, currentFilter.startDate, currentFilter.endDate);
				});

				// Race condition check: only update if store hasn't been reset
				if (requestId !== currentRequestId) {
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

		loadMore: async (limit = 12) => {
			const gen = loadGeneration;
			const nextPage = state.pagination.next_page;
			if (!nextPage || state.isLoading) return;

			if (state.loadedPages.has(nextPage)) {
				return;
			}
			state.loadedPages.add(nextPage);

			const now = Date.now();
			const currentFilter = newsFilter;
			const filterKey = JSON.stringify(currentFilter);
			const cacheKey = `${nextPage}-${filterKey}`;

			const cachedPage = state.cache[cacheKey];
			if (cachedPage && !isCacheExpired(cachedPage.lastUpdated)) {
				if (gen !== loadGeneration) return;
				state.list = [...state.list, ...cachedPage.list];
				state.pagination = {
					...cachedPage.pagination,
					current_page: cachedPage.pagination.current_page
				};
				state.lastUpdated = cachedPage.lastUpdated;
				return;
			}

			const requestId = currentRequestId;
			state.isLoading = true;

			try {
				const res = await newsDedup.execute(`news-${cacheKey}`, async () => {
					return await news.getNews(
						nextPage,
						limit,
						currentFilter.startDate,
						currentFilter.endDate
					);
				});

				if (requestId !== currentRequestId) return;
				if (gen !== loadGeneration) return;

				const standardizedMeta: PaginationMeta = {
					current_page: res.meta.page,
					last_page: res.meta.total_page,
					total_data: res.meta.count_total,
					per_page: res.meta.limit_per_page,
					next_page: res.meta.page < res.meta.total_page ? res.meta.page + 1 : null
				};

				const existingIds = new Set(state.list.map((n) => n.news_id));
				const newItems = res.data.filter((n) => !existingIds.has(n.news_id));
				state.list = [...state.list, ...newItems];
				state.pagination = standardizedMeta;
				state.lastUpdated = now;

				state.cache[cacheKey] = {
					list: res.data,
					pagination: standardizedMeta,
					lastUpdated: now
				};
			} catch (e) {
				if (requestId === currentRequestId) {
					logger.error('Failed to load more news', e);
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
