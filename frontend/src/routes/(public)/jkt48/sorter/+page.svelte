<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import SorterGenerationSelect from '$lib/components/sorter/SorterGenerationSelect.svelte';
	import SorterProcess from '$lib/components/sorter/SorterProcess.svelte';
	import SorterResults from '$lib/components/sorter/SorterResults.svelte';
	import { createSorter } from '$lib/stores/sorter.svelte';

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

		<div
			class="w-full max-w-2xl bg-gradient-to-r from-red-500/10 via-pink-500/5 to-transparent border border-red-200/50 dark:border-red-900/30 rounded-3xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm mt-6 text-left"
		>
			<div class="space-y-1">
				<h4
					class="font-black text-red-600 dark:text-red-400 text-sm sm:text-base tracking-tight uppercase"
				>
					🔒 {t('theater.sorter.historyFeatures')}
				</h4>
				<p class="text-xs font-semibold text-slate-500 dark:text-zinc-400 leading-relaxed max-w-md">
					{t('theater.sorter.landingPromo')}
				</p>
			</div>
			<a
				href="/register"
				class="px-5 py-2.5 rounded-full bg-red-600 hover:bg-red-700 text-white font-black text-xs uppercase tracking-widest text-center shadow-lg shadow-red-500/20 hover:shadow-red-500/30 hover:-translate-y-0.5 transition-all shrink-0 cursor-pointer"
			>
				{t('theater.sorter.loginNow')}
			</a>
		</div>
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
