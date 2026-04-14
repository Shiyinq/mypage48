import { news } from '$lib/apis/news';
import type { News, PaginationMeta } from '$lib/types';
import { isCacheExpired } from '$lib/utils/cache';
import { logger } from '$lib/utils/logger';

/**
 * News store - migrated to Svelte 5 Shared Rune State.
 * Manages the fetching and pagination of news articles.
 */

interface NewsState {
	list: News[];
	pagination: PaginationMeta;
	error: string | null;
	lastUpdated: number;
	isLoading: boolean;
}

const initialState: NewsState = {
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
	isLoading: false
};

const state = $state<NewsState>(initialState);

function createNewsStore() {
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
			Object.assign(state, initialState);
		},

		load: async (page = 1, limit = 12, forceRefresh = false) => {
			const now = Date.now();

			// Cache check: if we already have this page and it's not expired, don't re-fetch
			if (
				page === state.pagination.current_page &&
				!forceRefresh &&
				state.list.length > 0 &&
				!isCacheExpired(state.lastUpdated)
			) {
				return;
			}

			state.error = null;
			state.isLoading = true;

			try {
				const res = await news.getNews(page, limit);

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
			} catch (e) {
				logger.error('Failed to load news', e);
				state.error = 'Failed to load news';
			} finally {
				state.isLoading = false;
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
