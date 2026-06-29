<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import SorterGenerationSelect from '$lib/components/sorter/SorterGenerationSelect.svelte';
	import SorterProcess from '$lib/components/sorter/SorterProcess.svelte';
	import { createSorter } from '$lib/stores/sorter.svelte';

	import { fade } from 'svelte/transition';
	import SorterRankDisplay from '$lib/components/sorter/SorterRankDisplay.svelte';
	import SorterEditableHeader from '$lib/components/sorter/SorterEditableHeader.svelte';
	import { sorterNavbarStore } from '$lib/stores/sorterNavbar.svelte';

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

	// Sync plain data to the navbar store
	$effect(() => {
		sorterNavbarStore.update({
			pageType: 'sorter',
			layoutMode,
			sorterState: sorter.currentState as 'landing' | 'sorting' | 'results',
			numQuestion: sorter.numQuestion,
			onSetLayout: setLayout,
			onShare: shareResults,
			onRestart: restart
		});
		return () => {
			sorterNavbarStore.reset();
		};
	});

	let isNavigating = false;
	let lastState = $state(sorter.currentState);

	$effect(() => {
		const currentPath = $page.url.pathname;
		if (isNavigating) return;

		const basePath = '/jkt48/sorter';

		if (sorter.currentState === 'sorting' && lastState !== 'sorting') {
			if (currentPath !== `${basePath}/sorting`) {
				isNavigating = true;
				goto(`${basePath}/sorting`, { keepFocus: true, noScroll: true }).then(
					() => (isNavigating = false)
				);
			}
		} else if (sorter.currentState === 'results' && lastState !== 'results') {
			if (currentPath !== `${basePath}/results`) {
				isNavigating = true;
				goto(`${basePath}/results`, { keepFocus: true, noScroll: true }).then(
					() => (isNavigating = false)
				);
			}
		} else if (sorter.currentState === 'landing' && lastState !== 'landing') {
			if (currentPath !== basePath) {
				isNavigating = true;
				goto(basePath, { keepFocus: true, noScroll: true }).then(() => (isNavigating = false));
			}
		}

		lastState = sorter.currentState;
	});

	$effect(() => {
		const step = $page.params.step;
		if (!isNavigating) {
			if (!step && sorter.currentState !== 'landing') {
				sorter.restart();
			} else if (step === 'sorting' && sorter.currentState === 'landing') {
				goto('/jkt48/sorter', { replaceState: true, keepFocus: true, noScroll: true });
			}
		}
	});
</script>

<SEO title={t('theater.sorter.title')} path="/jkt48/sorter" description={t('seo.sorter')} />

<div
	class={`w-full flex flex-col items-center justify-start min-h-[calc(100svh-64px)] ${sorter.currentState === 'results' ? 'pt-4 md:pt-6 pb-12' : 'pt-4 md:pt-8 pb-12'}`}
>
	{#if sorter.currentState === 'landing'}
		<div class="text-center mb-6 md:mb-12 px-4 w-full pt-4 md:pt-8 hidden md:block">
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
		<div in:fade={{ duration: 200 }} class="w-full flex flex-col items-center">
			<div
				class={`w-full space-y-8 px-4 sm:px-4 mx-auto pb-24 ${layoutMode === 'list' ? 'max-w-3xl' : 'max-w-6xl'}`}
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
	{/if}
</div>

<style>
</style>
