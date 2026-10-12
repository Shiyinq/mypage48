<script lang="ts">
	import { Send } from 'lucide-svelte';
	import { loadOnView } from '$lib/actions/loadOnView';
	import { embedPreferences } from '$lib/stores/embed.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** Public channel handle, already validated by `extractTelegramEmbed`. */
		channel: string;
		/** Numeric message id, already validated by `extractTelegramEmbed`. */
		messageId: string;
		class?: string;
	}

	let { channel, messageId, class: klass = '' }: Props = $props();

	const { t } = useTranslation();

	// The embed page reports its own height from these origins via postMessage.
	const EMBED_ORIGINS = ['https://t.me', 'https://post.tg.dev'];

	/**
	 * "Lite" embed: nothing third-party loads until the viewer clicks (or scrolls it
	 * into view when auto-load is on).
	 */
	let playing = $state(false);
	/** The post reports its height; this is the fallback until it does. */
	let frameHeight = $state(240);
	let iframeEl = $state<HTMLIFrameElement | undefined>();

	// Built from a fixed origin with a validated channel/id, never from user input.
	let embedSrc = $derived(`https://t.me/${channel}/${messageId}?embed=1`);

	function play(event: MouseEvent) {
		// The card behind the embed is a link; the click must not navigate away.
		event.stopPropagation();
		playing = true;
	}

	function handleMessage(event: MessageEvent) {
		// Only messages from the Telegram embed origin, and only from *our* iframe, so
		// several embeds on one page do not resize each other.
		if (!EMBED_ORIGINS.includes(event.origin)) return;
		if (!iframeEl || event.source !== iframeEl.contentWindow) return;

		let value: unknown = event.data;
		if (typeof value === 'string') {
			try {
				value = JSON.parse(value);
			} catch {
				return;
			}
		}

		const data = value as { event?: string; height?: number };
		if (data?.event === 'resize' && typeof data.height === 'number' && data.height > 0) {
			frameHeight = Math.ceil(data.height);
		}
	}

	$effect(() => {
		if (!playing) return;
		window.addEventListener('message', handleMessage);
		return () => window.removeEventListener('message', handleMessage);
	});
</script>

<div
	class={`w-full ${klass}`}
	use:loadOnView={{ enabled: embedPreferences.autoLoad, onLoad: () => (playing = true) }}
>
	{#if playing}
		<iframe
			bind:this={iframeEl}
			src={embedSrc}
			title={t('page48.aria.telegramPost')}
			class="block w-full"
			style={`height: ${frameHeight}px`}
			allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
			referrerpolicy="strict-origin-when-cross-origin"
			allowfullscreen
		></iframe>
	{:else}
		<button
			type="button"
			class="group/tg flex min-h-[140px] w-full cursor-pointer items-center justify-center gap-3 rounded-2xl border border-gray-200 bg-white px-4 py-6 transition-colors hover:bg-gray-50 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:bg-zinc-800/60"
			onclick={play}
			aria-label={t('page48.embed.viewOnTelegram')}
		>
			<span
				class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#229ED9] text-white transition-transform group-hover/tg:scale-105"
			>
				<Send size={18} />
			</span>
			<span class="text-left">
				<span class="block text-[14px] font-semibold text-gray-900 dark:text-gray-100">
					{t('page48.embed.viewOnTelegram')}
				</span>
				<span class="block text-[12px] text-gray-500 dark:text-gray-400">
					{t('page48.embed.telegramLoads')}
				</span>
			</span>
		</button>
	{/if}
</div>
