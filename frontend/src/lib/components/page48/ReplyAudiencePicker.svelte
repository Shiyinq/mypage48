<script lang="ts">
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Check } from 'lucide-svelte';
	import { portal } from '$lib/actions/portal';
	import { PAGE48_REPLY_SETTINGS, type Page48ReplySetting } from '$lib/api/page48';
	import { REPLY_AUDIENCE_ICONS } from '$lib/constants/replyAudience';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** Element the panel is anchored to (the composer's reply-audience button). */
		anchor?: HTMLElement;
		value: Page48ReplySetting;
		onSelect: (value: Page48ReplySetting) => void;
		onClose: () => void;
	}

	let { anchor, value, onSelect, onClose }: Props = $props();

	const { t } = useTranslation();

	const PANEL_WIDTH = 340;
	const GAP = 8;

	let panelEl = $state<HTMLDivElement>();
	let panelWidth = $state(PANEL_WIDTH);
	let position = $state({ left: GAP, top: GAP });

	/**
	 * Follow the anchor: the panel is portalled and fixed, so it has to be placed
	 * against the button's current rect every time the page (or a scroller inside
	 * a modal) moves — otherwise it would stay put while the page scrolls.
	 */
	function place() {
		const width = Math.min(PANEL_WIDTH, window.innerWidth - GAP * 2);
		panelWidth = width;
		if (!anchor) {
			position = { left: GAP, top: GAP };
			return;
		}

		const rect = anchor.getBoundingClientRect();
		const height = panelEl?.offsetHeight ?? 0;
		const spaceBelow = window.innerHeight - rect.bottom - GAP;
		const spaceAbove = rect.top - GAP;

		// Below the button by default; flip above only when it would not fit below
		// but does above. Otherwise clamp so the panel stays on screen.
		let top: number;
		if (spaceBelow >= height || spaceAbove < height) {
			top = Math.min(rect.bottom + GAP, window.innerHeight - height - GAP);
		} else {
			top = rect.top - height - GAP;
		}

		position = {
			left: Math.max(GAP, Math.min(rect.left, window.innerWidth - width - GAP)),
			top: Math.max(GAP, top)
		};
	}

	function choose(setting: Page48ReplySetting) {
		onSelect(setting);
		onClose();
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') onClose();
	}

	onMount(() => {
		// Placed once the panel has rendered (so its height is known), then kept in
		// sync with every scroll — including scrollers, via the capture phase.
		requestAnimationFrame(place);
		const onMove = () => place();
		window.addEventListener('scroll', onMove, true);
		window.addEventListener('resize', onMove);
		return () => {
			window.removeEventListener('scroll', onMove, true);
			window.removeEventListener('resize', onMove);
		};
	});
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- Portalled above the composer modal (z-10060) so the panel is not clipped. -->
<div
	use:portal
	class="fixed inset-0 z-[10070]"
	onclick={(event) => {
		if (event.target === event.currentTarget) onClose();
	}}
	role="presentation"
	transition:fade={{ duration: 100 }}
>
	<div
		bind:this={panelEl}
		class="absolute overflow-hidden rounded-2xl border border-gray-200 bg-white p-2 shadow-xl dark:border-zinc-800 dark:bg-zinc-900"
		style={`left:${position.left}px; top:${position.top}px; width:${panelWidth}px;`}
		role="dialog"
		aria-label={t('page48.replyAudience.title')}
	>
		<h3 class="px-3 py-2 text-[17px] font-bold text-gray-900 dark:text-gray-100">
			{t('page48.replyAudience.title')}
		</h3>

		{#each PAGE48_REPLY_SETTINGS as setting (setting)}
			{@const Icon = REPLY_AUDIENCE_ICONS[setting]}
			<button
				type="button"
				class="flex w-full cursor-pointer items-center gap-3 rounded-xl px-3 py-3 text-left transition-colors hover:bg-gray-100 dark:hover:bg-white/10"
				onclick={() => choose(setting)}
				aria-pressed={value === setting}
			>
				<Icon size={22} class="shrink-0 text-gray-900 dark:text-gray-100" />
				<span class="min-w-0 flex-1 text-[15px] font-semibold text-gray-900 dark:text-gray-100">
					{t(`page48.replyAudience.${setting}`)}
				</span>
				{#if value === setting}
					<span
						class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-500 text-white"
					>
						<Check size={15} strokeWidth={3} />
					</span>
				{:else}
					<span class="h-6 w-6 shrink-0 rounded-full border-2 border-gray-300 dark:border-zinc-600"
					></span>
				{/if}
			</button>
		{/each}
	</div>
</div>
