<script lang="ts">
	import { loadOnView } from '$lib/actions/loadOnView';
	import { page48Api } from '$lib/api/page48';
	import { extractTikTokEmbed, type TikTokEmbed as TikTokEmbedData } from '$lib/utils/page48';
	import TikTokEmbed from '$lib/components/page48/TikTokEmbed.svelte';
	import TikTokLinkCard from '$lib/components/page48/TikTokLinkCard.svelte';

	interface Props {
		/** The short link found in the post, e.g. `https://vm.tiktok.com/...`. */
		url: string;
		maxWidth?: number;
		class?: string;
	}

	let { url, maxWidth, class: klass = '' }: Props = $props();

	/** The resolved post, or null while it is still a plain link. */
	let embed = $state<TikTokEmbedData | null>(null);
	let started = $state(false);

	/**
	 * Resolving only talks to our own backend (which follows the redirect), so it is
	 * safe to do as soon as the card is reached. The third-party iframe itself still
	 * respects the auto-load setting inside `TikTokEmbed`.
	 */
	async function resolve() {
		if (started) return;
		started = true;
		try {
			const canonical = await page48Api.resolveShortLink(url);
			embed = extractTikTokEmbed(canonical);
		} catch {
			// Stays a plain link card.
		}
	}
</script>

{#if embed}
	<TikTokEmbed videoId={embed.videoId} kind={embed.kind} {maxWidth} class={klass} />
{:else}
	<div use:loadOnView={{ onLoad: resolve }}>
		<TikTokLinkCard {url} class={klass} />
	</div>
{/if}
