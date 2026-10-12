<script lang="ts">
	import { Music } from 'lucide-svelte';
	import { loadOnView } from '$lib/actions/loadOnView';
	import { embedPreferences } from '$lib/stores/embed.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { SpotifyKind } from '$lib/utils/page48';

	interface Props {
		/** The 22-character Spotify id, already validated by `extractSpotifyEmbed`. */
		spotifyId: string;
		/** Which resource the id points at; decides the embed path and height. */
		kind: SpotifyKind;
		class?: string;
	}

	let { spotifyId, kind, class: klass = '' }: Props = $props();

	const { t } = useTranslation();

	// Spotify's iframe has a fixed layout per resource type (px). These are the
	// values its own oEmbed returns, and the widget fills the frame at this size.
	const HEIGHTS: Record<SpotifyKind, number> = {
		track: 152,
		episode: 232,
		album: 352,
		playlist: 352,
		artist: 352,
		show: 352
	};

	/**
	 * "Lite" embed: nothing third-party loads until the viewer clicks (or scrolls it
	 * into view when auto-load is on).
	 */
	let playing = $state(false);
	let theme = $state<'light' | 'dark'>('light');

	let height = $derived(HEIGHTS[kind] ?? 352);

	// Built from a fixed origin with a validated id, never from user input.
	let embedSrc = $derived(
		`https://open.spotify.com/embed/${kind}/${spotifyId}?utm_source=generator${
			theme === 'dark' ? '&theme=0' : ''
		}`
	);

	function play(event: MouseEvent) {
		// The card behind the embed is a link; the click must not navigate away.
		event.stopPropagation();
		if (typeof document !== 'undefined') {
			theme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
		}
		playing = true;
	}
</script>

<div
	class={`w-full ${klass}`}
	use:loadOnView={{ enabled: embedPreferences.autoLoad, onLoad: () => (playing = true) }}
>
	{#if playing}
		<!-- Same markup Spotify's own embed snippet uses: width 100% + a fixed
		     `height` attribute, so the widget always fills the exact frame. -->
		<iframe
			src={embedSrc}
			title={t('page48.aria.spotifyEmbed')}
			width="100%"
			{height}
			style="border-radius: 12px"
			class="block w-full"
			allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
			referrerpolicy="strict-origin-when-cross-origin"
			allowfullscreen
		></iframe>
	{:else}
		<button
			type="button"
			class="group/sp flex w-full cursor-pointer items-center justify-center gap-3 rounded-xl bg-[#121212] px-4 text-white transition-colors hover:bg-[#1f1f1f]"
			style={`height: ${height}px`}
			onclick={play}
			aria-label={t('page48.embed.listenOnSpotify')}
		>
			<span
				class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#1DB954] text-black transition-transform group-hover/sp:scale-105"
			>
				<Music size={20} />
			</span>
			<span class="text-left">
				<span class="block text-[14px] font-semibold">{t('page48.embed.listenOnSpotify')}</span>
				<span class="block text-[12px] text-white/60">{t('page48.embed.spotifyLoads')}</span>
			</span>
		</button>
	{/if}
</div>
