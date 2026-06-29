<script lang="ts">
	import { Play } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { fade } from 'svelte/transition';

	const { t } = useTranslation();

	interface Props {
		generations: string[];
		selectedGenerations: Set<string>;
		loadingGenerations: boolean;
		selectedMembersCount: number;
		variant?: 'public' | 'theater';
		ontoggle?: (gen: string) => void;
		onselectAll?: () => void;
		ondeselectAll?: () => void;
		onstart?: () => void;
	}

	let {
		generations,
		selectedGenerations,
		loadingGenerations,
		selectedMembersCount,
		variant = 'public',
		ontoggle,
		onselectAll,
		ondeselectAll,
		onstart
	}: Props = $props();

	function toggleGeneration(gen: string) {
		ontoggle?.(gen);
	}

	function selectAll() {
		onselectAll?.();
	}

	function deselectAll() {
		ondeselectAll?.();
	}

	function start() {
		onstart?.();
	}

	let isPublic = $derived(variant === 'public');
</script>

<div in:fade={{ duration: 300 }} class="w-full max-w-2xl px-4 space-y-6">
	<div
		class={isPublic
			? 'bg-white dark:bg-zinc-900 rounded-2xl p-6 shadow-xl border border-gray-100 dark:border-zinc-800 space-y-6'
			: 'bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-6 shadow-sm transition-all duration-300 space-y-6'}
	>
		<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
			<h3
				class={isPublic
					? 'font-black text-themed uppercase tracking-widest text-sm text-slate-400'
					: 'font-bold text-themed text-lg sm:text-base'}
			>
				{t('theater.sorter.generation')}
			</h3>
			<div class="flex gap-4 font-black items-center sm:justify-end">
				<button
					onclick={selectAll}
					class={`text-xs transition-transform cursor-pointer uppercase tracking-widest ${isPublic ? 'text-red-600 hover:scale-105' : 'text-rose-500 hover:text-rose-600'}`}
				>
					{t('theater.sorter.selectAll')}
				</button>
				{#if !isPublic}
					<span class="text-zinc-300">|</span>
				{/if}
				<button
					onclick={deselectAll}
					class={`text-xs transition-colors cursor-pointer uppercase tracking-widest ${isPublic ? 'text-slate-400 hover:text-themed' : 'text-zinc-400 hover:text-themed'}`}
				>
					{t('theater.sorter.clear')}
				</button>
			</div>
		</div>

		<div
			class={isPublic
				? 'grid grid-cols-2 sm:grid-cols-4 gap-3'
				: 'grid grid-cols-3 sm:grid-cols-4 gap-2'}
		>
			{#if loadingGenerations}
				{#each Array(isPublic ? 8 : 9)}
					<div
						class={isPublic
							? 'h-12 bg-slate-50 dark:bg-zinc-800 animate-pulse rounded-2xl'
							: 'h-10 bg-zinc-100 dark:bg-zinc-800 animate-pulse rounded-xl'}
					></div>
				{/each}
			{:else}
				{#each generations as gen}
					<button
						onclick={() => toggleGeneration(gen)}
						class={`px-4 py-3 rounded-2xl text-sm font-black transition-all border-2 cursor-pointer shadow-sm ${
							selectedGenerations.has(gen)
								? isPublic
									? 'bg-red-600 border-red-600 text-white shadow-lg shadow-red-500/30 ring-4 ring-red-500/10'
									: 'bg-rose-500 border-rose-600 text-white scale-105 shadow-md shadow-rose-500/20'
								: isPublic
									? 'bg-white dark:bg-zinc-800 border-gray-50 dark:border-zinc-700 text-slate-500 hover:border-red-600/30'
									: 'bg-zinc-50 dark:bg-zinc-800 border-zinc-100 dark:border-zinc-700 text-zinc-500 dark:text-zinc-400 hover:border-rose-300'
						}`}
					>
						{t('theater.sorter.genLabel', { gen })}
					</button>
				{/each}
			{/if}
		</div>

		<div
			class={`flex items-center justify-between ${isPublic ? 'pt-6 border-t border-gray-50 dark:border-zinc-800' : 'pt-4 border-t border-zinc-100 dark:border-zinc-800 text-sm text-themed-secondary'}`}
		>
			<span class={isPublic ? 'text-xs font-black uppercase tracking-widest text-slate-400' : ''}
				>{t('theater.sorter.selectedMembers')}</span
			>
			<div class="flex items-baseline gap-2">
				<span class={`font-black text-3xl ${isPublic ? 'text-red-600' : 'text-rose-500'}`}>
					{selectedMembersCount}
				</span>
				<span
					class={isPublic
						? 'text-[10px] font-black uppercase border-b-2 border-red-600'
						: 'text-[10px] font-bold uppercase tracking-widest'}>{t('theater.sorter.ready')}</span
				>
			</div>
		</div>
	</div>

	<button
		onclick={start}
		disabled={loadingGenerations || selectedMembersCount < 2}
		class={`w-full sm:w-80 h-16 rounded-full font-black text-xl shadow-xl hover:-translate-y-1 transition-all duration-300 flex items-center justify-center gap-3 group disabled:opacity-50 disabled:grayscale mx-auto cursor-pointer ${
			isPublic
				? 'bg-red-600 hover:bg-red-700 text-white shadow-red-500/30'
				: 'bg-rose-500 hover:bg-rose-600 text-white shadow-none'
		}`}
	>
		<Play class="w-6 h-6 fill-current group-hover:translate-x-1 transition-transform" />
		{t('theater.sorter.start')}
	</button>
</div>
