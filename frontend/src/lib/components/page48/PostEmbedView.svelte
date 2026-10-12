<script lang="ts">
	import { loadOnView } from '$lib/actions/loadOnView';
	import { page48Api } from '$lib/api/page48';
	import { findPostEmbed, type PostEmbed } from '$lib/utils/page48';
	import YouTubeEmbed from '$lib/components/page48/YouTubeEmbed.svelte';
	import XEmbed from '$lib/components/page48/XEmbed.svelte';
	import InstagramEmbed from '$lib/components/page48/InstagramEmbed.svelte';
	import InstagramStoryCard from '$lib/components/page48/InstagramStoryCard.svelte';
	import TikTokEmbed from '$lib/components/page48/TikTokEmbed.svelte';
	import TikTokLinkCard from '$lib/components/page48/TikTokLinkCard.svelte';
	import SpotifyEmbed from '$lib/components/page48/SpotifyEmbed.svelte';
	import SpotifyLinkCard from '$lib/components/page48/SpotifyLinkCard.svelte';
	import TelegramEmbed from '$lib/components/page48/TelegramEmbed.svelte';

	interface Props {
		embed: PostEmbed;
		/** Smaller sizing, used by quoted posts and the composer preview. */
		compact?: boolean;
		class?: string;
	}

	let { embed, compact = false, class: klass = '' }: Props = $props();

	/** A `*-link` embed turns into a real provider embed once the backend answers. */
	let resolved = $state<PostEmbed | null>(null);
	let started = $state(false);

	function resolveShortLink(url: string) {
		if (started) return;
		started = true;
		page48Api
			.resolveShortLink(url)
			.then((canonical) => {
				const parsed = findPostEmbed([{ text: canonical, link: canonical }]);
				// Guard against a resolver answer that is another short link.
				if (parsed && parsed.type !== 'tiktok-link' && parsed.type !== 'spotify-link') {
					resolved = parsed;
				}
			})
			.catch(() => {
				// Stays a plain link card.
			});
	}

	let shown = $derived(resolved ?? embed);
</script>

{#if shown.type === 'youtube'}
	<YouTubeEmbed
		videoId={shown.videoId}
		start={shown.start}
		maxHeight={compact ? 300 : undefined}
		class={klass}
	/>
{:else if shown.type === 'x'}
	<XEmbed tweetId={shown.tweetId} class={klass} />
{:else if shown.type === 'instagram'}
	<InstagramEmbed
		shortcode={shown.shortcode}
		kind={shown.kind}
		height={compact ? 420 : undefined}
		class={klass}
	/>
{:else if shown.type === 'instagram-story'}
	<InstagramStoryCard url={shown.url} class={klass} />
{:else if shown.type === 'tiktok'}
	<TikTokEmbed
		videoId={shown.videoId}
		kind={shown.kind}
		maxWidth={compact ? 280 : undefined}
		class={klass}
	/>
{:else if shown.type === 'spotify'}
	<SpotifyEmbed kind={shown.kind} spotifyId={shown.spotifyId} class={klass} />
{:else if shown.type === 'telegram'}
	<TelegramEmbed channel={shown.channel} messageId={shown.messageId} class={klass} />
{:else if shown.type === 'tiktok-link'}
	{@const linkUrl = shown.url}
	<div use:loadOnView={{ onLoad: () => resolveShortLink(linkUrl) }}>
		<TikTokLinkCard url={linkUrl} class={klass} />
	</div>
{:else if shown.type === 'spotify-link'}
	{@const linkUrl = shown.url}
	<div use:loadOnView={{ onLoad: () => resolveShortLink(linkUrl) }}>
		<SpotifyLinkCard url={linkUrl} class={klass} />
	</div>
{/if}
