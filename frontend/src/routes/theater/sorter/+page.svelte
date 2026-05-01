<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import SorterGenerationSelect from '$lib/components/sorter/SorterGenerationSelect.svelte';
	import SorterProcess from '$lib/components/sorter/SorterProcess.svelte';
	import SorterResults from '$lib/components/sorter/SorterResults.svelte';
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
			onshare={sorter.shareResults}
			onrestart={sorter.restart}
			onchangeLayout={(modeVal) => (layoutMode = modeVal)}
			variant="theater"
		/>
	{/if}
</div>

<style>
</style>
