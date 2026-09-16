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

	let isPublic = true;

	let isEditingTitle = $state(false);
	let isEditingSubtitle = $state(false);
	let tempTitle = $state('');
	let tempSubtitle = $state('');

	const TITLE_LIMIT = 50;
	const SUBTITLE_LIMIT = 100;

	function startEditTitle() {
		tempTitle = sorter.resultsTitle;
		isEditingTitle = true;
	}

	function saveTitle() {
		if (tempTitle.trim()) {
			sorter.updateLocalHistoryTitle(
				tempTitle.trim().slice(0, TITLE_LIMIT),
				sorter.resultsDescription
			);
		}
		isEditingTitle = false;
	}

	function cancelTitle() {
		isEditingTitle = false;
	}

	function startEditSubtitle() {
		tempSubtitle = sorter.resultsDescription;
		isEditingSubtitle = true;
	}

	function saveSubtitle() {
		if (tempSubtitle.trim()) {
			sorter.updateLocalHistoryTitle(
				sorter.resultsTitle,
				tempSubtitle.trim().slice(0, SUBTITLE_LIMIT)
			);
		}
		isEditingSubtitle = false;
	}

	function cancelSubtitle() {
		isEditingSubtitle = false;
	}

	function setLayout(mode: 'card' | 'list') {
		layoutMode = mode;
	}

	function shareResults() {
		sorter.shareResults(sorter.resultsTitle, sorter.resultsDescription);
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
							title={sorter.resultsTitle}
							description={sorter.resultsDescription}
							{tempTitle}
							tempDescription={tempSubtitle}
							{isEditingTitle}
							isEditingDescription={isEditingSubtitle}
							placeholderDescription={t('theater.sorter.resultsSubtitle') || 'Subtitle'}
							onTitleChange={(v) => (tempTitle = v)}
							onDescriptionChange={(v) => (tempSubtitle = v)}
							onstartEditTitle={startEditTitle}
							oncancelEditTitle={cancelTitle}
							onsaveTitle={saveTitle}
							onstartEditDescription={startEditSubtitle}
							oncancelEditDescription={cancelSubtitle}
							onsaveDescription={saveSubtitle}
							titleLimit={TITLE_LIMIT}
							descriptionLimit={SUBTITLE_LIMIT}
							filters={sorter.filterMode === 'generation'
								? Array.from(sorter.selectedGenerations).sort((a, b) => parseInt(a) - parseInt(b))
								: Array.from(sorter.selectedTeams).sort()}
						/>
					</div>
				</div>

				<SorterRankDisplay results={sorter.results} {layoutMode} {isPublic} />
			</div>
		</div>
	{/if}
</div>
