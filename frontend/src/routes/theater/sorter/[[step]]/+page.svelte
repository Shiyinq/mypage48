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
	import { sorterApi } from '$lib/apis/sorter';
	import { sorterNavbarStore } from '$lib/stores/sorterNavbar.svelte';

	const { t } = useTranslation();
	const sorter = createSorter(t, '/theater/sorter');

	let layoutMode: 'card' | 'list' = $state('card');

	onMount(() => {
		sorter.fetchMembers();
	});

	// For inline results
	let isPublic = false;
	let customTitle = $state(t('theater.sorter.results'));
	let customSubtitle = $state(t('theater.sorter.resultsSubtitle'));
	let sortedSelectedGens = $derived(
		[...sorter.selectedGenerations].sort((a, b) => parseInt(a) - parseInt(b))
	);

	let isEditingTitle = $state(false);
	let isEditingSubtitle = $state(false);
	let tempTitle = $state('');
	let tempSubtitle = $state('');
	let isSaving = $state(false);
	let savedHistoryId = $state<string | null>(null);

	const TITLE_LIMIT = 50;
	const SUBTITLE_LIMIT = 100;

	function startEditTitle() {
		tempTitle = customTitle;
		isEditingTitle = true;
	}

	async function saveTitle() {
		if (tempTitle.trim()) {
			customTitle = tempTitle.trim().slice(0, TITLE_LIMIT);
			if (savedHistoryId) {
				isSaving = true;
				try {
					await sorterApi.updateSorterHistory(savedHistoryId, { title: customTitle });
				} catch (e) {
					console.error('Failed to update title', e);
				} finally {
					isSaving = false;
				}
			}
		}
		isEditingTitle = false;
	}

	function cancelTitle() {
		isEditingTitle = false;
	}

	function startEditSubtitle() {
		tempSubtitle = customSubtitle;
		isEditingSubtitle = true;
	}

	async function saveSubtitle() {
		if (tempSubtitle.trim()) {
			customSubtitle = tempSubtitle.trim().slice(0, SUBTITLE_LIMIT);
			if (savedHistoryId) {
				isSaving = true;
				try {
					await sorterApi.updateSorterHistory(savedHistoryId, { description: customSubtitle });
				} catch (e) {
					console.error('Failed to update description', e);
				} finally {
					isSaving = false;
				}
			}
		}
		isEditingSubtitle = false;
	}

	function cancelSubtitle() {
		isEditingSubtitle = false;
	}

	async function saveResults() {
		if (isSaving) return;
		isSaving = true;
		try {
			const saved = await sorter.saveCurrentResult(customTitle, customSubtitle);
			savedHistoryId = saved._id;
		} finally {
			isSaving = false;
		}
	}

	function setLayout(mode: 'card' | 'list') {
		layoutMode = mode;
	}

	function shareResults() {
		sorter.shareResults(customTitle, customSubtitle);
	}

	function restart() {
		savedHistoryId = null;
		customTitle = t('theater.sorter.results');
		customSubtitle = t('theater.sorter.resultsSubtitle');
		sorter.restart();
	}

	// Sync plain data to the navbar store (NO Snippets, NO Symbols)
	$effect(() => {
		sorterNavbarStore.update({
			pageType: 'sorter',
			layoutMode,
			sorterState: sorter.currentState as 'landing' | 'sorting' | 'results',
			numQuestion: sorter.numQuestion,
			isSaving,
			savedHistoryId,
			onSetLayout: setLayout,
			onSave: saveResults,
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

		const basePath = '/theater/sorter';

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
				goto('/theater/sorter', { replaceState: true, keepFocus: true, noScroll: true });
			}
		}
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
	class={`w-full flex flex-col items-center justify-start min-h-[calc(100svh-64px)] ${sorter.currentState === 'results' ? 'pt-4 md:pt-6 pb-12' : 'pt-4 md:pt-8 pb-12'}`}
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
		<div in:fade={{ duration: 200 }} class="w-full flex flex-col items-center">
			<div
				class={`w-full space-y-8 px-4 sm:px-4 mx-auto pb-24 ${layoutMode === 'list' ? 'max-w-3xl' : 'max-w-6xl'}`}
			>
				<div class="flex flex-col md:flex-row md:items-start justify-between gap-4 w-full">
					<div class="flex flex-col gap-2 w-full min-w-0">
						<SorterEditableHeader
							title={customTitle}
							description={customSubtitle}
							{tempTitle}
							tempDescription={tempSubtitle}
							{isEditingTitle}
							isEditingDescription={isEditingSubtitle}
							{isSaving}
							placeholderDescription={t('theater.sorter.resultsSubtitle') || 'Subtitle'}
							onTitleChange={(v) => (tempTitle = v)}
							onDescriptionChange={(v) => (tempSubtitle = v)}
							onstartEditTitle={startEditTitle}
							oncancelEditTitle={cancelTitle}
							onsaveTitle={saveTitle}
							onstartEditDescription={startEditSubtitle}
							oncancelEditDescription={cancelSubtitle}
							onsaveDescription={saveSubtitle}
							filters={sortedSelectedGens}
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
