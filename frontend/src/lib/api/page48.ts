import { client, API_BASE } from '$lib/apis/client';
import { accessToken } from '$lib/stores/accessToken.svelte';
import { page48NavStore } from '$lib/stores/page48Nav.svelte';
import { getCSRFToken } from '$lib/utils/auth';

export interface Page48ImageRef {
	filename: string;
	width: number;
	height: number;
}

export interface Page48ThreadPostInput {
	content: string;
	images?: Page48ImageRef[];
	videos?: { filename: string; width: number; height: number; duration: number }[];
	poll?: { options: string[] } | null;
	quotedPostId?: string | null;
}

export interface Page48ThreadResponse {
	rootPostId: string;
	posts: Page48Post[];
}

export interface Page48Image {
	filename: string;
	url: string;
	url_medium?: string | null;
	url_small?: string | null;
	blurHash?: string | null;
	width: number;
	height: number;
}

export interface Page48Video {
	filename: string;
	url: string | null;
	width: number;
	height: number;
	duration: number;
}

export interface VideoUploadResponse {
	filename: string;
	url: string | null;
	width: number;
	height: number;
	duration: number;
}

export interface Page48PollOption {
	id: string;
	text: string;
	votes: number;
}

export interface Page48Poll {
	options: Page48PollOption[];
	totalVotes: number;
	endsAt: string;
	isExpired: boolean;
	/** Option picked by the current user, if any. */
	myOptionId: string | null;
}

export interface Page48Post {
	postId: string;
	rootPostId: string | null;
	parentPostId: string | null;
	depth: number;
	replyCount: number;

	userId: string;
	username: string;
	userDisplayName: string;
	userProfilePicture: string | null;
	userProfilePicture_small: string | null;
	userBlurHash: string | null;

	content: string;
	images: Page48Image[];
	videos: Page48Video[];
	tags: string[];
	poll: Page48Poll | null;
	/** How many posts by the same author continue this one as a thread. */
	threadCount: number;

	likesCount: number;
	repostCount: number;
	/** Quotes of this post, counted live; the icon shows it added to reposts. */
	quoteCount: number;
	bookmarksCount: number;

	isEdited: boolean;
	createdAt: string;
	updatedAt: string;

	isLiked: boolean;
	isReposted: boolean;
	isBookmarked: boolean;

	/** Set on a profile page when the author pinned this post (one per user). */
	isPinned?: boolean;

	/** The post this one quotes, if any. Never nested more than one level. */
	quotedPost?: Page48Post | null;
	/** Kept even when the quoted post is gone, so the UI can detect a dangling quote. */
	quotedPostId?: string | null;

	// Populated when the post is returned as a user's repost
	repostedAt?: string | null;
}

export interface Page48UserProfile {
	userId: string;
	name: string;
	username: string;
	bio: string | null;
	profilePicture: string | null;
	profilePicture_medium: string | null;
	profilePicture_small: string | null;
	blurHash: string | null;
	bannerPicture: string | null;
	bannerPicture_medium: string | null;
	bannerPicture_small: string | null;
	bannerBlurHash: string | null;
	postCount: number;
	repostCount: number;
	/** How the signed-in viewer stands with this account. */
	isBlocked: boolean;
	isBlockedBy: boolean;
	isMuted: boolean;
	/** Follower-only account: posts are hidden until a follow is approved. */
	isLocked: boolean;
	/** The viewer's follow request is still waiting for approval. */
	isFollowPending: boolean;
	followerCount: number;
	followingCount: number;
	isFollowing: boolean;
}

export interface ThreadResponse {
	post: Page48Post;
	replies: ThreadResponse[];
}

export interface ToggleResponse {
	status: boolean;
	count: number;
}

export interface BlockResponse {
	isBlocked: boolean;
}

export interface MuteResponse {
	isMuted: boolean;
}

export interface PostPaginationMeta {
	nextCursor: string | null;
	hasMore: boolean;
}

export interface PostPaginationResponse {
	data: Page48Post[];
	meta: PostPaginationMeta;
}

export interface PostUserItem {
	userId: string;
	username: string;
	name: string;
	profilePicture: string | null;
	profilePicture_small: string | null;
	bio: string | null;
	/** Whether the requesting user already follows this account. */
	isFollowing?: boolean;
	/** Whether the requesting user has an unanswered follow request pending. */
	isPending?: boolean;
}

export interface PostUserListResponse {
	data: PostUserItem[];
	meta: PostPaginationMeta;
}

export type Page48NotificationType =
	| 'reply'
	| 'mention'
	| 'follow'
	| 'followRequest'
	| 'followAccepted'
	| 'like'
	| 'repost'
	| 'quote';

export type Page48NotificationTab = 'replies' | 'mentions' | 'likes' | 'reposts' | 'follows';

/** Unread notifications per tab, plus the overall total shown on the bell. */
export interface Page48NotificationCounts extends Record<Page48NotificationTab, number> {
	total: number;
}

/**
 * Only what a notification row shows. The server deliberately skips resolving
 * (and signing) the post's media for it.
 */
export interface Page48NotificationPost {
	postId: string;
	content: string;
	createdAt: string;
}

export interface Page48Notification {
	notificationId: string;
	type: Page48NotificationType;
	isUnread: boolean;
	createdAt: string;
	/** Identity is resolved live by the server, never stored on the notification. */
	actor: PostUserItem;
	/** The post to preview and open; null for follows and deleted posts. */
	post: Page48NotificationPost | null;
}

export interface Page48NotificationPaginationResponse {
	data: Page48Notification[];
	meta: PostPaginationMeta;
}

/** One row of the notifications overview: unread count plus a preview. */
export interface Page48NotificationTabSummary {
	tab: Page48NotificationTab;
	count: number;
	previews: Page48Notification[];
}

export interface Page48NotificationOverview {
	total: number;
	tabs: Page48NotificationTabSummary[];
}

export type Page48SearchTab = 'top' | 'posts' | 'media' | 'users' | 'tags';

/** The overview tab of search: a few people, tags, then the newest posts. */
export interface Page48SearchTopResponse {
	users: PostUserItem[];
	tags: TrendingTag[];
	posts: Page48Post[];
}

export interface FollowResponse {
	isFollowing: boolean;
	/** True when the target is follower-only, so this is a request. */
	isPending: boolean;
	followerCount: number;
}

export interface Page48Settings {
	locked: boolean;
}

export interface PostActivityResponse {
	post: Page48Post;
	quoteCount: number;
	repostCount: number;
	likeCount: number;
	/** Likes are only visible to the author of the post. */
	canViewLikes: boolean;
}

export interface TrendingTag {
	tag: string;
	count: number;
}

export interface TrendingTagsResponse {
	tags: TrendingTag[];
}

export interface ActiveUser {
	userId: string;
	username: string;
	name: string;
	profilePicture: string | null;
	postCount: number;
	lastPostedAt: string | null;
}

export interface ActiveUsersResponse {
	users: ActiveUser[];
}

export type ReportTargetType = 'post' | 'user';
export type ReportReason = 'spam' | 'harassment' | 'inappropriate' | 'other';

export interface ReportCreate {
	targetType: ReportTargetType;
	targetId: string;
	reason: ReportReason;
	note?: string | null;
}

export interface ReportResponse {
	reportId: string;
	targetType: ReportTargetType;
	targetId: string;
	reason: ReportReason;
	note: string | null;
	status: string;
	createdAt: string;
}

export interface AdminReportItem {
	reportId: string;
	targetType: ReportTargetType;
	targetId: string;
	reason: ReportReason;
	note: string | null;
	status: string;
	createdAt: string;
	reporterUserId: string;
	reporterUsername: string | null;
	targetExists: boolean;
	targetUsername: string | null;
	targetDisplayName: string | null;
	targetContent: string | null;
	targetImageCount: number;
	targetProfilePicture: string | null;
}

export interface AdminReportPaginationResponse {
	data: AdminReportItem[];
	meta: {
		nextCursor: string | null;
		hasMore: boolean;
		total: number;
	};
}

function buildCursorQuery(limit: number, cursor: string | null): string {
	const searchParams = new URLSearchParams();
	searchParams.set('limit', limit.toString());
	if (cursor) searchParams.set('cursor', cursor);
	return searchParams.toString();
}

/**
 * Session cache for the list endpoints. It is only read when the current page
 * was reached with the browser back button, so returning to a list (for example
 * from a post's activity page) restores it instead of calling the API again.
 */
const listResponseCache = new Map<string, unknown>();

/** How long after a back/forward navigation a list may be served from cache. */
const HISTORY_NAV_WINDOW_MS = 1500;

/** Drop the cache whenever the content of a list may have changed. */
function clearListResponseCache(): void {
	listResponseCache.clear();
}

async function cachedListGet<T>(url: string, fetcher: () => Promise<T>): Promise<T> {
	const fromHistory = Date.now() - page48NavStore.viaHistoryAt < HISTORY_NAV_WINDOW_MS;
	if (fromHistory) {
		const hit = listResponseCache.get(url);
		if (hit !== undefined) return hit as T;
	}
	const data = await fetcher();
	listResponseCache.set(url, data);
	return data;
}

export const page48Api = {
	getFeed: async (
		limit: number = 20,
		cursor: string | null = null,
		media: 'text' | 'image' | 'video' | null = null,
		following: boolean = false
	): Promise<PostPaginationResponse> => {
		const mediaParam = media ? `&media=${media}` : '';
		const followingParam = following ? '&following=true' : '';
		const url = `/page48/feed?${buildCursorQuery(limit, cursor)}${mediaParam}${followingParam}`;
		return cachedListGet(url, () => client<PostPaginationResponse>(url));
	},

	getPost: async (postId: string): Promise<Page48Post> => {
		return client<Page48Post>(`/page48/posts/${postId}`);
	},

	getThread: async (postId: string): Promise<ThreadResponse> => {
		return client<ThreadResponse>(`/page48/posts/${postId}/thread`);
	},

	getDirectReplies: async (
		postId: string,
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostPaginationResponse> => {
		const url = `/page48/posts/${postId}/replies?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostPaginationResponse>(url));
	},

	getPostActivity: async (postId: string): Promise<PostActivityResponse> => {
		return client<PostActivityResponse>(`/page48/posts/${postId}/activity`);
	},

	getPostQuotes: async (
		postId: string,
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostPaginationResponse> => {
		const url = `/page48/posts/${postId}/quotes?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostPaginationResponse>(url));
	},

	getPostReposts: async (
		postId: string,
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostUserListResponse> => {
		const url = `/page48/posts/${postId}/reposts?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostUserListResponse>(url));
	},

	getPostLikes: async (
		postId: string,
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostUserListResponse> => {
		const url = `/page48/posts/${postId}/likes?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostUserListResponse>(url));
	},

	createPost: async (
		content: string,
		images: Page48ImageRef[] = [],
		videos: { filename: string; width: number; height: number; duration: number }[] = [],
		parentPostId?: string,
		poll?: { options: string[] } | null,
		quotedPostId?: string
	) => {
		clearListResponseCache();
		return client<Page48Post>('/page48/posts', {
			method: 'POST',
			body: { content, images, videos, parentPostId, poll: poll ?? null, quotedPostId }
		});
	},

	votePoll: async (postId: string, optionId: string): Promise<Page48Poll> => {
		return client<Page48Poll>(`/page48/posts/${postId}/poll/vote`, {
			method: 'POST',
			body: { optionId }
		});
	},

	createThread: async (posts: Page48ThreadPostInput[]): Promise<Page48ThreadResponse> => {
		clearListResponseCache();
		return client<Page48ThreadResponse>('/page48/posts/thread', {
			method: 'POST',
			body: { posts }
		});
	},

	uploadVideo: async (
		file: File,
		meta: { width: number; height: number; duration: number },
		onProgress?: (percent: number) => void
	): Promise<VideoUploadResponse> => {
		// Raw XHR (not `client`) because multipart/form-data must keep the browser's
		// boundary, and XHR also gives us upload progress for large files.
		const form = new FormData();
		form.append('file', file, file.name);
		form.append('width', String(Math.round(meta.width) || 0));
		form.append('height', String(Math.round(meta.height) || 0));
		form.append('duration', String(meta.duration || 0));

		return new Promise<VideoUploadResponse>((resolve, reject) => {
			const xhr = new XMLHttpRequest();
			xhr.open('POST', `${API_BASE}/page48/videos`);
			xhr.withCredentials = true;

			const token = accessToken.value;
			if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
			const csrf = getCSRFToken();
			if (csrf) xhr.setRequestHeader('X-CSRF-Token', csrf);

			xhr.upload.onprogress = (e) => {
				if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
			};
			xhr.onload = () => {
				if (xhr.status >= 200 && xhr.status < 300) {
					try {
						resolve(JSON.parse(xhr.responseText) as VideoUploadResponse);
					} catch (err) {
						reject(err);
					}
					return;
				}
				let detail = 'Upload failed';
				try {
					detail = (JSON.parse(xhr.responseText) as { detail?: string })?.detail || detail;
				} catch {
					// keep default detail
				}
				reject({ detail, status: xhr.status });
			};
			xhr.onerror = () => reject({ detail: 'Network error' });
			xhr.send(form);
		});
	},

	deletePost: async (postId: string) => {
		clearListResponseCache();
		return client(`/page48/posts/${postId}`, { method: 'DELETE' });
	},

	editPost: async (postId: string, content: string): Promise<Page48Post> => {
		clearListResponseCache();
		return client<Page48Post>(`/page48/posts/${postId}`, {
			method: 'PATCH',
			body: { content }
		});
	},

	createReport: async (payload: ReportCreate): Promise<ReportResponse> => {
		return client<ReportResponse>('/page48/reports', { method: 'POST', body: { ...payload } });
	},

	getAdminReports: async (
		limit: number = 20,
		cursor: string | null = null,
		targetType: ReportTargetType | null = null
	): Promise<AdminReportPaginationResponse> => {
		const searchParams = new URLSearchParams();
		searchParams.set('limit', limit.toString());
		if (cursor) searchParams.set('cursor', cursor);
		if (targetType) searchParams.set('targetType', targetType);
		return client<AdminReportPaginationResponse>(
			`/page48/admin/reports?${searchParams.toString()}`
		);
	},

	toggleLike: async (postId: string): Promise<ToggleResponse> => {
		return client<ToggleResponse>(`/page48/posts/${postId}/like`, { method: 'POST' });
	},

	toggleRepost: async (postId: string): Promise<ToggleResponse> => {
		return client<ToggleResponse>(`/page48/posts/${postId}/repost`, { method: 'POST' });
	},

	toggleBookmark: async (postId: string): Promise<ToggleResponse> => {
		return client<ToggleResponse>(`/page48/posts/${postId}/bookmark`, { method: 'POST' });
	},

	blockUser: async (username: string): Promise<BlockResponse> => {
		clearListResponseCache();
		return client<BlockResponse>(`/page48/users/${encodeURIComponent(username)}/block`, {
			method: 'POST'
		});
	},

	unblockUser: async (username: string): Promise<BlockResponse> => {
		clearListResponseCache();
		return client<BlockResponse>(`/page48/users/${encodeURIComponent(username)}/block`, {
			method: 'DELETE'
		});
	},

	muteUser: async (username: string): Promise<MuteResponse> => {
		clearListResponseCache();
		return client<MuteResponse>(`/page48/users/${encodeURIComponent(username)}/mute`, {
			method: 'POST'
		});
	},

	unmuteUser: async (username: string): Promise<MuteResponse> => {
		clearListResponseCache();
		return client<MuteResponse>(`/page48/users/${encodeURIComponent(username)}/mute`, {
			method: 'DELETE'
		});
	},

	getBlocks: async (
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostUserListResponse> => {
		const url = `/page48/me/blocks?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostUserListResponse>(url));
	},

	getMutes: async (
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostUserListResponse> => {
		const url = `/page48/me/mutes?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostUserListResponse>(url));
	},

	pinPost: async (postId: string): Promise<Page48Post> => {
		clearListResponseCache();
		return client<Page48Post>(`/page48/posts/${postId}/pin`, { method: 'POST' });
	},

	unpinPost: async (postId: string): Promise<Page48Post> => {
		clearListResponseCache();
		return client<Page48Post>(`/page48/posts/${postId}/pin`, { method: 'DELETE' });
	},

	getNotifications: async (
		tab: Page48NotificationTab = 'replies',
		limit: number = 20,
		cursor: string | null = null
	): Promise<Page48NotificationPaginationResponse> => {
		const searchParams = new URLSearchParams();
		searchParams.set('tab', tab);
		searchParams.set('limit', limit.toString());
		if (cursor) searchParams.set('cursor', cursor);
		return client<Page48NotificationPaginationResponse>(
			`/page48/notifications?${searchParams.toString()}`
		);
	},

	getNotificationCounts: async (): Promise<Page48NotificationCounts> => {
		return client<Page48NotificationCounts>('/page48/notifications/counts');
	},

	getNotificationOverview: async (): Promise<Page48NotificationOverview> => {
		return client<Page48NotificationOverview>('/page48/notifications/overview');
	},

	searchTop: async (query: string): Promise<Page48SearchTopResponse> => {
		return client<Page48SearchTopResponse>(`/page48/search/top?query=${encodeURIComponent(query)}`);
	},

	searchPosts: async (
		query: string,
		tab: 'posts' | 'media',
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostPaginationResponse> => {
		const searchParams = new URLSearchParams();
		searchParams.set('query', query);
		searchParams.set('tab', tab);
		searchParams.set('limit', limit.toString());
		if (cursor) searchParams.set('cursor', cursor);
		return client<PostPaginationResponse>(`/page48/search/posts?${searchParams.toString()}`);
	},

	searchUsers: async (query: string): Promise<PostUserListResponse> => {
		return client<PostUserListResponse>(`/page48/search/users?query=${encodeURIComponent(query)}`);
	},

	searchTags: async (query: string): Promise<TrendingTagsResponse> => {
		return client<TrendingTagsResponse>(`/page48/search/tags?query=${encodeURIComponent(query)}`);
	},

	/** Marks one tab read, so only the tab actually opened loses its unread dot. */
	markNotificationsRead: async (tab: Page48NotificationTab): Promise<{ count: number }> => {
		return client<{ count: number }>(`/page48/notifications/read?tab=${tab}`, {
			method: 'POST'
		});
	},

	getBookmarks: async (
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostPaginationResponse> => {
		const url = `/page48/me/bookmarks?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostPaginationResponse>(url));
	},

	getLikes: async (
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostPaginationResponse> => {
		const url = `/page48/me/likes?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostPaginationResponse>(url));
	},

	getUserProfile: async (username: string): Promise<Page48UserProfile> => {
		return client<Page48UserProfile>(`/page48/users/${encodeURIComponent(username)}/profile`);
	},

	followUser: async (username: string): Promise<FollowResponse> => {
		clearListResponseCache();
		return client<FollowResponse>(`/page48/users/${encodeURIComponent(username)}/follow`, {
			method: 'POST'
		});
	},

	unfollowUser: async (username: string): Promise<FollowResponse> => {
		clearListResponseCache();
		return client<FollowResponse>(`/page48/users/${encodeURIComponent(username)}/follow`, {
			method: 'DELETE'
		});
	},

	acceptFollowRequest: async (username: string): Promise<FollowResponse> => {
		clearListResponseCache();
		return client<FollowResponse>(`/page48/users/${encodeURIComponent(username)}/follow/accept`, {
			method: 'POST'
		});
	},

	declineFollowRequest: async (username: string): Promise<FollowResponse> => {
		clearListResponseCache();
		return client<FollowResponse>(`/page48/users/${encodeURIComponent(username)}/follow/request`, {
			method: 'DELETE'
		});
	},

	updateSettings: async (locked: boolean): Promise<Page48Settings> => {
		clearListResponseCache();
		return client<Page48Settings>('/page48/me/settings', {
			method: 'PATCH',
			body: { locked }
		});
	},

	getFollowers: async (
		username: string,
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostUserListResponse> => {
		const url = `/page48/users/${encodeURIComponent(username)}/followers?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostUserListResponse>(url));
	},

	getFollowing: async (
		username: string,
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostUserListResponse> => {
		const url = `/page48/users/${encodeURIComponent(username)}/following?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostUserListResponse>(url));
	},

	getUserPosts: async (
		username: string,
		limit: number = 20,
		cursor: string | null = null,
		media: 'text' | 'image' | 'video' | null = null
	): Promise<PostPaginationResponse> => {
		const mediaParam = media ? `&media=${media}` : '';
		const url = `/page48/users/${encodeURIComponent(username)}/posts?${buildCursorQuery(limit, cursor)}${mediaParam}`;
		return cachedListGet(url, () => client<PostPaginationResponse>(url));
	},

	getUserReplies: async (
		username: string,
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostPaginationResponse> => {
		const url = `/page48/users/${encodeURIComponent(username)}/replies?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostPaginationResponse>(url));
	},

	getUserReposts: async (
		username: string,
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostPaginationResponse> => {
		const url = `/page48/users/${encodeURIComponent(username)}/reposts?${buildCursorQuery(limit, cursor)}`;
		return cachedListGet(url, () => client<PostPaginationResponse>(url));
	},

	getTrendingTags: async (limit: number = 10): Promise<TrendingTagsResponse> => {
		return client<TrendingTagsResponse>(`/page48/tags/trending?limit=${limit}`);
	},

	getActiveUsers: async (limit: number = 5, days: number = 7): Promise<ActiveUsersResponse> => {
		return client<ActiveUsersResponse>(`/page48/users/active?limit=${limit}&days=${days}`);
	},

	getPostsByTag: async (
		tag: string,
		limit: number = 20,
		cursor: string | null = null,
		media: 'text' | 'image' | 'video' | null = null
	): Promise<PostPaginationResponse> => {
		const mediaParam = media ? `&media=${media}` : '';
		const url = `/page48/tags/${encodeURIComponent(tag)}/posts?${buildCursorQuery(limit, cursor)}${mediaParam}`;
		return cachedListGet(url, () => client<PostPaginationResponse>(url));
	}
};
