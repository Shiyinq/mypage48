import { client, API_BASE } from '$lib/apis/client';
import { accessToken } from '$lib/stores/accessToken.svelte';
import { getCSRFToken } from '$lib/utils/auth';

export interface Page48ImageRef {
	filename: string;
	width: number;
	height: number;
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

	likesCount: number;
	repostCount: number;
	bookmarksCount: number;

	isEdited: boolean;
	createdAt: string;
	updatedAt: string;

	isLiked: boolean;
	isReposted: boolean;
	isBookmarked: boolean;

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
	postCount: number;
	repostCount: number;
}

export interface ThreadResponse {
	post: Page48Post;
	replies: ThreadResponse[];
}

export interface ToggleResponse {
	status: boolean;
	count: number;
}

export interface PostPaginationMeta {
	nextCursor: string | null;
	hasMore: boolean;
}

export interface PostPaginationResponse {
	data: Page48Post[];
	meta: PostPaginationMeta;
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

export const page48Api = {
	getFeed: async (
		limit: number = 20,
		cursor: string | null = null,
		media: 'text' | 'image' | 'video' | null = null
	): Promise<PostPaginationResponse> => {
		const mediaParam = media ? `&media=${media}` : '';
		return client<PostPaginationResponse>(
			`/page48/feed?${buildCursorQuery(limit, cursor)}${mediaParam}`
		);
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
		return client<PostPaginationResponse>(
			`/page48/posts/${postId}/replies?${buildCursorQuery(limit, cursor)}`
		);
	},

	createPost: async (
		content: string,
		images: Page48ImageRef[] = [],
		videos: { filename: string; width: number; height: number; duration: number }[] = [],
		parentPostId?: string,
		poll?: { options: string[] } | null
	) => {
		return client<Page48Post>('/page48/posts', {
			method: 'POST',
			body: { content, images, videos, parentPostId, poll: poll ?? null }
		});
	},

	votePoll: async (postId: string, optionId: string): Promise<Page48Poll> => {
		return client<Page48Poll>(`/page48/posts/${postId}/poll/vote`, {
			method: 'POST',
			body: { optionId }
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
		return client(`/page48/posts/${postId}`, { method: 'DELETE' });
	},

	editPost: async (postId: string, content: string): Promise<Page48Post> => {
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

	getBookmarks: async (
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostPaginationResponse> => {
		return client<PostPaginationResponse>(
			`/page48/me/bookmarks?${buildCursorQuery(limit, cursor)}`
		);
	},

	getLikes: async (
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostPaginationResponse> => {
		return client<PostPaginationResponse>(`/page48/me/likes?${buildCursorQuery(limit, cursor)}`);
	},

	getUserProfile: async (username: string): Promise<Page48UserProfile> => {
		return client<Page48UserProfile>(`/page48/users/${encodeURIComponent(username)}/profile`);
	},

	getUserPosts: async (
		username: string,
		limit: number = 20,
		cursor: string | null = null,
		media: 'text' | 'image' | 'video' | null = null
	): Promise<PostPaginationResponse> => {
		const mediaParam = media ? `&media=${media}` : '';
		return client<PostPaginationResponse>(
			`/page48/users/${encodeURIComponent(username)}/posts?${buildCursorQuery(limit, cursor)}${mediaParam}`
		);
	},

	getUserReplies: async (
		username: string,
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostPaginationResponse> => {
		return client<PostPaginationResponse>(
			`/page48/users/${encodeURIComponent(username)}/replies?${buildCursorQuery(limit, cursor)}`
		);
	},

	getUserReposts: async (
		username: string,
		limit: number = 20,
		cursor: string | null = null
	): Promise<PostPaginationResponse> => {
		return client<PostPaginationResponse>(
			`/page48/users/${encodeURIComponent(username)}/reposts?${buildCursorQuery(limit, cursor)}`
		);
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
		return client<PostPaginationResponse>(
			`/page48/tags/${encodeURIComponent(tag)}/posts?${buildCursorQuery(limit, cursor)}${mediaParam}`
		);
	}
};
