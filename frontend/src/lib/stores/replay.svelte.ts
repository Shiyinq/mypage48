import { replayApi } from '$lib/apis/replay';
import type { ReplayVideo } from '$lib/types/replay';
import type { PaginationMeta } from '$lib/types/common';
import { createRequestDedup } from '$lib/utils/requestDedup';

const REPLAY_CACHE_TTL = 5 * 60 * 1000;

interface ReplayPageCache {
	videos: ReplayVideo[];
	pagination: PaginationMeta;
	lastUpdated: number;
}

interface ReplayState {
	videos: ReplayVideo[];
	pagination: PaginationMeta;
	loading: boolean;
	error: string | null;
	lastUpdated: number;
	cache: Record<string, ReplayPageCache>;
	loadedPages: Set<number>;
	currentFilterKey: string;
}

const getInitialState = (): ReplayState => ({
	videos: [],
	pagination: {
		current_page: 1,
		last_page: 1,
		total_data: 0,
		per_page: 20,
		next_page: null
	},
	loading: true,
	error: null,
	lastUpdated: 0,
	cache: {},
	loadedPages: new Set(),
	currentFilterKey: ''
});

const state = $state<ReplayState>(getInitialState());

const dedup = createRequestDedup();

function createReplayStore() {
	let currentRequestId = 0;
	let loadGeneration = 0;

	return {
		get videos() {
			return state.videos;
		},
		get pagination() {
			return state.pagination;
		},
		get loading() {
			return state.loading;
		},
		get error() {
			return state.error;
		},

		reset: () => {
			const freshState = getInitialState();
			state.videos = freshState.videos;
			state.pagination = freshState.pagination;
			state.loading = freshState.loading;
			state.error = freshState.error;
			state.lastUpdated = freshState.lastUpdated;
			state.cache = freshState.cache;
			state.loadedPages = freshState.loadedPages;
			currentRequestId++;
			dedup.clear();
		},

		loadVideos: async (
			page = 1,
			limit = 20,
			search = '',
			platform = '',
			member = '',
			force = false
		) => {
			const normSearch = search.trim();
			const normPlatform = platform === 'all' || !platform ? '' : platform.trim().toLowerCase();
			const normMember = member.trim();

			const filterKey = `${normSearch}-${normPlatform}-${normMember}`;
			const cacheKey = `${page}-${filterKey}`;
			const now = Date.now();

			loadGeneration++;
			state.currentFilterKey = filterKey;

			const cachedPage = state.cache[cacheKey];
			if (cachedPage && !force && now - cachedPage.lastUpdated < REPLAY_CACHE_TTL) {
				state.videos = cachedPage.videos;
				state.pagination = cachedPage.pagination;
				state.lastUpdated = cachedPage.lastUpdated;
				state.loading = false;
				state.error = null;
				state.loadedPages = new Set([page]);
				return;
			}

			const requestId = currentRequestId;
			state.error = null;
			state.loading = true;
			state.loadedPages = new Set([page]);

			// Clear videos and reset pagination when loading page 1 to show loading skeleton
			if (page === 1) {
				state.videos = [];
				state.pagination = getInitialState().pagination;
			}

			try {
				const res = await dedup.execute(`replay-${cacheKey}`, async () => {
					return await replayApi.getVideos(page, limit, normSearch, normPlatform, normMember);
				});

				if (requestId !== currentRequestId) return;

				state.videos = res.data;
				state.pagination = res.meta;
				state.lastUpdated = now;

				state.cache[cacheKey] = {
					videos: res.data,
					pagination: res.meta,
					lastUpdated: now
				};
			} catch (e) {
				if (requestId === currentRequestId) {
					state.error = (e as Error).message;
					console.error('Failed to load replay videos:', e);
				}
			} finally {
				if (requestId === currentRequestId) {
					state.loading = false;
				}
			}
		},

		loadMore: async (limit = 20, search = '', platform = '', member = '') => {
			const gen = loadGeneration;
			const nextPage = state.pagination.next_page;
			if (!nextPage || state.loading) return;

			if (state.loadedPages.has(nextPage)) return;
			state.loadedPages.add(nextPage);

			const normSearch = search.trim();
			const normPlatform = platform === 'all' || !platform ? '' : platform.trim().toLowerCase();
			const normMember = member.trim();

			const filterKey = `${normSearch}-${normPlatform}-${normMember}`;
			if (filterKey !== state.currentFilterKey) return;

			const cacheKey = `${nextPage}-${filterKey}`;
			const now = Date.now();

			const cachedPage = state.cache[cacheKey];
			if (cachedPage && now - cachedPage.lastUpdated < REPLAY_CACHE_TTL) {
				if (gen !== loadGeneration) return;
				state.videos = [...state.videos, ...cachedPage.videos];
				state.pagination = cachedPage.pagination;
				state.lastUpdated = cachedPage.lastUpdated;
				return;
			}

			const requestId = currentRequestId;
			state.loading = true;

			try {
				const res = await dedup.execute(`replay-${cacheKey}`, async () => {
					return await replayApi.getVideos(nextPage, limit, normSearch, normPlatform, normMember);
				});

				if (requestId !== currentRequestId || gen !== loadGeneration) return;

				state.videos = [...state.videos, ...res.data];
				state.pagination = res.meta;
				state.lastUpdated = now;

				state.cache[cacheKey] = {
					videos: res.data,
					pagination: res.meta,
					lastUpdated: now
				};
			} catch (e) {
				if (requestId === currentRequestId) {
					state.error = (e as Error).message;
					console.error('Failed to load more replay videos:', e);
				}
			} finally {
				if (requestId === currentRequestId) {
					state.loading = false;
				}
			}
		},

		getVideoByYoutubeId: async (youtubeId: string): Promise<ReplayVideo | null> => {
			try {
				const res = await replayApi.getVideos(1, 1, undefined, undefined, undefined, youtubeId);
				return res.data?.[0] || null;
			} catch (e) {
				console.error('Failed to fetch replay by youtube_id:', e);
				return null;
			}
		},

		getSrt: async (liveId: string): Promise<string> => {
			return await replayApi.getSrt(liveId);
		}
	};
}

export const replayStore = createReplayStore();
