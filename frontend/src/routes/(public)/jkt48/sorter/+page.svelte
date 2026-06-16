<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import SorterGenerationSelect from '$lib/components/sorter/SorterGenerationSelect.svelte';
	import SorterProcess from '$lib/components/sorter/SorterProcess.svelte';
	import { createSorter } from '$lib/stores/sorter.svelte';
	import { PromoBanner } from '$lib/components/common';
	import { isImmersive } from '$lib/stores';

	import { ChevronLeft, LayoutGrid, List, Share2, RotateCcw } from 'lucide-svelte';
	import { fade } from 'svelte/transition';
	import SorterRankDisplay from '$lib/components/sorter/SorterRankDisplay.svelte';
	import SorterEditableHeader from '$lib/components/sorter/SorterEditableHeader.svelte';

	const { t } = useTranslation();
	const sorter = createSorter(t, '/jkt48/sorter');

	let layoutMode: 'card' | 'list' = $state('card');

	onMount(() => {
		sorter.fetchMembers();
	});

	// For inline results
	let isPublic = true;
	let customTitle = $state(t('theater.sorter.results'));
	let customSubtitle = $state(t('theater.sorter.resultsSubtitle'));
	let sortedSelectedGens = $derived(
		[...sorter.selectedGenerations].sort((a, b) => parseInt(a) - parseInt(b))
	);

	function setLayout(mode: 'card' | 'list') {
		layoutMode = mode;
	}

	function shareResults() {
		sorter.shareResults(customTitle, customSubtitle);
	}

	function restart() {
		sorter.restart();
	}

	$effect(() => {
		if (sorter.currentState === 'results' || sorter.currentState === 'sorting') {
			isImmersive.set(true);
			if (typeof window !== 'undefined') {
				document.body.style.overflow = 'hidden';
			}
		} else {
			isImmersive.set(false);
			if (typeof window !== 'undefined') {
				document.body.style.overflow = '';
			}
		}
	});

	onDestroy(() => {
		isImmersive.set(false);
		if (typeof window !== 'undefined') {
			document.body.style.overflow = '';
		}
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
		<div
			class="fixed inset-0 bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 flex flex-col overflow-hidden z-[40]"
			in:fade
		>
			<!-- Dedicated Top Navbar -->
			<div
				class="h-14 border-b border-gray-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md flex items-center justify-between px-4 z-50 shrink-0"
			>
				<div class="flex items-center gap-4">
					<button
						onclick={restart}
						class="flex items-center gap-2 text-slate-900 dark:text-white hover:text-red-600 dark:hover:text-red-400 transition-colors bg-transparent border-none p-0 cursor-pointer font-bold"
					>
						<ChevronLeft size={20} />
						<span class="font-black tracking-tighter text-lg"
							>Oshi <span class="text-red-600 italic">Sorter</span></span
						>
					</button>
					<div class="hidden sm:h-4 sm:w-px sm:bg-gray-200 sm:dark:border-zinc-800"></div>
					<div
						class="hidden xs:flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 dark:bg-red-500/10"
					>
						<span
							class="text-[10px] font-black uppercase tracking-widest text-red-600 dark:text-red-400"
							>{t('theater.sorter.results')}</span
						>
					</div>
				</div>

				<div class="flex items-center gap-2 sm:gap-3">
					<div
						class="flex bg-gray-50/50 dark:bg-zinc-800/30 backdrop-blur-md rounded-full p-1 border shadow-inner border-gray-200 dark:border-zinc-800"
					>
						<button
							onclick={() => setLayout('card')}
							class={`p-1.5 rounded-full transition-all cursor-pointer ${layoutMode === 'card' ? 'bg-red-600 text-white shadow-lg shadow-red-500/20' : 'text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}
							title={t('theater.sorter.gridView')}
						>
							<LayoutGrid size={16} />
						</button>
						<button
							onclick={() => setLayout('list')}
							class={`p-1.5 rounded-full transition-all cursor-pointer ${layoutMode === 'list' ? 'bg-red-600 text-white shadow-lg shadow-red-500/20' : 'text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}
							title={t('theater.sorter.listView')}
						>
							<List size={16} />
						</button>
					</div>

					<button
						onclick={shareResults}
						class="w-8 h-8 text-white font-black rounded-full transition-all shadow-lg flex items-center justify-center cursor-pointer bg-red-600 hover:bg-red-700 shadow-red-500/20"
						title={t('theater.sorter.share')}
					>
						<Share2 size={14} />
					</button>
					<button
						onclick={restart}
						class="w-8 h-8 bg-white dark:bg-zinc-800 font-black rounded-full transition-all shadow-md border flex items-center justify-center cursor-pointer text-slate-900 dark:text-white border-gray-200 dark:border-zinc-700 hover:bg-slate-50 dark:hover:bg-zinc-700"
						title={t('theater.sorter.restart')}
					>
						<RotateCcw size={14} />
					</button>
				</div>
			</div>

			<!-- Scrollable content area -->
			<div class="flex-1 overflow-y-auto px-4 py-8 flex flex-col items-center">
				<div
					class={`w-full space-y-8 px-1.5 sm:px-4 mx-auto pb-24 ${layoutMode === 'list' ? 'max-w-3xl' : 'max-w-6xl'}`}
				>
					<div class="flex flex-col md:flex-row md:items-start justify-between gap-4 w-full">
						<div class="flex flex-col gap-2 w-full min-w-0">
							<SorterEditableHeader
								title={customTitle}
								description={customSubtitle}
								tempTitle=""
								tempDescription=""
								isEditingTitle={false}
								isEditingDescription={false}
								filters={sortedSelectedGens}
								hideEdit={true}
							/>
						</div>
					</div>

					<SorterRankDisplay results={sorter.results} {layoutMode} {isPublic} />
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
</style>
