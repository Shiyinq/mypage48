<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import SorterProcess from '$lib/components/sorter/SorterProcess.svelte';
	import { publicSorter } from '$lib/stores/sorter.svelte';
	import { fade } from 'svelte/transition';
	import SorterRankDisplay from '$lib/components/sorter/SorterRankDisplay.svelte';
	import SorterEditableHeader from '$lib/components/sorter/SorterEditableHeader.svelte';
	import { sorterNavbarStore } from '$lib/stores/sorterNavbar.svelte';

	const { t } = useTranslation();
	const sorter = publicSorter;

	let layoutMode: 'card' | 'list' = $state('card');

	onMount(() => {
		if (sorter.currentState === 'landing') {
			goto('/jkt48/sorter');
		}
	});

	$effect(() => {
		if (sorter.currentState === 'landing') {
			goto('/jkt48/sorter');
		}
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

	// Sync plain data to the navbar store (NO Snippets, NO Symbols)
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
</script>

<SEO title={t('theater.sorter.title')} path="/jkt48/sorter/sorting" description={t('seo.sorter')} />

<div
	class={`w-full flex flex-col items-center justify-start min-h-[calc(100svh-64px)] ${sorter.currentState === 'results' ? 'pt-4 md:pt-6 pb-12' : 'pt-4 md:pt-8 pb-12'}`}
>
	{#if sorter.currentState === 'sorting'}
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
			onexit={restart}
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
