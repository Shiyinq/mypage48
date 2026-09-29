import { page48Api, type TrendingTag } from '$lib/api/page48';
import { members as membersApi, type MemberXAccount } from '$lib/apis/members';
import { logger } from '$lib/utils/logger';
import { createRequestDedup } from '$lib/utils/requestDedup';

export const page48NavbarStore = $state<{
	pageType:
		| 'feed'
		| 'post-detail'
		| 'user-profile'
		| 'bookmarks'
		| 'search'
		| 'trending'
		| 'members';
}>({
	pageType: 'feed'
});

/**
 * Cached list store shared at module scope.
 *
 * The Page48 sidebar hashtags (member X accounts, trending tags) are mounted on
 * every Page48 page (feed, photos, videos, profile, tag, post detail). Without
 * caching they refetch on each navigation, so we keep the result in the store
 * and only fetch once per session (unless `force` is passed), deduplicating
 * concurrent requests like the other stores do.
 */
interface CachedListState<T> {
	data: T[];
	isLoading: boolean;
	isLoaded: boolean;
	error: string | null;
}

function createCachedListStore<T>(key: string, fetcher: () => Promise<T[]>) {
	const state = $state<CachedListState<T>>({
		data: [],
		isLoading: false,
		isLoaded: false,
		error: null
	});
	const dedup = createRequestDedup();

	return {
		get data() {
			return state.data;
		},
		get isLoading() {
			return state.isLoading;
		},
		get isLoaded() {
			return state.isLoaded;
		},
		get error() {
			return state.error;
		},

		/** Return the cached list when already loaded, otherwise fetch (deduped). */
		load: async (force = false) => {
			if (state.isLoaded && !force) return;

			return dedup.execute(key, async () => {
				state.isLoading = true;
				state.error = null;
				try {
					state.data = await fetcher();
					state.isLoaded = true;
				} catch (e) {
					logger.error(`Failed to load ${key}`, e, { context: 'Page48Store' });
					state.error = `Failed to load ${key}`;
					// Mark as settled so the skeleton doesn't spin forever.
					state.isLoaded = true;
				} finally {
					state.isLoading = false;
				}
			});
		},

		reset: () => {
			state.data = [];
			state.isLoading = false;
			state.isLoaded = false;
			state.error = null;
			dedup.clear();
		}
	};
}

/** Member X/Twitter hashtags shown on the left sidebar. */
export const memberXTagsStore = createCachedListStore<MemberXAccount>('member X accounts', () =>
	membersApi.getXAccounts()
);

/** Trending hashtags shown on the right sidebar. */
export const trendingTagsStore = createCachedListStore<TrendingTag>(
	'trending tags',
	async () => (await page48Api.getTrendingTags(8)).tags
);

/**
 * Global video sound preference (session-scoped). Videos autoplay muted, but once
 * the user unmutes one video every subsequent video also plays with sound.
 */
export const page48SoundStore = $state<{ enabled: boolean }>({ enabled: false });

export function setPage48Sound(enabled: boolean) {
	page48SoundStore.enabled = enabled;
}
