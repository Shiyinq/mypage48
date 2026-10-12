<script lang="ts">
	import { loadOnView } from '$lib/actions/loadOnView';
	import { embedPreferences } from '$lib/stores/embed.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { InstagramKind } from '$lib/utils/page48';

	interface Props {
		/** The permalink shortcode, already validated by `extractInstagramEmbed`. */
		shortcode: string;
		/** `p`, `reel` or `tv` — decides which embed path is used. */
		kind: InstagramKind;
		/** Embed height in px. The official iframe has no resize message, so this is fixed. */
		height?: number;
		class?: string;
	}

	let { shortcode, kind, height = 700, class: klass = '' }: Props = $props();

	const { t } = useTranslation();

	/**
	 * "Lite" embed: nothing third-party loads until the viewer clicks, so a feed full
	 * of Instagram links never pays for dozens of iframes (or their tracking) up front.
	 */
	let playing = $state(false);

	// Built from a fixed origin with a validated shortcode, never from user input.
	let embedSrc = $derived(`https://www.instagram.com/${kind}/${shortcode}/embed/`);

	function play(event: MouseEvent) {
		// The card behind the embed is a link; the click must not navigate away.
		event.stopPropagation();
		playing = true;
	}
</script>

<div
	class={`mx-auto w-full max-w-[540px] ${klass}`}
	use:loadOnView={{ enabled: embedPreferences.autoLoad, onLoad: () => (playing = true) }}
>
	<div
		class="relative w-full overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-900"
	>
		{#if playing}
			<iframe
				src={embedSrc}
				title={t('page48.aria.instagramPost')}
				class="block w-full"
				style={`height: ${height}px`}
				allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
				referrerpolicy="strict-origin-when-cross-origin"
				allowfullscreen
			></iframe>
		{:else}
			<button
				type="button"
				class="group/ig flex min-h-[150px] w-full cursor-pointer items-center justify-center gap-3 px-4 py-6 transition-colors hover:bg-gray-50 dark:hover:bg-zinc-800/60"
				onclick={play}
				aria-label={t('page48.embed.viewOnInstagram')}
			>
				<span
					class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-600 text-white transition-transform group-hover/ig:scale-105"
				>
					<svg
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="h-[20px] w-[20px]"
						aria-hidden="true"
					>
						<rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
						<path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
						<line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
					</svg>
				</span>
				<span class="text-left">
					<span class="block text-[14px] font-semibold text-gray-900 dark:text-gray-100">
						{t('page48.embed.viewOnInstagram')}
					</span>
					<span class="block text-[12px] text-gray-500 dark:text-gray-400">
						{t('page48.embed.instagramLoads')}
					</span>
				</span>
			</button>
		{/if}
	</div>
</div>
