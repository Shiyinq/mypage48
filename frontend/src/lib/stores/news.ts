import { writable, get } from 'svelte/store';
import { news } from '$lib/apis/news';
import type { News, PaginationMeta } from '$lib/types';
import { isCacheExpired } from '$lib/utils/cache';
import { logger } from '$lib/utils/logger';

interface NewsState {
	list: News[];
	pagination: PaginationMeta;
	error: string | null;
	lastUpdated: number;
}

export const isNewsLoading = writable(false);

function createNewsStore() {
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
		lastUpdated: 0
	};

	const { subscribe, set, update } = writable<NewsState>(initialState);

	return {
		subscribe,
		reset: () => {
			set(initialState);
			isNewsLoading.set(false);
		},

		load: async (page = 1, limit = 12, forceRefresh = false) => {
			const state = get({ subscribe });
			const now = Date.now();

			// Simple cache check to avoid reloading the SAME page unnecessarily
			if (
				page === state.pagination.current_page &&
				!forceRefresh &&
				state.list.length > 0 &&
				!isCacheExpired(state.lastUpdated)
			) {
				return;
			}

			update((s) => ({ ...s, error: null }));
			isNewsLoading.set(true);

			try {
				const res = await news.getNews(page, limit);

				const standardizedMeta: PaginationMeta = {
					current_page: res.meta.page,
					last_page: res.meta.total_page,
					total_data: res.meta.count_total,
					per_page: res.meta.limit_per_page,
					next_page: res.meta.page < res.meta.total_page ? res.meta.page + 1 : null
				};

				update((s) => ({
					...s,
					list: res.data, // Replace data for standard pagination
					pagination: standardizedMeta,
					error: null,
					lastUpdated: now
				}));
			} catch (e) {
				logger.error('Failed to load news', e);
				update((s) => ({ ...s, error: 'Failed to load news' }));
			} finally {
				isNewsLoading.set(false);
			}
		}
	};
}

export const newsStore = createNewsStore();

// Derived Stores
export const newsList = {
	subscribe: (cb: (val: News[]) => void) => newsStore.subscribe((val) => cb(val.list))
};

export const newsLoading = isNewsLoading;

export const newsPagination = {
	subscribe: (cb: (val: PaginationMeta) => void) => newsStore.subscribe((val) => cb(val.pagination))
};

export const newsError = {
	subscribe: (cb: (val: string | null) => void) => newsStore.subscribe((val) => cb(val.error))
};
