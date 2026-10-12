<script lang="ts">
	import { fade } from 'svelte/transition';
	import { portal } from '$lib/actions/portal';
	import type { MentionCandidate } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** Element the panel is anchored to (the composer's textarea). */
		anchor?: HTMLElement;
		items: MentionCandidate[];
		activeIndex: number;
		/** A following-list lookup is in flight (shown when the list is still empty). */
		loading?: boolean;
		onHover: (index: number) => void;
		onPick: (candidate: MentionCandidate) => void;
		onClose: () => void;
	}

	let { anchor, items, activeIndex, loading = false, onHover, onPick, onClose }: Props = $props();

	const { t } = useTranslation();

	const PANEL_WIDTH = 280;
	const GAP = 8;
	const MAX_VISIBLE = 6;
	const ROW_HEIGHT = 52;

	let panelWidth = $state(PANEL_WIDTH);
	let position = $state({ left: GAP, top: GAP });

	// Only an estimate: the panel sizes itself, but it is placed before it renders.
	let estimatedHeight = $derived(
		Math.min(Math.max(items.length, 1), MAX_VISIBLE) * ROW_HEIGHT + GAP
	);

	function place() {
		panelWidth = Math.min(PANEL_WIDTH, window.innerWidth - GAP * 2);
		if (!anchor) {
			position = { left: GAP, top: GAP };
			return;
		}

		const rect = anchor.getBoundingClientRect();
		const height = estimatedHeight;
		// Prefer sitting above the field, like a mention popup should.
		const above = rect.top - height - GAP;
		const top =
			above >= GAP ? above : Math.min(rect.bottom + GAP, window.innerHeight - height - GAP);

		position = {
			left: Math.max(GAP, Math.min(rect.left, window.innerWidth - panelWidth - GAP)),
			top: Math.max(GAP, top)
		};
	}

	// Re-place as the list grows (suggestions from the following list arrive later).
	$effect(() => {
		void items.length;
		void estimatedHeight;
		place();
	});

	function avatarUrl(candidate: MentionCandidate): string {
		if (candidate.profilePicture) return candidate.profilePicture;
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(candidate.name || candidate.username)}&background=fca5a5&color=fff`;
	}
</script>

<!-- Above every other Page48 layer (popovers z-10040, modals z-10060, emoji panel
     z-10070), since this is opened from the composer modal too. -->
<div
	use:portal
	class="fixed inset-0 z-[10080]"
	onclick={(event) => {
		if (event.target === event.currentTarget) onClose();
	}}
	role="presentation"
	transition:fade={{ duration: 80 }}
>
	<div
		class="absolute overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-xl dark:border-zinc-800 dark:bg-zinc-900"
		style={`left:${position.left}px; top:${position.top}px; width:${panelWidth}px;`}
		role="listbox"
		tabindex="-1"
		aria-label={t('page48.aria.mentionSuggestions')}
		onmousedown={(event) => event.preventDefault()}
	>
		{#if items.length === 0}
			<p class="px-4 py-3 text-[13px] text-gray-400 dark:text-gray-500">
				{loading ? t('page48.mentions.searching') : t('page48.mentions.noResults')}
			</p>
		{:else}
			<ul class="overflow-y-auto py-1" style={`max-height:${MAX_VISIBLE * ROW_HEIGHT}px;`}>
				{#each items as item, index (item.username)}
					<li>
						<button
							type="button"
							class={`flex w-full cursor-pointer items-center gap-2.5 px-3 py-2 text-left transition-colors ${
								index === activeIndex
									? 'bg-gray-100 dark:bg-white/10'
									: 'hover:bg-gray-50 dark:hover:bg-white/5'
							}`}
							onmouseenter={() => onHover(index)}
							onclick={() => onPick(item)}
							role="option"
							aria-selected={index === activeIndex}
						>
							<img
								src={avatarUrl(item)}
								alt=""
								class="h-8 w-8 shrink-0 rounded-full bg-gray-100 object-cover dark:bg-zinc-800"
								loading="lazy"
							/>
							<span class="min-w-0 flex-1">
								<span
									class="block truncate text-[14px] font-semibold text-gray-900 dark:text-gray-100"
								>
									{item.name}
								</span>
								<span class="block truncate text-[13px] text-gray-500 dark:text-gray-400">
									@{item.username}
								</span>
							</span>
						</button>
					</li>
				{/each}
			</ul>
		{/if}
	</div>
</div>
