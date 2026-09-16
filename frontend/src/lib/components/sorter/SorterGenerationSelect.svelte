<script lang="ts">
	import { Play } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { fade } from 'svelte/transition';
	import type { createSorter } from '$lib/stores/sorter.svelte';
	import type { Member } from '$lib/apis/members';
	import { getTeamColors } from '$lib/constants/teamColors';

	interface Props {
		sorter: ReturnType<typeof createSorter>;
	}

	let { sorter }: Props = $props();

	const { t } = useTranslation();

	function selectAll() {
		if (sorter.filterMode === 'generation') {
			sorter.selectAllGenerations();
		} else {
			sorter.selectAllTeams();
		}
	}

	function deselectAll() {
		if (sorter.filterMode === 'generation') {
			sorter.deselectAllGenerations();
		} else {
			sorter.deselectAllTeams();
		}
	}

	function start() {
		sorter.startSort();
	}

	const selectedMembersCount = $derived(
		sorter.filterMode === 'generation'
			? sorter.allMembers.filter((m: Member) => sorter.selectedGenerations.has(m.generation)).length
			: sorter.allMembers.filter(
					(m: Member) => m.member_type && sorter.selectedTeams.has(m.member_type)
				).length
	);
</script>

<div in:fade={{ duration: 300 }} class="w-full max-w-2xl px-4 space-y-6">
	<div
		class="bg-white dark:bg-zinc-900 rounded-2xl p-6 shadow-md border border-gray-100 dark:border-zinc-800 space-y-6"
	>
		<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
			<div class="flex gap-2 font-black items-center">
				<button
					onclick={() => (sorter.filterMode = 'generation')}
					class={`text-sm cursor-pointer uppercase tracking-widest transition-all hover:scale-105 ${
						sorter.filterMode === 'generation'
							? 'text-red-600'
							: 'text-slate-400 dark:text-zinc-500 hover:text-red-600'
					}`}
				>
					{t('theater.sorter.generation')}
				</button>
				<span class="text-slate-400 dark:text-zinc-500">/</span>
				<button
					onclick={() => (sorter.filterMode = 'team')}
					class={`text-sm cursor-pointer uppercase tracking-widest transition-all hover:scale-105 ${
						sorter.filterMode === 'team'
							? 'text-red-600'
							: 'text-slate-400 dark:text-zinc-500 hover:text-red-600'
					}`}
				>
					{t('theater.sorter.team')}
				</button>
			</div>
			<div class="flex gap-2 font-black items-center sm:justify-end">
				<button
					onclick={selectAll}
					class="text-xs transition-transform cursor-pointer uppercase tracking-widest text-red-600 hover:scale-105"
				>
					{t('theater.sorter.selectAll')}
				</button>
				<span class="text-xs text-slate-300 dark:text-zinc-600">&bull;</span>
				<button
					onclick={deselectAll}
					class="text-xs transition-all cursor-pointer uppercase tracking-widest text-slate-400 dark:text-zinc-500 hover:text-red-600 hover:scale-105"
				>
					{t('theater.sorter.clear')}
				</button>
			</div>
		</div>

		<div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
			{#if sorter.loadingGenerations}
				{#each Array(8)}
					<div class="h-12 bg-slate-50 dark:bg-zinc-800 animate-pulse rounded-2xl"></div>
				{/each}
			{:else if sorter.filterMode === 'generation'}
				{#each sorter.generations as gen}
					<button
						onclick={() => sorter.toggleGeneration(gen)}
						class={`px-4 py-3 rounded-2xl text-sm font-black transition-all border-2 cursor-pointer ${
							sorter.selectedGenerations.has(gen)
								? 'bg-red-600 border-red-600 text-white shadow-md shadow-red-600/20 ring-4 ring-red-600/10'
								: 'bg-white dark:bg-zinc-800 border-gray-50 dark:border-zinc-700 text-slate-500 hover:border-red-600/30 shadow-sm'
						}`}
					>
						{t('theater.sorter.genLabel', { gen })}
					</button>
				{/each}
			{:else}
				{#each sorter.teams as team}
					<button
						onclick={() => sorter.toggleTeam(team)}
						class={`px-4 py-3 rounded-2xl text-sm font-black transition-all border-2 cursor-pointer ${
							sorter.selectedTeams.has(team)
								? 'text-white'
								: 'bg-white dark:bg-zinc-800 border-gray-50 dark:border-zinc-700 text-slate-500 hover:border-[var(--team-color)] shadow-sm'
						}`}
						style={`--team-color: ${getTeamColors(team).badgeBorder}; ${
							sorter.selectedTeams.has(team)
								? `background-color: var(--team-color); border-color: var(--team-color); box-shadow: 0 4px 6px -1px ${getTeamColors(team).badgeBg}33, 0 0 0 4px ${getTeamColors(team).badgeBg}1a;`
								: ''
						}`}
					>
						{team.charAt(0) + team.slice(1).toLowerCase()}
					</button>
				{/each}
			{/if}
		</div>

		<div
			class="flex items-center justify-between pt-6 border-t border-gray-50 dark:border-zinc-800"
		>
			<span class="text-xs font-black uppercase tracking-widest text-slate-400 dark:text-zinc-500"
				>{t('theater.sorter.selectedMembers')}</span
			>
			<div class="flex items-baseline gap-2">
				<span class="font-black text-3xl text-red-600">
					{selectedMembersCount}
				</span>
				<span class="text-[10px] font-black uppercase border-b-2 border-red-600 text-themed"
					>{t('theater.sorter.ready')}</span
				>
			</div>
		</div>
	</div>

	<div class="flex flex-col gap-3 w-full sm:w-80 mx-auto">
		<button
			onclick={start}
			disabled={sorter.loadingGenerations || selectedMembersCount < 2}
			class="w-full h-16 rounded-full font-black text-xl shadow-md hover:-translate-y-1 transition-all duration-300 flex items-center justify-center gap-3 group disabled:opacity-50 disabled:grayscale cursor-pointer bg-red-600 hover:bg-red-700 text-white shadow-red-600/20"
		>
			<Play class="w-6 h-6 fill-current group-hover:translate-x-1 transition-transform" />
			{t('theater.sorter.start')}
		</button>

		{#if sorter.hasSavedProgress}
			<button
				onclick={sorter.resumeSort}
				class="w-full h-12 rounded-full font-bold text-sm bg-white dark:bg-zinc-800 border-2 border-red-600 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-300 flex items-center justify-center cursor-pointer shadow-md"
			>
				{t('theater.sorter.resume') || 'Lanjutkan Sorter Sebelumnya'}
			</button>
		{/if}
	</div>
</div>
