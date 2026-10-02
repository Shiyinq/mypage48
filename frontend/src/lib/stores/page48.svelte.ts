import {
	page48Api,
	type ActiveUser,
	type Page48NotificationCounts,
	type Page48UserProfile,
	type TrendingTag
} from '$lib/api/page48';
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
		| 'notifications';
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

/** Most active users (last 7 days), shown under the trending tags. */
export const activeUsersStore = createCachedListStore<ActiveUser>(
	'active users',
	async () => (await page48Api.getActiveUsers(5)).users
);

/**
 * How long a hover-card profile may be reused. Long enough that sweeping the
 * pointer over a feed doesn't refetch, short enough that follow counts and bios
 * catch up on their own.
 */
const HOVER_PROFILE_TTL_MS = 5 * 60 * 1000;

/** A handle that failed to load is retried sooner, in case the account is new. */
const HOVER_PROFILE_MISS_TTL_MS = 60 * 1000;

/** A hover-card lookup: the profile, a handle that does not exist, or a failure. */
export type HoverProfileResult =
	| { status: 'ok'; profile: Page48UserProfile }
	| { status: 'missing' }
	| { status: 'error' };

/**
 * Profiles for the username hover card, keyed by handle.
 *
 * Hovering happens constantly and often for the same few authors, so the result is
 * cached per session with a TTL and concurrent requests for one handle are shared.
 * A handle that does not exist is cached too (and briefly), so a mention of a
 * username that was never real is not refetched every time the pointer crosses it.
 * Failures are deliberately not cached, so the next hover tries again.
 */
function createHoverProfileStore() {
	const cache = new Map<string, { result: HoverProfileResult; at: number }>();
	const inflight = new Map<string, Promise<HoverProfileResult>>();

	async function get(username: string): Promise<HoverProfileResult> {
		const key = username.toLowerCase();
		const hit = cache.get(key);
		if (hit) {
			const ttl = hit.result.status === 'ok' ? HOVER_PROFILE_TTL_MS : HOVER_PROFILE_MISS_TTL_MS;
			if (Date.now() - hit.at < ttl) return hit.result;
		}

		const pending = inflight.get(key);
		if (pending) return pending;

		const request = page48Api
			.getUserProfile(key)
			.then((profile): HoverProfileResult => ({ status: 'ok', profile }))
			.catch((err: unknown): HoverProfileResult => {
				const status = (err as { status?: number } | null)?.status;
				return status === 404 ? { status: 'missing' } : { status: 'error' };
			})
			.then((result) => {
				if (result.status !== 'error') cache.set(key, { result, at: Date.now() });
				return result;
			})
			.finally(() => {
				inflight.delete(key);
			});

		inflight.set(key, request);
		return request;
	}

	/** Drop one handle (e.g. after following, which changes the counts). */
	function invalidate(username: string) {
		cache.delete(username.toLowerCase());
	}

	return { get, invalidate };
}

export const page48HoverProfileStore = createHoverProfileStore();

/**
 * Global video sound preference (session-scoped). Videos autoplay muted, but once
 * the user unmutes one video every subsequent video also plays with sound.
 */
export const page48SoundStore = $state<{ enabled: boolean }>({ enabled: false });

export function setPage48Sound(enabled: boolean) {
	page48SoundStore.enabled = enabled;
}

/**
 * Unread Page48 notifications per tab, plus the total shown on the bell. Shared by
 * the navbar and the notifications page so the badge and the tabs agree.
 */
export const page48UnreadStore = $state<Page48NotificationCounts>({
	total: 0,
	replies: 0,
	mentions: 0,
	likes: 0,
	reposts: 0,
	follows: 0
});

/** Write counts that another response already carried (e.g. the overview). */
export function applyPage48Counts(counts: Page48NotificationCounts) {
	Object.assign(page48UnreadStore, counts);
}

/** The counts are cheap but requested on every navigation, so cache them briefly. */
const UNREAD_CACHE_MS = 30_000;
let lastUnreadFetch = 0;
let unreadFetchInFlight = false;

/**
 * Refresh the badge and the per-tab counts. Failures keep the last values, and a
 * fetch in flight is never duplicated. Pass `force` after an action that changes
 * the counts (e.g. opening a tab) to bypass the short cache.
 */
export async function refreshPage48Unread(force = false) {
	if (unreadFetchInFlight) return;
	if (!force && Date.now() - lastUnreadFetch < UNREAD_CACHE_MS) return;

	unreadFetchInFlight = true;
	try {
		Object.assign(page48UnreadStore, await page48Api.getNotificationCounts());
		lastUnreadFetch = Date.now();
	} catch (error) {
		logger.warn('Failed to refresh notification counts', error);
	} finally {
		unreadFetchInFlight = false;
	}
}
