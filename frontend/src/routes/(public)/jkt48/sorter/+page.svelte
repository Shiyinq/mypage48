<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import SorterGenerationSelect from '$lib/components/sorter/SorterGenerationSelect.svelte';
	import SorterProcess from '$lib/components/sorter/SorterProcess.svelte';
	import SorterResults from '$lib/components/sorter/SorterResults.svelte';
	import { createSorter } from '$lib/stores/sorter.svelte';
	import { PromoBanner } from '$lib/components/common';

	const { t } = useTranslation();
	const sorter = createSorter(t, '/jkt48/sorter');

	let layoutMode: 'card' | 'list' = $state('card');

	onMount(() => {
		sorter.fetchMembers();
	});
</script>

<SEO title={t('theater.sorter.title')} path="/jkt48/sorter" description={t('seo.sorter')} />

<div
	class="w-full flex flex-col items-center justify-start min-h-[calc(100svh-120px)] pt-4 md:pt-6 pb-12"
>
	{#if sorter.currentState === 'landing'}
		<div class="text-center space-y-4 mb-8">
			<h1
				class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter uppercase mb-3"
			>
				{t('theater.sorter.title')}
			</h1>
			<p
				class="text-base md:text-lg text-slate-500 dark:text-slate-400 font-medium max-w-2xl mx-auto uppercase tracking-widest leading-relaxed"
			>
				{t('theater.sorter.subtitle')}
			</p>
		</div>

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
			variant="public"
		/>

		<PromoBanner
			title={t('theater.sorter.historyFeatures')}
			desc={t('theater.sorter.landingPromo')}
			actionText={t('theater.sorter.loginNow')}
			class="max-w-2xl mt-6 mb-6"
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
			variant="public"
		/>
	{:else if sorter.currentState === 'results'}
		<SorterResults
			results={sorter.results}
			{layoutMode}
			selectedGenerations={sorter.selectedGenerations}
			onshare={sorter.shareResults}
			onrestart={sorter.restart}
			onchangeLayout={(mode: 'card' | 'list') => (layoutMode = mode)}
			variant="public"
		/>
	{/if}
</div>

<style>
</style>
