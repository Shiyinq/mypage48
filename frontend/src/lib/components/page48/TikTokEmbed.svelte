<script lang="ts">
	import { Music2 } from 'lucide-svelte';
	import { loadOnView } from '$lib/actions/loadOnView';
	import { embedPreferences } from '$lib/stores/embed.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { TikTokKind } from '$lib/utils/page48';

	interface Props {
		/** The numeric post id, already validated by `extractTikTokEmbed`. */
		videoId: string;
		/** `video` uses the Player API; `photo` uses the embed card (it renders slides). */
		kind: TikTokKind;
		/** Width cap in px; the 9:16 box centres instead of stretching on desktop. */
		maxWidth?: number;
		class?: string;
	}

	let { videoId, kind, maxWidth = 340, class: klass = '' }: Props = $props();

	const { t, locale } = useTranslation();

	/**
	 * "Lite" embed: nothing third-party loads until the viewer clicks, so a feed full
	 * of TikTok links never pays for dozens of iframes (or their tracking) up front.
	 */
	let playing = $state(false);

	// Built from a fixed origin with a validated numeric id, never from user input.
	let embedSrc = $derived.by(() => {
		const language = locale.value;
		// TikTok retired /embed/v2 (it answers 503); /embed/v3 is its replacement and
		// renders photo posts (the slideshow card) as well as videos.
		if (kind === 'photo') {
			return `https://www.tiktok.com/embed/v3/${videoId}?lang=${language}`;
		}
		return `https://www.tiktok.com/player/v1/${videoId}?autoplay=0&loop=0&controls=1&progress_bar=1&play_button=1&volume_control=1&fullscreen_button=1&timestamp=1&music_info=0&description=0&rel=0&language=${language}`;
	});

	function play(event: MouseEvent) {
		// The card behind the embed is a link; the click must not navigate away.
		event.stopPropagation();
		playing = true;
	}
</script>

<div
	class={`mx-auto w-full ${klass}`}
	style={`max-width: ${maxWidth}px`}
	use:loadOnView={{ enabled: embedPreferences.autoLoad, onLoad: () => (playing = true) }}
>
	<div
		class="relative w-full overflow-hidden rounded-2xl border border-gray-200 bg-black dark:border-zinc-700"
		style="aspect-ratio: 9 / 16"
	>
		{#if playing}
			<iframe
				src={embedSrc}
				title={t('page48.aria.tiktokPost')}
				class="absolute inset-0 h-full w-full"
				allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
				referrerpolicy="strict-origin-when-cross-origin"
				allowfullscreen
			></iframe>
		{:else}
			<button
				type="button"
				class="group/tt absolute inset-0 flex w-full cursor-pointer flex-col items-center justify-center gap-3 bg-zinc-950 px-4 text-white transition-colors hover:bg-zinc-900"
				onclick={play}
				aria-label={t('page48.embed.viewOnTikTok')}
			>
				<span
					class="flex h-12 w-12 items-center justify-center rounded-full bg-white text-black transition-transform group-hover/tt:scale-105"
				>
					<Music2 size={22} />
				</span>
				<span class="text-left">
					<span class="block text-[14px] font-semibold">
						{t('page48.embed.viewOnTikTok')}
					</span>
					<span class="block text-[12px] text-white/60">
						{t('page48.embed.tiktokLoads')}
					</span>
				</span>
			</button>
		{/if}
	</div>
</div>
