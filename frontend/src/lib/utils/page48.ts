import { page48Api, type Page48Post } from '$lib/api/page48';
import { storageApi } from '$lib/apis/storage';
import { showToast } from '$lib/stores/toast.svelte';
import { t } from '$lib/i18n';

export type Page48Interaction = 'like' | 'repost' | 'bookmark';

export type Page48Media = 'text' | 'image' | 'video';

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

/** Upload a list of files to storage and return their stored filenames. */
export async function uploadPage48Images(files: File[]): Promise<string[]> {
	const filenames: string[] = [];
	for (const file of files) {
		const base64 = await new Promise<string>((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => resolve(reader.result as string);
			reader.onerror = reject;
			reader.readAsDataURL(file);
		});

		const result = await storageApi.uploadImage(base64, 'page48');
		if (result.filename) filenames.push(result.filename);
	}
	return filenames;
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
