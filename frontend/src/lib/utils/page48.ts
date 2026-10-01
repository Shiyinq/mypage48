import { page48Api, type Page48Image, type Page48ImageRef, type Page48Post } from '$lib/api/page48';
import { storageApi } from '$lib/apis/storage';
import { showToast } from '$lib/stores/toast.svelte';
import { locale, t } from '$lib/i18n';
import { getLocaleMap, parseUTCDate } from '$lib/utils/time';

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

/** One post being composed; the composer hands these to the page for publishing. */
export interface PostDraftInput {
	content: string;
	images: File[];
	video: VideoDraft | null;
	poll: { options: string[] } | null;
	/** The post this draft quotes, if any. */
	quotedPostId?: string | null;
}

/** Aspect ratio (width / height) of an image; falls back to 16:9 when unknown. */
export function imageRatio(image: Page48Image): number {
	return image.width && image.height ? image.width / image.height : 16 / 9;
}

/**
 * Fill in dimensions for photos stored before sizes were saved (older posts).
 * Mutates the passed items, so the caller can rely on `imageRatio()` afterwards.
 * Returns a cleanup function for use inside an effect.
 */
export function measureMissingImageSizes(images: Page48Image[]): () => void {
	let cancelled = false;

	for (const image of images) {
		if (image.width && image.height) continue;

		const src = image.url_small || image.url_medium || image.url;
		if (!src) continue;

		const probe = new Image();
		probe.onload = () => {
			if (cancelled || !probe.naturalWidth || !probe.naturalHeight) return;
			image.width = probe.naturalWidth;
			image.height = probe.naturalHeight;
		};
		probe.src = src;
	}

	return () => {
		cancelled = true;
	};
}

/**
 * Box ratio used to size a multi-image strip (its height). The geometric mean of
 * every photo is used, so the strip lands between the narrowest and the widest
 * photo: neither orientation turns into a sliver, and none ends up wider than the
 * strip itself. Each slide still keeps its own ratio at that height.
 */
export function carouselRatio(images: Page48Image[]): number {
	const ratios = images.map(imageRatio).filter((ratio) => ratio > 0);
	if (ratios.length === 0) return 16 / 9;

	const logMean = ratios.reduce((sum, ratio) => sum + Math.log(ratio), 0) / ratios.length;

	return Math.min(Math.max(Math.exp(logMean), 9 / 16), 16 / 9);
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

/** Build a Page48 profile URL. Usernames are stored lower case. */
export function userUrl(username: string): string {
	return `/page48/u/${encodeURIComponent(username.toLowerCase())}`;
}

/** A user the composer can suggest after an `@`. */
export interface MentionCandidate {
	username: string;
	name: string;
	profilePicture?: string | null;
}

/** A run of post content: plain text, a link, a `#hashtag`, or an `@mention`. */
export interface ContentPart {
	text: string;
	link?: string;
	tag?: string;
	mention?: string;
}

/**
 * Matches a link (`http(s)://` or `www.`), a `#hashtag`, or an `@mention` that starts
 * a word (`foo@bar` stays text). Links come first so a `#` or `@` inside a URL is not
 * split off into a tag or a mention.
 */
const CONTENT_PATTERN =
	'(https?:\\/\\/[^\\s<>"\']+|www\\.[^\\s<>"\']+)|#([\\p{L}\\p{N}_]+)|(^|[^\\p{L}\\p{N}_@])@([\\p{L}\\p{N}_]{1,50})';

/** Punctuation that usually trails a link instead of belonging to it. */
const LINK_TRAILING = /[.,!?;:)\]}'"»«”’]+$/;

const USERNAME_CHAR = /[\p{L}\p{N}_]/u;

// Mirrors the backend's `username` field limit.
const MAX_MENTION_LENGTH = 50;

/**
 * Split content into plain text, link, `#hashtag` and `@mention` runs so each can be
 * rendered as a link. `tag`/`mention` are lower-cased for URL building; `text` keeps
 * exactly what the author typed.
 */
export function parseContent(content: string): ContentPart[] {
	const parts: ContentPart[] = [];
	const regex = new RegExp(CONTENT_PATTERN, 'gu');
	let lastIndex = 0;
	let match: RegExpExecArray | null;

	while ((match = regex.exec(content)) !== null) {
		const [full, url, tag, lead, mention] = match;
		// `lead` is the character matched to prove the `@` starts a mention; it
		// belongs to the plain-text run, so the mention itself begins after it.
		const start = match.index + (lead ? lead.length : 0);

		if (start > lastIndex) {
			parts.push({ text: content.slice(lastIndex, start) });
		}
		if (url) {
			// Trailing punctuation stays in the surrounding text, not in the link.
			const link = url.replace(LINK_TRAILING, '');
			parts.push({ text: link, link: linkHref(link) });
			lastIndex = match.index + link.length;
			continue;
		} else if (tag) {
			parts.push({ text: full, tag: tag.toLowerCase() });
		} else if (mention) {
			parts.push({ text: full.slice(lead.length), mention: mention.toLowerCase() });
		}
		lastIndex = match.index + full.length;
	}

	if (lastIndex < content.length) {
		parts.push({ text: content.slice(lastIndex) });
	}
	return parts;
}

/** `www.` links get an explicit scheme so they are real, clickable URLs. */
function linkHref(link: string): string {
	return /^www\./i.test(link) ? `https://${link}` : link;
}

/** A Page48 post link anywhere in `text`, e.g. `https://host/page48/post/<uuid>`. */
const PAGE48_POST_LINK =
	/https?:\/\/\S*?\/page48\/post\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\S*/i;

/**
 * Take the first Page48 post link out of pasted `text`. Returns the post id plus what
 * is left of the text without the link, so pasting a link can become a quote.
 */
export function takeQuotedPostLink(text: string): { postId: string; rest: string } | null {
	const match = text.match(PAGE48_POST_LINK);
	if (!match) return null;

	const rest = text
		.replace(PAGE48_POST_LINK, ' ')
		.replace(/[ \t]{2,}/g, ' ')
		.trim();
	return { postId: match[1].toLowerCase(), rest };
}

/**
 * The `@handle` the caret currently sits inside, or null when no mention is being
 * typed. `end` covers the whole handle so picking replaces all of it even when the
 * caret is in the middle of it.
 */
export function findActiveMention(
	text: string,
	caret: number
): { query: string; start: number; end: number } | null {
	const upTo = text.slice(0, caret);
	const at = upTo.lastIndexOf('@');
	if (at === -1) return null;

	// An `@` glued to a word is an address, not a mention.
	if (at > 0 && USERNAME_CHAR.test(upTo[at - 1])) return null;

	const query = upTo.slice(at + 1);
	if (query.length > MAX_MENTION_LENGTH) return null;
	for (const char of query) {
		if (!USERNAME_CHAR.test(char)) return null;
	}

	let end = caret;
	while (end < text.length && USERNAME_CHAR.test(text[end])) end += 1;

	return { query: query.toLowerCase(), start: at, end };
}

/** Prefix matches on the handle or the display name, handles first. */
export function searchMentionCandidates(
	candidates: MentionCandidate[],
	query: string
): MentionCandidate[] {
	const needle = query.toLowerCase();
	if (!needle) return candidates;

	const byHandle: MentionCandidate[] = [];
	const byName: MentionCandidate[] = [];

	for (const candidate of candidates) {
		if (candidate.username.toLowerCase().startsWith(needle)) {
			byHandle.push(candidate);
		} else if (candidate.name.toLowerCase().includes(needle)) {
			byName.push(candidate);
		}
	}

	return [...byHandle, ...byName];
}

/**
 * Read an image file's natural dimensions before uploading, so the feed knows the
 * right box for it. Falls back to 0 when the browser can't decode the file.
 */
async function probeImage(file: File): Promise<{ width: number; height: number }> {
	if (typeof createImageBitmap === 'function') {
		try {
			const bitmap = await createImageBitmap(file);
			const size = { width: bitmap.width, height: bitmap.height };
			bitmap.close();
			return size;
		} catch {
			// Fall through to the <img> path below.
		}
	}

	return new Promise((resolve) => {
		const url = URL.createObjectURL(file);
		const image = new Image();
		image.onload = () => {
			resolve({ width: image.naturalWidth, height: image.naturalHeight });
			URL.revokeObjectURL(url);
		};
		image.onerror = () => {
			resolve({ width: 0, height: 0 });
			URL.revokeObjectURL(url);
		};
		image.src = url;
	});
}

/** Upload images to storage (limited concurrency); returns references + sizes. */
export async function uploadPage48Images(
	files: File[],
	concurrency = 3
): Promise<Page48ImageRef[]> {
	const uploaded: (Page48ImageRef | null)[] = new Array(files.length).fill(null);
	let next = 0;

	async function worker() {
		while (next < files.length) {
			const index = next++;
			const file = files[index];
			const size = await probeImage(file);

			const base64 = await new Promise<string>((resolve, reject) => {
				const reader = new FileReader();
				reader.onload = () => resolve(reader.result as string);
				reader.onerror = reject;
				reader.readAsDataURL(file);
			});

			const result = await storageApi.uploadImage(base64, 'page48');
			if (result?.filename) {
				uploaded[index] = {
					filename: result.filename,
					width: size.width,
					height: size.height
				};
			}
		}
	}

	const workers = Math.max(1, Math.min(concurrency, files.length));
	await Promise.all(Array.from({ length: workers }, worker));

	// Keep the picked order, dropping anything that failed to upload.
	return uploaded.filter((image): image is Page48ImageRef => image !== null);
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
 * Timestamp shown on a post. While the post is fresh it is relative ("5m", "3j"),
 * then it becomes the calendar date and gains the year once it is not the current
 * one ("1 Oct" / "1 Oct 2025"). A post's own page passes `full` to get the exact
 * time and date instead ("8:31 PM · Oct 1, 2026").
 */
export function formatPostTime(dateStr: string, full = false): string {
	// The API sends UTC without a timezone marker, so it has to be read as UTC for
	// the browser to render it in the viewer's own timezone.
	const date = parseUTCDate(dateStr);
	if (Number.isNaN(date.getTime())) return '';

	const localeName = getLocaleMap(locale.value);

	if (full) {
		const time = new Intl.DateTimeFormat(localeName, {
			hour: 'numeric',
			minute: '2-digit'
		}).format(date);
		const day = new Intl.DateTimeFormat(localeName, {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		}).format(date);
		return `${time} · ${day}`;
	}

	const elapsed = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
	if (elapsed < 86400) {
		if (elapsed < 60) return `${elapsed}${t('page48.time.secondsShort')}`;
		if (elapsed < 3600) return `${Math.floor(elapsed / 60)}${t('page48.time.minutesShort')}`;
		return `${Math.floor(elapsed / 3600)}${t('page48.time.hoursShort')}`;
	}

	// The year is only worth the pixels once it is not the current one.
	const sameYear = date.getFullYear() === new Date().getFullYear();
	return new Intl.DateTimeFormat(localeName, {
		day: 'numeric',
		month: 'short',
		...(sameYear ? {} : { year: 'numeric' })
	}).format(date);
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
	const diff = parseUTCDate(endsAt).getTime() - now;
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
