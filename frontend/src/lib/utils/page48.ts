import { page48Api, type Page48Post } from '$lib/api/page48';
import { storageApi } from '$lib/apis/storage';
import { showToast } from '$lib/stores/toast.svelte';
import { t } from '$lib/i18n';

export type Page48Interaction = 'like' | 'repost' | 'bookmark';

export type Page48Media = 'text' | 'image' | 'video';

export const PAGE48_MAX_IMAGES = 10;
export const PAGE48_IMAGE_MAX_BYTES = 3 * 1024 * 1024;
export const PAGE48_VIDEO_MAX_BYTES = 50 * 1024 * 1024;
export const PAGE48_VIDEO_MAX_SECONDS = 60;
export const PAGE48_VIDEO_ALLOWED_TYPES = ['video/mp4', 'video/webm'];

export interface VideoDraft {
	file: File;
	width: number;
	height: number;
	duration: number;
}

/**
 * The media filter currently active, derived from the URL:
 * `/page48/photos` → image, `/page48/videos` → video, or a `?media=` query param.
 */
export function getActiveMedia(pathname: string, search: string): Page48Media | null {
	if (pathname.startsWith('/page48/photos')) return 'image';
	if (pathname.startsWith('/page48/videos')) return 'video';

	const value = new URLSearchParams(search).get('media');
	if (value === 'text' || value === 'image' || value === 'video') return value;
	return null;
}

/** Build a tag-page URL, preserving the active media filter. */
export function tagUrl(tag: string, media?: Page48Media | null): string {
	const base = `/page48/tag/${encodeURIComponent(tag.toLowerCase())}`;
	return media ? `${base}?media=${media}` : base;
}

/** Upload a list of files to storage (limited concurrency) and return filenames. */
export async function uploadPage48Images(files: File[], concurrency = 3): Promise<string[]> {
	const filenames: string[] = new Array(files.length).fill('');
	let next = 0;

	async function worker() {
		while (next < files.length) {
			const index = next++;
			const base64 = await new Promise<string>((resolve, reject) => {
				const reader = new FileReader();
				reader.onload = () => resolve(reader.result as string);
				reader.onerror = reject;
				reader.readAsDataURL(files[index]);
			});

			const result = await storageApi.uploadImage(base64, 'page48');
			filenames[index] = result?.filename ?? '';
		}
	}

	const workers = Math.max(1, Math.min(concurrency, files.length));
	await Promise.all(Array.from({ length: workers }, worker));

	// Keep the picked order, dropping anything that failed to upload.
	return filenames.filter((filename) => filename.length > 0);
}

/**
 * Read a local video file's duration and dimensions before uploading.
 * Client-side only: this is a UX guard, the server enforces the size limit.
 */
export function probeVideo(
	file: File
): Promise<{ duration: number; width: number; height: number }> {
	return new Promise((resolve, reject) => {
		const url = URL.createObjectURL(file);
		const video = document.createElement('video');
		video.preload = 'metadata';
		video.muted = true;

		const finish = () => {
			resolve({ duration: video.duration, width: video.videoWidth, height: video.videoHeight });
			video.removeAttribute('src');
			video.load();
			URL.revokeObjectURL(url);
		};

		video.onloadedmetadata = () => {
			// Some containers (webm / fragmented mp4) report Infinity until seeked.
			if (!Number.isFinite(video.duration)) {
				video.currentTime = 1e101;
				video.ontimeupdate = () => {
					video.ontimeupdate = null;
					finish();
				};
			} else {
				finish();
			}
		};
		video.onerror = () => {
			URL.revokeObjectURL(url);
			reject(new Error('unreadable video'));
		};
		video.src = url;
	});
}

/** Upload a video to Page48 storage; returns its stored reference + metadata. */
export async function uploadPage48Video(
	draft: VideoDraft,
	onProgress?: (percent: number) => void
): Promise<{ filename: string; width: number; height: number; duration: number }> {
	const res = await page48Api.uploadVideo(
		draft.file,
		{ width: draft.width, height: draft.height, duration: draft.duration },
		onProgress
	);
	return {
		filename: res.filename,
		width: res.width || draft.width,
		height: res.height || draft.height,
		duration: res.duration || draft.duration
	};
}

/** Absolute URL to a post's detail page (works in SSR too). */
export function getPostUrl(postId: string): string {
	if (typeof window === 'undefined') return `/page48/post/${postId}`;
	return `${window.location.origin}/page48/post/${postId}`;
}

/**
 * Toggle like/repost/bookmark for a post with an optimistic update.
 * Mutates `post` in place (works with Svelte 5 deep `$state` proxies) and
 * reconciles with the server response, reverting on failure.
 */
export async function togglePostInteraction(
	post: Page48Post,
	action: Page48Interaction
): Promise<void> {
	try {
		if (action === 'like') {
			const was = post.isLiked;
			post.isLiked = !was;
			post.likesCount += was ? -1 : 1;
			try {
				const res = await page48Api.toggleLike(post.postId);
				post.isLiked = res.status;
				post.likesCount = res.count;
			} catch (e) {
				post.isLiked = was;
				post.likesCount += was ? 1 : -1;
				throw e;
			}
			return;
		}

		if (action === 'repost') {
			const was = post.isReposted;
			post.isReposted = !was;
			post.repostCount += was ? -1 : 1;
			try {
				const res = await page48Api.toggleRepost(post.postId);
				post.isReposted = res.status;
				post.repostCount = res.count;
			} catch (e) {
				post.isReposted = was;
				post.repostCount += was ? 1 : -1;
				throw e;
			}
			return;
		}

		const was = post.isBookmarked;
		post.isBookmarked = !was;
		post.bookmarksCount += was ? -1 : 1;
		try {
			const res = await page48Api.toggleBookmark(post.postId);
			post.isBookmarked = res.status;
			post.bookmarksCount = res.count;
		} catch (e) {
			post.isBookmarked = was;
			post.bookmarksCount += was ? 1 : -1;
			throw e;
		}
	} catch {
		showToast(t('page48.error.action'), 'error');
	}
}

export const POLL_MIN_OPTIONS = 2;
export const POLL_MAX_OPTIONS = 6;
export const POLL_MAX_OPTION_LENGTH = 50;

/** Rounded share of the total votes, 0 when nobody voted yet. */
export function pollPercentage(votes: number, totalVotes: number): number {
	if (!totalVotes) return 0;
	return Math.round((votes / totalVotes) * 100);
}

/** "23j 59m" style countdown until a poll closes. */
export function formatPollRemaining(endsAt: string, now: number = Date.now()): string {
	const diff = new Date(endsAt).getTime() - now;
	if (!Number.isFinite(diff) || diff <= 0) return '';

	const hours = Math.floor(diff / 3_600_000);
	const minutes = Math.floor((diff % 3_600_000) / 60_000);
	if (hours > 0)
		return `${hours}${t('page48.time.hoursShort')} ${minutes}${t('page48.time.minutesShort')}`;
	if (minutes > 0) return `${minutes}${t('page48.time.minutesShort')}`;
	return `<${t('page48.time.minutesShort')}`;
}

/**
 * Cast a poll vote with an optimistic update, then reconcile with the server.
 * Mutates `post.poll` in place (works with Svelte 5 deep `$state` proxies).
 */
export async function voteOnPoll(post: Page48Post, optionId: string): Promise<void> {
	const poll = post.poll;
	if (!poll || poll.isExpired || poll.myOptionId) return;

	const snapshot = {
		options: poll.options.map((option) => ({ ...option })),
		totalVotes: poll.totalVotes,
		myOptionId: poll.myOptionId
	};

	poll.myOptionId = optionId;
	const chosen = poll.options.find((option) => option.id === optionId);
	if (chosen) chosen.votes += 1;
	poll.totalVotes += 1;

	try {
		const updated = await page48Api.votePoll(post.postId, optionId);
		poll.options = updated.options;
		poll.totalVotes = updated.totalVotes;
		poll.isExpired = updated.isExpired;
		poll.myOptionId = updated.myOptionId;
	} catch (err: unknown) {
		poll.options = snapshot.options;
		poll.totalVotes = snapshot.totalVotes;
		poll.myOptionId = snapshot.myOptionId;
		const e = err as { detail?: string };
		showToast(e?.detail || t('page48.poll.voteError'), 'error');
	}
}

/** Share a post via the Web Share API, falling back to clipboard copy. */
export async function sharePost(post: Page48Post): Promise<void> {
	const url = getPostUrl(post.postId);
	const text = post.content?.trim()
		? post.content.trim().slice(0, 120)
		: 'Lihat postingan ini di Page48';

	if (typeof navigator !== 'undefined' && navigator.share) {
		try {
			await navigator.share({ title: `${post.userDisplayName} di Page48`, text, url });
			return;
		} catch (err) {
			if (err instanceof DOMException && err.name === 'AbortError') return;
		}
	}

	try {
		await navigator.clipboard.writeText(url);
		showToast(t('page48.error.shareCopied'), 'success');
	} catch {
		showToast(t('page48.error.shareError'), 'error');
	}
}
