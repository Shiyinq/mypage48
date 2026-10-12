import type { Page48Post } from '$lib/api/page48';
import { page48Reads } from '$lib/stores/page48.svelte';

/**
 * Persistent state for the Page48 feeds.
 *
 * Each feed keeps its own bucket (posts, pagination cursor, scroll offset and the
 * posts detected while the viewer was away). Because the bucket lives at module
 * scope, navigating between Home and Following (or back to the Photos gallery)
 * renders the data that is already there instead of refetching behind a skeleton,
 * and the scroll offset can be restored.
 */

export interface Page48FeedParams {
	media?: 'text' | 'image' | 'video' | null;
	following?: boolean;
	/** First page size; defaults to 20 (the video feed uses 10). */
	limit?: number;
}

interface FeedBucket {
	posts: Page48Post[];
	nextCursor: string | null;
	hasMore: boolean;
	isLoaded: boolean;
	isLoading: boolean;
	isLoadingMore: boolean;
	isRefreshing: boolean;
	error: string | null;
	/** Last known window scroll offset, so returning restores the position. */
	scrollY: number;
	/** Last known item index, for a feed that scrolls by snap (the video feed). */
	position: number;
	/** Posts found by a background refresh, waiting to be shown on demand. */
	pending: Page48Post[];
}

const FEED_PAGE_SIZE = 20;

/** The page size this bucket was opened with (a media feed may use a smaller one). */
function pageSize(params: Page48FeedParams): number {
	return params.limit ?? FEED_PAGE_SIZE;
}

const buckets = $state<Record<string, FeedBucket>>({});

function createBucket(): FeedBucket {
	return {
		posts: [],
		nextCursor: null,
		hasMore: false,
		isLoaded: false,
		isLoading: false,
		isLoadingMore: false,
		isRefreshing: false,
		error: null,
		scrollY: 0,
		position: 0,
		pending: []
	};
}

function bucket(key: string): FeedBucket {
	if (!buckets[key]) buckets[key] = createBucket();
	return buckets[key];
}

/** Load the first page once. `force` re-fetches (used by the retry button). */
async function ensure(key: string, params: Page48FeedParams, force = false): Promise<void> {
	const state = bucket(key);
	if (state.isLoading) return;
	if (state.isLoaded && !force) return;

	state.isLoading = true;
	state.error = null;
	try {
		const response = await page48Reads.getFeed(
			pageSize(params),
			null,
			params.media ?? null,
			params.following ?? false
		);
		state.posts = response.data;
		state.hasMore = response.meta.hasMore;
		state.nextCursor = response.meta.nextCursor;
		state.pending = [];
		state.isLoaded = true;
	} catch (err) {
		state.error = (err as { message?: string })?.message ?? 'Failed to load feed';
	} finally {
		state.isLoading = false;
	}
}

/** Append the next page, skipping anything already shown. */
async function loadMore(key: string, params: Page48FeedParams): Promise<void> {
	const state = bucket(key);
	if (!state.isLoaded || state.isLoadingMore || !state.hasMore || !state.nextCursor) return;

	state.isLoadingMore = true;
	try {
		const response = await page48Reads.getFeed(
			pageSize(params),
			state.nextCursor,
			params.media ?? null,
			params.following ?? false
		);
		const known = new Set(state.posts.map((post) => post.postId));
		state.posts = [...state.posts, ...response.data.filter((post) => !known.has(post.postId))];
		state.hasMore = response.meta.hasMore;
		state.nextCursor = response.meta.nextCursor;
	} catch {
		// A failed page just leaves the cursor where it was; scrolling retries.
	} finally {
		state.isLoadingMore = false;
	}
}

/**
 * Refresh the first page in the background and stash any posts that are newer
 * than the current top, so the UI can offer them without moving the list.
 */
async function refresh(key: string, params: Page48FeedParams): Promise<void> {
	const state = bucket(key);
	if (!state.isLoaded || state.isRefreshing) return;

	state.isRefreshing = true;
	try {
		const response = await page48Reads.getFeed(
			pageSize(params),
			null,
			params.media ?? null,
			params.following ?? false
		);
		const known = new Set(state.posts.map((post) => post.postId));
		const fresh: Page48Post[] = [];
		// Newest first: the new posts sit at the front, right until a known one.
		for (const post of response.data) {
			if (known.has(post.postId)) break;
			fresh.push(post);
		}
		if (fresh.length > 0) {
			const pendingIds = new Set(state.pending.map((post) => post.postId));
			state.pending = [...fresh.filter((post) => !pendingIds.has(post.postId)), ...state.pending];
		}
	} catch {
		// A failed refresh keeps the feed as it is; the next tick tries again.
	} finally {
		state.isRefreshing = false;
	}
}

/** Move the waiting posts to the top of the feed. */
function applyPending(key: string): void {
	const state = bucket(key);
	if (state.pending.length === 0) return;
	const existing = new Set(state.posts.map((post) => post.postId));
	const add = state.pending.filter((post) => !existing.has(post.postId));
	state.posts = [...add, ...state.posts];
	state.pending = [];
}

/** Put a freshly created post on top (the author's own post, without a refetch). */
function prepend(key: string, post: Page48Post): void {
	const state = bucket(key);
	if (state.posts.some((entry) => entry.postId === post.postId)) return;
	state.posts = [post, ...state.posts];
}

function removePost(key: string, postId: string): void {
	const state = bucket(key);
	state.posts = state.posts.filter((post) => post.postId !== postId);
	state.pending = state.pending.filter((post) => post.postId !== postId);
}

function saveScroll(key: string, scrollY: number): void {
	bucket(key).scrollY = scrollY;
}

function savePosition(key: string, position: number): void {
	bucket(key).position = position;
}

export const page48FeedStore = {
	bucket,
	ensure,
	loadMore,
	refresh,
	applyPending,
	prepend,
	removePost,
	saveScroll,
	savePosition
};
