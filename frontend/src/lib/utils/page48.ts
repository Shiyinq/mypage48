import {
	page48Api,
	type Page48Image,
	type Page48ImageRef,
	type Page48MediaItem,
	type Page48MediaRef,
	type Page48Post
} from '$lib/api/page48';
import { storageApi } from '$lib/apis/storage';
import { showToast } from '$lib/stores/toast.svelte';
import { locale, t } from '$lib/i18n';
import { getLocaleMap, parseUTCDate } from '$lib/utils/time';

export type Page48Interaction = 'like' | 'repost' | 'bookmark';

export type Page48Media = 'text' | 'image' | 'video';

export const PAGE48_MAX_IMAGES = 10;
// Images and videos mixed, up to this many per post (mirrors the backend).
export const PAGE48_MAX_MEDIA = 10;
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

/** A picked photo, before it is uploaded. */
export interface ImageDraft {
	type: 'image';
	file: File;
}

/** One picked media file, images and videos mixed, in the chosen order. */
export type MediaDraft = ImageDraft | ({ type: 'video' } & VideoDraft);

/** One post being composed; the composer hands these to the page for publishing. */
export interface PostDraftInput {
	content: string;
	/** Ordered media picked for this post (images and videos mixed). */
	media: MediaDraft[];
	poll: { options: string[] } | null;
	/** The post this draft quotes, if any. */
	quotedPostId?: string | null;
	/** Hide this post's content behind a spoiler gate until the reader opts in. */
	isSpoiler?: boolean;
	/** Media already on the post, kept unless removed (edit mode). */
	existingMedia?: Page48MediaItem[];
}

/** Upload every picked file and return the ordered refs the API expects. */
export async function uploadDraftMedia(media: MediaDraft[]): Promise<Page48MediaRef[]> {
	const refs: Page48MediaRef[] = [];
	for (const item of media) {
		if (item.type === 'video') {
			const uploaded = await uploadPage48Video(item);
			refs.push({
				type: 'video',
				filename: uploaded.filename,
				width: uploaded.width,
				height: uploaded.height,
				duration: uploaded.duration
			});
		} else {
			const [uploaded] = await uploadPage48Images([item.file]);
			refs.push({
				type: 'image',
				filename: uploaded.filename,
				width: uploaded.width,
				height: uploaded.height
			});
		}
	}
	return refs;
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

/** A run of post content: plain text, a link, a `#hashtag`, an `@mention` or a spoiler. */
export interface ContentPart {
	text: string;
	link?: string;
	tag?: string;
	mention?: string;
	/** Inline `||spoiler||` run: hidden until the reader taps it. */
	spoiler?: boolean;
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

/** Inline spoilers, e.g. `||the twist||`. */
const SPOILER_PATTERN = /\|\|([\s\S]+?)\|\|/g;

/**
 * Split content into plain text, link, `#hashtag`, `@mention` and inline `||spoiler||`
 * runs. Spoilers are pulled out first so a `#`/`@`/URL inside one is not turned into a
 * link; the rest of the text is parsed as before.
 */
export function parseContent(content: string): ContentPart[] {
	const parts: ContentPart[] = [];
	const regex = new RegExp(SPOILER_PATTERN.source, 'gu');
	let lastIndex = 0;
	let match: RegExpExecArray | null;

	while ((match = regex.exec(content)) !== null) {
		if (match.index > lastIndex) {
			parts.push(...parsePlainRuns(content.slice(lastIndex, match.index)));
		}
		parts.push({ text: match[1], spoiler: true });
		lastIndex = match.index + match[0].length;
	}

	if (lastIndex < content.length) {
		parts.push(...parsePlainRuns(content.slice(lastIndex)));
	}
	return parts;
}

/**
 * Split a spoiler-free run into plain text, link, `#hashtag` and `@mention` parts.
 * `tag`/`mention` are lower-cased for URL building; `text` keeps what the author typed.
 */
function parsePlainRuns(content: string): ContentPart[] {
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

/** A YouTube video the feed can embed inline. */
export interface YouTubeEmbed {
	videoId: string;
	/** Playback offset in seconds, taken from `?t=`/`?start=`. */
	start?: number;
}

/**
 * Matches the many shapes of a YouTube URL and captures the 11-character video id:
 * `watch?v=`, `youtu.be/`, `/shorts/`, `/embed/`, `/live/` and `/v/`. Extra query
 * parameters (playlists, share tokens, timestamps) are ignored. The leading
 * `//` keeps lookalike hosts such as `notyoutube.com` from matching.
 */
const YOUTUBE_ID_PATTERN =
	/(?:^|\/\/)(?:www\.|m\.|music\.)?(?:youtube(?:-nocookie)?\.com\/(?:watch\?(?:[^#\s]*&)?v=|shorts\/|embed\/|live\/|v\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/i;

/**
 * Reads the playback offset from `t`/`start`, accepting both `90` and the `1m30s`
 * form YouTube puts in share links. Returns undefined when there is no offset.
 */
function youTubeStartSeconds(url: string): number | undefined {
	const match = url.match(/[?&#](?:t|start)=([0-9hms]+)/i);
	if (!match) return undefined;

	const value = match[1].toLowerCase();
	if (/^\d+$/.test(value)) {
		const seconds = parseInt(value, 10);
		return seconds > 0 ? seconds : undefined;
	}

	let seconds = 0;
	for (const part of value.match(/(\d+[hms])/g) ?? []) {
		const unit = part.slice(-1);
		const amount = parseInt(part, 10);
		if (unit === 'h') seconds += amount * 3600;
		else if (unit === 'm') seconds += amount * 60;
		else seconds += amount;
	}
	return seconds > 0 ? seconds : undefined;
}

/** The video id inside a YouTube link, or null for any other URL. */
export function extractYouTubeEmbed(url: string): YouTubeEmbed | null {
	const match = url.match(YOUTUBE_ID_PATTERN);
	if (!match) return null;
	return { videoId: match[1], start: youTubeStartSeconds(url) };
}

/** An embedded X (Twitter) post. */
export interface XEmbed {
	tweetId: string;
}

/**
 * Matches an X/Twitter status URL and captures the numeric tweet id. Covers the
 * `x.com` and `twitter.com` hosts (with `www.`/`mobile.` subdomains) and the
 * `i/web/status` form. The id length is bounded so the pattern stays linear, and
 * the leading `//` keeps lookalike hosts such as `evil-x.com` from matching.
 */
const X_ID_PATTERN =
	/(?:^|\/\/)(?:www\.|mobile\.)?(?:twitter|x)\.com\/(?:[A-Za-z0-9_]+\/status(?:es)?|i\/web\/status)\/(\d{1,20})/i;

/** The tweet id inside an X/Twitter link, or null for any other URL. */
export function extractXEmbed(url: string): XEmbed | null {
	const match = url.match(X_ID_PATTERN);
	if (!match) return null;
	return { tweetId: match[1] };
}

/** A kind of Instagram permalink that the official `/embed` iframe accepts. */
export type InstagramKind = 'p' | 'reel' | 'tv';

/** An embeddable Instagram post, reel or IGTV video. */
export interface InstagramEmbed {
	shortcode: string;
	kind: InstagramKind;
}

/**
 * Matches an Instagram post/reel/tv permalink and captures its shortcode. The
 * leading `//` keeps lookalike hosts such as `notinstagram.com` from matching.
 * Profiles and stories have no embed endpoint and are handled separately.
 */
const INSTAGRAM_POST_PATTERN =
	/(?:^|\/\/)(?:www\.)?instagram\.com\/(p|reel|reels|tv)\/([A-Za-z0-9_-]{5,20})/i;

/** The shortcode inside an Instagram post link, or null for any other URL. */
export function extractInstagramEmbed(url: string): InstagramEmbed | null {
	const match = url.match(INSTAGRAM_POST_PATTERN);
	if (!match) return null;
	return {
		kind: match[1].toLowerCase() === 'reels' ? 'reel' : (match[1].toLowerCase() as InstagramKind),
		shortcode: match[2]
	};
}

/**
 * An Instagram story. Stories are ephemeral and have no official embed endpoint,
 * so this is only used to render a link card that opens the story on Instagram.
 */
export interface InstagramStory {
	url: string;
}

const INSTAGRAM_STORY_PATTERN =
	/(?:^|\/\/)(?:www\.)?instagram\.com\/stories\/(?:highlights\/)?([A-Za-z0-9_.]{1,30})\/(\d{1,25})/i;

/** A normalised link to an Instagram story, or null for any other URL. */
export function extractInstagramStory(url: string): InstagramStory | null {
	const match = url.match(INSTAGRAM_STORY_PATTERN);
	if (!match) return null;
	return { url: `https://www.instagram.com/stories/${match[1]}/${match[2]}/` };
}

/** A kind of TikTok post the player can render. */
export type TikTokKind = 'video' | 'photo';

/** An embeddable TikTok video or photo post. */
export interface TikTokEmbed {
	videoId: string;
	kind: TikTokKind;
}

/**
 * Matches a TikTok video/photo permalink and captures the numeric id. The leading
 * `//` keeps lookalike hosts such as `nottiktok.com` from matching. Share links
 * (`vm.tiktok.com/...`) carry no id and are handled by `extractTikTokLink`.
 */
const TIKTOK_POST_PATTERN =
	/(?:^|\/\/)(?:www\.|m\.)?tiktok\.com\/@[A-Za-z0-9_.]{1,30}\/(video|photo)\/(\d{6,25})/i;

/** The id and kind inside a TikTok permalink, or null for any other URL. */
export function extractTikTokEmbed(url: string): TikTokEmbed | null {
	const match = url.match(TIKTOK_POST_PATTERN);
	if (!match) return null;
	return { kind: match[1].toLowerCase() as TikTokKind, videoId: match[2] };
}

/**
 * A TikTok share link. It only carries an opaque code, so the video id cannot be
 * resolved from the browser (CORS blocks the redirect); this becomes a link card.
 */
export interface TikTokLink {
	url: string;
}

const TIKTOK_SHORT_PATTERN =
	/(?:^|\/\/)(?:(?:vm|vt)\.tiktok\.com\/[A-Za-z0-9]{4,20}|(?:www\.)?tiktok\.com\/t\/[A-Za-z0-9]{4,20})/i;

/** The cleaned share link, or null for any other URL. */
export function extractTikTokLink(url: string): TikTokLink | null {
	if (!TIKTOK_SHORT_PATTERN.test(url)) return null;
	return { url };
}

/** A kind of Spotify resource the embed player accepts. */
export type SpotifyKind = 'track' | 'album' | 'playlist' | 'episode' | 'artist' | 'show';

/** An embeddable Spotify track, album, playlist, episode, artist or show. */
export interface SpotifyEmbed {
	kind: SpotifyKind;
	spotifyId: string;
}

/**
 * Matches an `open.spotify.com` permalink (with an optional `intl-xx` region
 * prefix) and captures the 22-character id. The leading `//` keeps lookalike
 * hosts such as `notspotify.com` from matching.
 */
const SPOTIFY_ID_PATTERN =
	/(?:^|\/\/)(?:open\.)?spotify\.com\/(?:intl-[a-z]{2}\/)?(track|album|playlist|episode|artist|show)\/([A-Za-z0-9]{22})/i;

/** The kind and id inside a Spotify permalink, or null for any other URL. */
export function extractSpotifyEmbed(url: string): SpotifyEmbed | null {
	const match = url.match(SPOTIFY_ID_PATTERN);
	if (!match) return null;
	return { kind: match[1].toLowerCase() as SpotifyKind, spotifyId: match[2] };
}

/**
 * A Spotify share link (`spotify.link/...`). Like the TikTok one, it carries no
 * id; the backend resolver turns it into a canonical `open.spotify.com` URL.
 */
export interface SpotifyLink {
	url: string;
}

const SPOTIFY_SHORT_PATTERN = /(?:^|\/\/)spotify\.link\/[A-Za-z0-9]{4,30}/i;

/** The cleaned share link, or null for any other URL. */
export function extractSpotifyLink(url: string): SpotifyLink | null {
	if (!SPOTIFY_SHORT_PATTERN.test(url)) return null;
	return { url };
}

/** An embeddable public Telegram channel post. */
export interface TelegramEmbed {
	channel: string;
	messageId: string;
}

/**
 * Matches a public Telegram channel post (`t.me/<channel>/<id>`, with an optional
 * `/s/` preview prefix or the `telegram.me` host) and captures the channel and
 * message id. The leading `//` keeps lookalike hosts such as `nott.me` out, and
 * the 5-32 channel length skips `t.me/c/<id>` private links.
 */
const TELEGRAM_PATTERN =
	/(?:^|\/\/)(?:t\.me|telegram\.me)\/(?:s\/)?([A-Za-z0-9_]{5,32})\/(\d{1,12})/i;

/** The channel and message id inside a Telegram link, or null for any other URL. */
export function extractTelegramEmbed(url: string): TelegramEmbed | null {
	const match = url.match(TELEGRAM_PATTERN);
	if (!match) return null;
	return { channel: match[1], messageId: match[2] };
}

/** An embeddable (or link-card) link found in a post: one per post, first wins. */
export type PostEmbed =
	| ({ type: 'youtube' } & YouTubeEmbed)
	| ({ type: 'x' } & XEmbed)
	| ({ type: 'instagram' } & InstagramEmbed)
	| ({ type: 'instagram-story' } & InstagramStory)
	| ({ type: 'tiktok' } & TikTokEmbed)
	| ({ type: 'tiktok-link' } & TikTokLink)
	| ({ type: 'spotify' } & SpotifyEmbed)
	| ({ type: 'spotify-link' } & SpotifyLink)
	| ({ type: 'telegram' } & TelegramEmbed);

/**
 * The first embeddable link among already-parsed content parts. Only one embed is
 * shown per post, matching how a link preview behaves elsewhere.
 */
export function findPostEmbed(parts: ContentPart[]): PostEmbed | null {
	for (const part of parts) {
		if (!part.link) continue;

		const youtube = extractYouTubeEmbed(part.link);
		if (youtube) return { type: 'youtube', ...youtube };

		const x = extractXEmbed(part.link);
		if (x) return { type: 'x', ...x };

		const instagram = extractInstagramEmbed(part.link);
		if (instagram) return { type: 'instagram', ...instagram };

		const story = extractInstagramStory(part.link);
		if (story) return { type: 'instagram-story', ...story };

		const tiktok = extractTikTokEmbed(part.link);
		if (tiktok) return { type: 'tiktok', ...tiktok };

		const tiktokLink = extractTikTokLink(part.link);
		if (tiktokLink) return { type: 'tiktok-link', ...tiktokLink };

		const spotify = extractSpotifyEmbed(part.link);
		if (spotify) return { type: 'spotify', ...spotify };

		const spotifyLink = extractSpotifyLink(part.link);
		if (spotifyLink) return { type: 'spotify-link', ...spotifyLink };

		const telegram = extractTelegramEmbed(part.link);
		if (telegram) return { type: 'telegram', ...telegram };
	}
	return null;
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
