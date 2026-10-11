<script lang="ts">
	import { loadOnView } from '$lib/actions/loadOnView';
	import { embedPreferences } from '$lib/stores/embed.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** The numeric tweet id, already validated by `extractXEmbed`. */
		tweetId: string;
		class?: string;
	}

	let { tweetId, class: klass = '' }: Props = $props();

	const { t } = useTranslation();

	/**
	 * "Lite" embed: nothing third-party loads until the viewer clicks, so a feed full
	 * of X links never pays for dozens of iframes (or their tracking) up front.
	 */
	let playing = $state(false);
	/** The iframe reports its own height; this is the fallback until it does. */
	let frameHeight = $state(280);
	let iframeEl = $state<HTMLIFrameElement | undefined>();
	let theme = $state<'light' | 'dark'>('light');

	// Built from a fixed origin with a validated numeric id, never from user input.
	let embedSrc = $derived(
		`https://platform.twitter.com/embed/Tweet.html?id=${tweetId}&dnt=true&theme=${theme}`
	);

	function play(event: MouseEvent) {
		// The card behind the embed is a link; the click must not navigate away.
		event.stopPropagation();
		if (typeof document !== 'undefined') {
			theme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
		}
		playing = true;
	}

	/** Reads the height out of the embed's resize postMessage, if that is what this is. */
	function readResizeHeight(data: unknown): number | undefined {
		let value: unknown = data;
		if (typeof value === 'string') {
			try {
				value = JSON.parse(value);
			} catch {
				return undefined;
			}
		}

		const embed = (
			value as {
				'twttr.embed'?: { method?: string; params?: Array<{ height?: number }> };
			}
		)?.['twttr.embed'];
		if (embed?.method !== 'twttr.private.resize') return undefined;

		const height = embed.params?.[0]?.height;
		return typeof height === 'number' && height > 0 ? Math.ceil(height) : undefined;
	}

	function handleMessage(event: MessageEvent) {
		// Only messages from the X embed origin, and only from *our* iframe, so several
		// embeds on one page do not resize each other.
		if (event.origin !== 'https://platform.twitter.com') return;
		if (!iframeEl || event.source !== iframeEl.contentWindow) return;

		const height = readResizeHeight(event.data);
		if (height) frameHeight = height;
	}

	$effect(() => {
		if (!playing) return;
		window.addEventListener('message', handleMessage);
		return () => window.removeEventListener('message', handleMessage);
	});
</script>

<div
	class={`relative w-full overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-900 ${klass}`}
	use:loadOnView={{ enabled: embedPreferences.autoLoad, onLoad: () => (playing = true) }}
>
	{#if playing}
		<iframe
			bind:this={iframeEl}
			src={embedSrc}
			title={t('page48.aria.xPost')}
			class="block w-full"
			style={`height: ${frameHeight}px`}
			allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
			referrerpolicy="strict-origin-when-cross-origin"
			allowfullscreen
		></iframe>
	{:else}
		<button
			type="button"
			class="group/x flex min-h-[150px] w-full cursor-pointer items-center justify-center gap-3 px-4 py-6 transition-colors hover:bg-gray-50 dark:hover:bg-zinc-800/60"
			onclick={play}
			aria-label={t('page48.embed.viewOnX')}
		>
			<span
				class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-black text-white transition-transform group-hover/x:scale-105 dark:bg-white dark:text-black"
			>
				<svg viewBox="0 0 24 24" fill="currentColor" class="h-[18px] w-[18px]" aria-hidden="true">
					<path
						d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
					/>
				</svg>
			</span>
			<span class="text-left">
				<span class="block text-[14px] font-semibold text-gray-900 dark:text-gray-100">
					{t('page48.embed.viewOnX')}
				</span>
				<span class="block text-[12px] text-gray-500 dark:text-gray-400">
					{t('page48.embed.xLoads')}
				</span>
			</span>
		</button>
	{/if}
</div>
