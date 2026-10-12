<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Clock, Search } from 'lucide-svelte';
	import { portal } from '$lib/actions/portal';
	import {
		EMOJI_CATEGORIES,
		EMOJI_RECENT_KEY,
		EMOJI_RECENT_LIMIT,
		searchEmojis,
		type Emoji
	} from '$lib/constants/emojis';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** Element the panel is anchored to (the composer's emoji button). */
		anchor?: HTMLElement;
		onPick: (char: string) => void;
		onClose: () => void;
	}

	let { anchor, onPick, onClose }: Props = $props();

	const { t } = useTranslation();

	const PANEL_WIDTH = 320;
	const PANEL_HEIGHT = 320;
	const GAP = 8;
	/** The scroll spy ignores scroll events while a tab-triggered scroll runs. */
	const SPY_LOCK_MS = 600;

	let query = $state('');
	let activeTab = $state('recent');
	// Snapshot of the recently used emoji, taken when the panel opens so the list
	// doesn't reshuffle under the pointer while picking.
	let recents = $state<Emoji[]>([]);
	let panelWidth = $state(PANEL_WIDTH);
	let position = $state({ left: GAP, top: GAP });
	let scrollEl = $state<HTMLDivElement>();

	let spyLockedUntil = 0;
	let savedRecents: string[] = [];

	let results = $derived(query.trim() ? searchEmojis(query) : []);

	// Every category is rendered in one continuous list with its own title, and
	// the tab row mirrors it (like X).
	let sections = $derived([
		...(recents.length > 0
			? [{ id: 'recent', label: t('page48.emoji.recent'), emojis: recents }]
			: []),
		...EMOJI_CATEGORIES.map((category) => ({
			id: category.id,
			label: t(`page48.emoji.${category.id}`),
			emojis: category.emojis
		}))
	]);

	let tabs = $derived([
		...(recents.length > 0 ? [{ id: 'recent', label: t('page48.emoji.recent'), icon: '' }] : []),
		...EMOJI_CATEGORIES.map((category) => ({
			id: category.id,
			label: t(`page48.emoji.${category.id}`),
			icon: category.icon
		}))
	]);

	function readRecents(): string[] {
		try {
			const stored: unknown = JSON.parse(localStorage.getItem(EMOJI_RECENT_KEY) ?? '[]');
			return Array.isArray(stored)
				? stored.filter((char): char is string => typeof char === 'string')
				: [];
		} catch {
			return [];
		}
	}

	function toEmojis(chars: string[]): Emoji[] {
		const all = EMOJI_CATEGORIES.flatMap((category) => category.emojis);
		return chars
			.map((char) => all.find((emoji) => emoji.char === char))
			.filter((emoji): emoji is Emoji => !!emoji);
	}

	function pick(emoji: Emoji) {
		onPick(emoji.char);

		// Persist for the next time the panel opens; the open list stays put.
		savedRecents = [emoji.char, ...savedRecents.filter((char) => char !== emoji.char)].slice(
			0,
			EMOJI_RECENT_LIMIT
		);
		try {
			localStorage.setItem(EMOJI_RECENT_KEY, JSON.stringify(savedRecents));
		} catch {
			// Private mode / storage disabled: recents are non-essential.
		}
	}

	function findSection(id: string): HTMLElement | undefined {
		return scrollEl?.querySelector<HTMLElement>(`[data-section="${id}"]`) ?? undefined;
	}

	function scrollToSection(id: string) {
		const section = findSection(id);
		if (!section || !scrollEl) return;

		spyLockedUntil = performance.now() + SPY_LOCK_MS;
		activeTab = id;
		scrollEl.scrollTo({ top: section.offsetTop, behavior: 'smooth' });
	}

	/** Highlight the tab of the section currently at the top of the list. */
	function handleScroll() {
		const container = scrollEl;
		if (!container || query.trim() || performance.now() < spyLockedUntil) return;

		let current = tabs[0]?.id ?? '';
		for (const section of sections) {
			const el = findSection(section.id);
			if (el && el.offsetTop - container.scrollTop <= 2) current = section.id;
		}
		activeTab = current;
	}

	async function selectTab(id: string) {
		// Leaving search mode first, otherwise the list wouldn't have sections.
		query = '';
		activeTab = id;
		await tick();
		scrollToSection(id);
	}

	function place() {
		panelWidth = Math.min(PANEL_WIDTH, window.innerWidth - GAP * 2);
		if (!anchor) {
			position = { left: GAP, top: GAP };
			return;
		}

		const rect = anchor.getBoundingClientRect();
		const above = rect.top - PANEL_HEIGHT - GAP;
		const top =
			above >= GAP ? above : Math.min(rect.bottom + GAP, window.innerHeight - PANEL_HEIGHT - GAP);

		position = {
			left: Math.max(GAP, Math.min(rect.left, window.innerWidth - panelWidth - GAP)),
			top: Math.max(GAP, top)
		};
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') onClose();
	}

	onMount(() => {
		savedRecents = readRecents();
		recents = toEmojis(savedRecents);
		activeTab = recents.length > 0 ? 'recent' : EMOJI_CATEGORIES[0].id;
		place();
	});
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- Sits above the Page48 modals (z-10060): the panel is opened from inside the
     composer modal, and below it the whole panel would hide behind the backdrop. -->
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
		class="absolute flex flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-xl dark:border-zinc-800 dark:bg-zinc-900"
		style={`left:${position.left}px; top:${position.top}px; width:${panelWidth}px; height:${PANEL_HEIGHT}px;`}
		role="dialog"
		aria-label={t('page48.composer.addEmoji')}
	>
		<!-- Search -->
		<div class="flex items-center gap-2 border-b border-gray-100 px-3 py-2 dark:border-zinc-800">
			<Search size={15} class="shrink-0 text-gray-400" />
			<input
				bind:value={query}
				type="text"
				placeholder={t('page48.emoji.search')}
				aria-label={t('page48.emoji.search')}
				class="w-full bg-transparent text-[13px] text-gray-900 outline-none placeholder:text-gray-400 dark:text-gray-100 dark:placeholder:text-gray-500"
			/>
		</div>

		<!-- Continuous list: one titled section per category -->
		<div bind:this={scrollEl} onscroll={handleScroll} class="relative flex-1 overflow-y-auto px-2">
			{#if query.trim()}
				{#if results.length > 0}
					<div class="grid grid-cols-8 gap-0.5 py-1">
						{#each results as emoji (emoji.char)}
							{@render emojiButton(emoji)}
						{/each}
					</div>
				{:else}
					<p class="py-8 text-center text-[13px] text-gray-400 dark:text-gray-500">
						{t('page48.emoji.empty')}
					</p>
				{/if}
			{:else}
				{#each sections as section (section.id)}
					<div data-section={section.id}>
						<h3
							class="sticky top-0 z-10 mt-1 bg-white/95 px-1 py-1 text-[11px] font-semibold tracking-wide text-gray-400 uppercase backdrop-blur-sm dark:bg-zinc-900/95 dark:text-gray-500"
						>
							{section.label}
						</h3>
						<div class="grid grid-cols-8 gap-0.5 pb-1">
							{#each section.emojis as emoji (emoji.char)}
								{@render emojiButton(emoji)}
							{/each}
						</div>
					</div>
				{/each}
			{/if}
		</div>

		<!-- Category tabs -->
		<div
			class="no-scrollbar flex items-center gap-0.5 overflow-x-auto border-t border-gray-100 px-1.5 py-1.5 dark:border-zinc-800"
		>
			{#each tabs as tab (tab.id)}
				<button
					type="button"
					class={`flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg text-[18px] leading-none text-gray-500 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-white/10 ${
						activeTab === tab.id ? 'bg-gray-100 dark:bg-white/10' : ''
					}`}
					onclick={() => selectTab(tab.id)}
					title={tab.label}
					aria-label={tab.label}
					aria-pressed={activeTab === tab.id}
				>
					{#if tab.id === 'recent'}
						<Clock size={16} />
					{:else}
						{tab.icon}
					{/if}
				</button>
			{/each}
		</div>
	</div>
</div>

{#snippet emojiButton(emoji: Emoji)}
	<button
		type="button"
		class="flex h-9 w-9 cursor-pointer items-center justify-center rounded-lg text-[22px] leading-none transition-colors hover:bg-gray-100 dark:hover:bg-white/10"
		onclick={() => pick(emoji)}
		title={emoji.label}
		aria-label={emoji.label}
	>
		{emoji.char}
	</button>
{/snippet}
