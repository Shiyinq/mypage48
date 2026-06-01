<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import SorterGenerationSelect from '$lib/components/sorter/SorterGenerationSelect.svelte';
	import SorterProcess from '$lib/components/sorter/SorterProcess.svelte';
	import SorterResults from '$lib/components/sorter/SorterResults.svelte';
	import SorterHistory from '$lib/components/sorter/SorterHistory.svelte';
	import SorterHistoryDetail from '$lib/components/sorter/SorterHistoryDetail.svelte';
	import { createSorter } from '$lib/stores/sorter.svelte';

	const { t } = useTranslation();
	const sorter = createSorter(t, '/theater/sorter');

	let layoutMode: 'card' | 'list' = $state('card');

	onMount(() => {
		sorter.fetchMembers();
	});
</script>

<SEO
	title={t('theater.sorter.title')}
	path="/theater/sorter"
	description={t('theater.sorter.subtitle')}
/>

<svelte:head>
	<style>
		/* Keep sorter layout roomy without breaking theater layout rhythm */
		:global(.max-w-6xl.mx-auto.p-4.pb-24),
		:global(.max-w-6xl.mx-auto) {
			padding-bottom: 1rem !important;
			max-width: 100% !important;
		}
		:global(.mb-6.flex.flex-col.md\:flex-row) {
			margin-bottom: 1rem !important;
		}
	</style>
</svelte:head>

<div
	class={`w-full flex flex-col items-center justify-start min-h-[calc(100svh-120px)] ${sorter.currentState === 'results' ? 'pt-0 pb-12' : 'pt-0 pb-4 overflow-hidden'}`}
>
	<!-- Sub Navbar for switching between landing and history views -->
	{#if sorter.currentState === 'landing' || sorter.currentState === 'history'}
		<div class="flex items-center justify-center gap-3 sm:gap-4 mb-8">
			<button
				onclick={() => {
					sorter.currentState = 'landing';
				}}
				class={`px-5 py-2.5 rounded-full font-black text-xs uppercase tracking-widest transition-all cursor-pointer ${sorter.currentState === 'landing' ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'bg-white dark:bg-zinc-900 text-zinc-500 border border-zinc-200 dark:border-zinc-800 hover:text-rose-500'}`}
			>
				{t('theater.sorter.startNew') || 'Mulai Sorter'}
			</button>
			<button
				onclick={() => {
					sorter.goToHistory();
				}}
				class={`px-5 py-2.5 rounded-full font-black text-xs uppercase tracking-widest transition-all cursor-pointer ${sorter.currentState === 'history' ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'bg-white dark:bg-zinc-900 text-zinc-500 border border-zinc-200 dark:border-zinc-800 hover:text-rose-500'}`}
			>
				{t('theater.sorter.history') || 'Riwayat Sorter'}
			</button>
		</div>
	{/if}

	{#if sorter.currentState === 'landing'}
		<SorterGenerationSelect
			generations={sorter.generations}
			selectedGenerations={sorter.selectedGenerations}
			loadingGenerations={sorter.loadingGenerations}
			selectedMembersCount={sorter.allMembers.filter((m) =>
				sorter.selectedGenerations.has(m.generation)
			).length}
			ontoggle={sorter.toggleGeneration}
			onselectAll={sorter.selectAllGenerations}
			ondeselectAll={sorter.deselectAllGenerations}
			onstart={sorter.startSort}
			variant="theater"
		/>
	{:else if sorter.currentState === 'sorting'}
		<SorterProcess
			numQuestion={sorter.numQuestion}
			displayProgress={sorter.displayProgress}
			leftMember={sorter.leftMember}
			rightMember={sorter.rightMember}
			isAnimating={sorter.isAnimating}
			lastSelectedSide={sorter.lastSelectedSide}
			hasHistory={sorter.history.length > 0}
			onselect={sorter.handleSelect}
			onundo={sorter.undo}
			onexit={sorter.restart}
			variant="theater"
		/>
	{:else if sorter.currentState === 'results'}
		<SorterResults
			results={sorter.results}
			{layoutMode}
			selectedGenerations={sorter.selectedGenerations}
			onshare={sorter.shareResults}
			onrestart={sorter.restart}
			onchangeLayout={(modeVal: 'card' | 'list') => (layoutMode = modeVal)}
			onsave={sorter.saveCurrentResult}
			variant="theater"
		/>
	{:else if sorter.currentState === 'history'}
		<SorterHistory
			histories={sorter.savedHistories}
			loading={sorter.loadingHistory}
			onview={sorter.viewHistoryDetail}
			ondelete={sorter.deleteSavedHistory}
		/>
	{:else if sorter.currentState === 'history-detail'}
		{#if sorter.selectedHistory}
			<SorterHistoryDetail
				historyItem={sorter.selectedHistory}
				onback={() => {
					sorter.currentState = 'history';
				}}
			/>
		{/if}
	{/if}
</div>

<style>
</style>
