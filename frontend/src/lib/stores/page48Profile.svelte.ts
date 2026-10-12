import type { Page48Post, Page48UserProfile } from '$lib/api/page48';
import { page48Reads } from '$lib/stores/page48.svelte';

/**
 * Session cache for a Page48 profile: its header and each of its tabs.
 *
 * Revisiting a profile or switching between its tabs reuses what is already here
 * instead of refetching behind a skeleton. The header is quietly revalidated once
 * it goes stale; tabs keep their loaded pages (deep scrolls included) intact.
 *
 * The store lives at module scope, so its lifetime is the session: entries are
 * only dropped when the cache grows past its caps (least recently touched first).
 */

export type Page48ProfileTab =
	| 'posts'
	| 'images'
	| 'videos'
	| 'reposts'
	| 'replies'
	| 'likes'
	| 'bookmarks';

interface ProfileEntry {
	data: Page48UserProfile | null;
	isLoaded: boolean;
	isLoading: boolean;
	error: string | null;
	notFound: boolean;
	/** When the data was last read from the network, for the quiet revalidation. */
	fetchedAt: number;
}

interface ListEntry {
	posts: Page48Post[];
	nextCursor: string | null;
	hasMore: boolean;
	isLoaded: boolean;
	isLoading: boolean;
	isLoadingMore: boolean;
	/** When the first page was last read, for the quiet revalidation. */
	fetchedAt: number;
	/** Last known window scroll offset for this tab, so returning restores it. */
	scrollY: number;
}

const PROFILE_CAP = 30;
const LIST_CAP = 200;
/** Re-reading the header is skipped while the cached copy is this fresh. */
const REVALIDATE_AFTER_MS = 60_000;

const profiles = $state<Record<string, ProfileEntry>>({});
const lists = $state<Record<string, ListEntry>>({});

// Access order per cache, for eviction. A plain Map keeps insertion order, so the
// first key is the least recently touched; entries are re-inserted on use.
const profileOrder = new Map<string, true>();
const listOrder = new Map<string, true>();

const EMPTY_PROFILE: ProfileEntry = {
	data: null,
	isLoaded: false,
	isLoading: false,
	error: null,
	notFound: false,
	fetchedAt: 0
};

const EMPTY_LIST: ListEntry = {
	posts: [],
	nextCursor: null,
	hasMore: false,
	isLoaded: false,
	isLoading: false,
	isLoadingMore: false,
	fetchedAt: 0,
	scrollY: 0
};

function touch(order: Map<string, true>, key: string): void {
	order.delete(key);
	order.set(key, true);
}

/** Drop the least recently touched entries until the cache is under its cap. */
function evict<T>(entries: Record<string, T>, order: Map<string, true>, cap: number): void {
	while (order.size > cap) {
		const oldest = order.keys().next().value;
		if (oldest === undefined) break;
		order.delete(oldest);
		delete entries[oldest];
	}
}

function listKey(username: string, tab: Page48ProfileTab): string {
	return `${username}|${tab}`;
}

function fetchTabList(
	username: string,
	tab: Page48ProfileTab,
	cursor: string | null
): Promise<{ data: Page48Post[]; meta: { hasMore: boolean; nextCursor: string | null } }> {
	switch (tab) {
		case 'images':
			return page48Reads.getUserPosts(username, 20, cursor, 'image');
		case 'videos':
			return page48Reads.getUserPosts(username, 20, cursor, 'video');
		case 'reposts':
			return page48Reads.getUserReposts(username, 20, cursor);
		case 'replies':
			return page48Reads.getUserReplies(username, 20, cursor);
		case 'likes':
			return page48Reads.getLikes(20, cursor);
		case 'bookmarks':
			return page48Reads.getBookmarks(20, cursor);
		default:
			return page48Reads.getUserPosts(username, 20, cursor);
	}
}

/** The reactive header entry for a username, or an empty placeholder. */
function readProfile(username: string): ProfileEntry {
	return profiles[username] ?? EMPTY_PROFILE;
}

/** The reactive list entry for a profile tab, or an empty placeholder. */
function readList(username: string, tab: Page48ProfileTab): ListEntry {
	return lists[listKey(username, tab)] ?? EMPTY_LIST;
}

/** Load the header once. `force` refetches (used by the retry button). */
async function ensureProfile(username: string, force = false): Promise<void> {
	if (!username) return;
	const existing = profiles[username];
	if (existing?.isLoading) return;
	if (existing?.isLoaded && !force) return;

	if (!profiles[username]) profiles[username] = { ...EMPTY_PROFILE };
	// Read back so we hold the reactive proxy, not the plain object we assigned.
	const entry = profiles[username];
	touch(profileOrder, username);
	evict(profiles, profileOrder, PROFILE_CAP);

	entry.isLoading = true;
	entry.error = null;
	entry.notFound = false;
	try {
		entry.data = await page48Reads.getUserProfile(username);
		entry.isLoaded = true;
		entry.fetchedAt = Date.now();
	} catch (err) {
		const e = err as { status?: number; message?: string };
		if (e?.status === 404) {
			entry.notFound = true;
			entry.isLoaded = true;
		} else {
			entry.error = e?.message ?? 'Failed to load profile';
		}
	} finally {
		entry.isLoading = false;
	}
}

/** Quietly refresh a loaded header. `force` skips the freshness gate (profile entry). */
async function revalidateProfile(username: string, force = false): Promise<void> {
	const entry = profiles[username];
	if (!entry?.isLoaded || entry.isLoading) return;
	if (!force && Date.now() - entry.fetchedAt < REVALIDATE_AFTER_MS) return;
	touch(profileOrder, username);
	try {
		entry.data = await page48Reads.getUserProfile(username);
		entry.fetchedAt = Date.now();
	} catch {
		// Keep the cached header; the next visit tries again.
	}
}

/** Load a tab's first page once. `force` refetches. */
async function ensureList(username: string, tab: Page48ProfileTab, force = false): Promise<void> {
	if (!username) return;
	const key = listKey(username, tab);
	const existing = lists[key];
	if (existing?.isLoading) return;
	if (existing?.isLoaded && !force) return;

	if (!lists[key]) lists[key] = { ...EMPTY_LIST, posts: [] };
	// Read back so we hold the reactive proxy, not the plain object we assigned.
	const entry = lists[key];
	touch(listOrder, key);
	evict(lists, listOrder, LIST_CAP);

	entry.isLoading = true;
	try {
		const response = await fetchTabList(username, tab, null);
		entry.posts = response.data;
		entry.hasMore = response.meta.hasMore;
		entry.nextCursor = response.meta.nextCursor;
		entry.isLoaded = true;
		entry.fetchedAt = Date.now();
	} catch {
		entry.posts = [];
		entry.hasMore = false;
		entry.nextCursor = null;
		entry.isLoaded = true;
	} finally {
		entry.isLoading = false;
	}
}

/**
 * Merge the newest posts on top of a loaded tab (keeping every page already
 * loaded), so a revisit shows new posts without losing a deep scroll. Returns how
 * many posts were prepended.
 */
async function revalidateList(
	username: string,
	tab: Page48ProfileTab,
	force = false
): Promise<number> {
	const key = listKey(username, tab);
	const entry = lists[key];
	if (!entry?.isLoaded || entry.isLoading) return 0;
	if (!force && Date.now() - entry.fetchedAt < REVALIDATE_AFTER_MS) return 0;
	touch(listOrder, key);
	try {
		const response = await fetchTabList(username, tab, null);
		const fresh = response.data;
		const freshIds = new Set(fresh.map((post) => post.postId));
		const prevById = new Map(entry.posts.map((post) => [post.postId, post]));
		// Only these tabs are ordered by the post's own creation time, so only there
		// can "missing from the window" mean "deleted". The others (reposts, likes,
		// bookmarks) are ordered by an interaction time and never drop posts here.
		const timeOrdered =
			tab === 'posts' || tab === 'images' || tab === 'videos' || tab === 'replies';
		// The oldest post inside the refreshed window. Anything newer than it that is
		// missing from the window was deleted (or hidden) and must drop out.
		const windowMin = fresh.length ? Date.parse(fresh[fresh.length - 1].createdAt) : NaN;

		const tail = entry.posts.filter((post) => {
			if (freshIds.has(post.postId)) return false; // replaced by the fresh copy
			if (!timeOrdered) return true;
			const at = Date.parse(post.createdAt);
			if (!Number.isNaN(windowMin) && !Number.isNaN(at) && at >= windowMin) return false;
			return true;
		});

		const added = fresh.filter((post) => !prevById.has(post.postId)).length;
		const removed = entry.posts.length - tail.length - fresh.length + added;
		const edited = fresh.filter((post) => {
			const prev = prevById.get(post.postId);
			return prev && (prev.content !== post.content || prev.updatedAt !== post.updatedAt);
		}).length;

		entry.fetchedAt = Date.now();
		const changed = added + removed + edited;
		if (changed === 0) return 0;

		entry.posts = [...fresh, ...tail];
		return changed;
	} catch {
		return 0;
	}
}

function saveScroll(username: string, tab: Page48ProfileTab, scrollY: number): void {
	const entry = lists[listKey(username, tab)];
	if (entry) entry.scrollY = scrollY;
}

/** Append the next page of a tab, skipping anything already shown. */
async function loadMoreList(username: string, tab: Page48ProfileTab): Promise<void> {
	const entry = lists[listKey(username, tab)];
	if (!entry?.isLoaded || entry.isLoadingMore || !entry.hasMore || !entry.nextCursor) return;

	entry.isLoadingMore = true;
	try {
		const response = await fetchTabList(username, tab, entry.nextCursor);
		const known = new Set(entry.posts.map((post) => post.postId));
		entry.posts = [...entry.posts, ...response.data.filter((post) => !known.has(post.postId))];
		entry.hasMore = response.meta.hasMore;
		entry.nextCursor = response.meta.nextCursor;
	} catch {
		// Keep the cursor; scrolling retries.
	} finally {
		entry.isLoadingMore = false;
	}
}

/** Merge a partial update into a cached header (follow, block, mute). */
function patchProfile(username: string, partial: Partial<Page48UserProfile>): void {
	const entry = profiles[username];
	if (!entry?.data) return;
	entry.data = { ...entry.data, ...partial };
}

/** Put a freshly created post on top of one of the profile's tabs. */
function prependPost(username: string, tab: Page48ProfileTab, post: Page48Post): void {
	const entry = lists[listKey(username, tab)];
	if (!entry || entry.posts.some((p) => p.postId === post.postId)) return;
	entry.posts = [post, ...entry.posts];
}

function removePost(username: string, tab: Page48ProfileTab, postId: string): void {
	const entry = lists[listKey(username, tab)];
	if (!entry) return;
	entry.posts = entry.posts.filter((post) => post.postId !== postId);
}

/** Rebuild a tab's list (e.g. pinning moves one post to the top). */
function updatePosts(
	username: string,
	tab: Page48ProfileTab,
	updater: (posts: Page48Post[]) => Page48Post[]
): void {
	const entry = lists[listKey(username, tab)];
	if (entry) entry.posts = updater(entry.posts);
}

export const page48ProfileStore = {
	readProfile,
	readList,
	ensureProfile,
	revalidateProfile,
	ensureList,
	revalidateList,
	loadMoreList,
	saveScroll,
	patchProfile,
	prependPost,
	removePost,
	updatePosts
};

// A post edited or deleted anywhere must be reflected in every cached tab, not
// just the page it happened on (each page holds its own copy of the post).
if (typeof window !== 'undefined') {
	window.addEventListener('page48:post-updated', (event) => {
		const updated = (event as CustomEvent<Page48Post>).detail;
		if (!updated?.postId) return;
		for (const key of Object.keys(lists)) {
			const list = lists[key];
			if (list.posts.some((post) => post.postId === updated.postId)) {
				list.posts = list.posts.map((post) =>
					post.postId === updated.postId ? { ...post, ...updated } : post
				);
			}
		}
	});

	window.addEventListener('page48:post-deleted', (event) => {
		const postId = (event as CustomEvent<{ postId?: string }>).detail?.postId;
		if (!postId) return;
		for (const key of Object.keys(lists)) {
			const list = lists[key];
			if (list.posts.some((post) => post.postId === postId)) {
				list.posts = list.posts.filter((post) => post.postId !== postId);
			}
		}
	});
}
