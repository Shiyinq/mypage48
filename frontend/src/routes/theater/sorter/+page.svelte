<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import SorterGenerationSelect from '$lib/components/sorter/SorterGenerationSelect.svelte';
	import SorterProcess from '$lib/components/sorter/SorterProcess.svelte';
	import { createSorter } from '$lib/stores/sorter.svelte';
	import { isImmersive } from '$lib/stores';

	import { ChevronLeft, LayoutGrid, List, Share2, RotateCcw, Save, Check } from 'lucide-svelte';
	import { fade } from 'svelte/transition';
	import SorterRankDisplay from '$lib/components/sorter/SorterRankDisplay.svelte';
	import SorterEditableHeader from '$lib/components/sorter/SorterEditableHeader.svelte';
	import { sorterApi } from '$lib/apis/sorter';

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
		<div
			class="fixed inset-0 bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 flex flex-col overflow-hidden z-[40]"
			in:fade
		>
			<!-- Dedicated Top Navbar -->
			<div
				class="absolute top-0 left-0 right-0 h-16 border-b border-black/5 dark:border-white/5 bg-white/60 dark:bg-zinc-950/60 backdrop-blur-xl flex items-center justify-between px-4 z-50 shrink-0"
			>
				<div class="flex items-center gap-4">
					<button
						onclick={restart}
						class="flex items-center gap-2 text-slate-900 dark:text-white hover:text-red-600 dark:hover:text-red-400 transition-colors bg-transparent border-none p-0 cursor-pointer font-bold"
					>
						<ChevronLeft size={20} />
						<span class="font-extrabold tracking-tight text-lg"
							>Oshi <span class="text-rose-500 italic">Sorter</span></span
						>
					</button>
					<div class="hidden sm:h-4 sm:w-px sm:bg-gray-200 sm:dark:border-zinc-800"></div>
					<div
						class="hidden xs:flex items-center gap-2 px-3 py-1 rounded-full bg-rose-50 dark:bg-rose-500/10"
					>
						<span
							class="text-[10px] font-black uppercase tracking-widest text-rose-500 dark:text-rose-400"
							>{t('theater.sorter.results')}</span
						>
					</div>
				</div>

				<div class="flex items-center gap-2 sm:gap-3">
					<div
						class="flex bg-gray-50/50 dark:bg-zinc-800/30 backdrop-blur-md rounded-full p-1 border shadow-inner border-zinc-200 dark:border-zinc-800"
					>
						<button
							onclick={() => setLayout('card')}
							class={`p-1.5 rounded-full transition-all cursor-pointer ${layoutMode === 'card' ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}
							title={t('theater.sorter.gridView')}
						>
							<LayoutGrid size={16} />
						</button>
						<button
							onclick={() => setLayout('list')}
							class={`p-1.5 rounded-full transition-all cursor-pointer ${layoutMode === 'list' ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}
							title={t('theater.sorter.listView')}
						>
							<List size={16} />
						</button>
					</div>

					{#if !savedHistoryId}
						<button
							onclick={saveResults}
							disabled={isSaving}
							class="w-8 h-8 bg-green-600 hover:bg-green-700 text-white font-black rounded-full transition-all shadow-lg flex items-center justify-center cursor-pointer disabled:opacity-50"
							title={t('theater.sorter.save') || 'Save Results'}
						>
							{#if isSaving}
								<div
									class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"
								></div>
							{:else}
								<Save size={14} />
							{/if}
						</button>
					{:else}
						<div
							class="w-8 h-8 bg-green-500/20 text-green-600 dark:text-green-400 font-black rounded-full flex items-center justify-center cursor-default"
							title={t('theater.sorter.saveSuccess') || 'Tersimpan'}
						>
							<Check size={14} />
						</div>
					{/if}

					<button
						onclick={shareResults}
						class="w-8 h-8 text-white font-black rounded-full transition-all shadow-lg flex items-center justify-center cursor-pointer bg-rose-500 hover:bg-rose-600 shadow-rose-500/20"
						title={t('theater.sorter.share')}
					>
						<Share2 size={14} />
					</button>
					<button
						onclick={restart}
						class="w-8 h-8 bg-white dark:bg-zinc-800 font-black rounded-full transition-all shadow-md border flex items-center justify-center cursor-pointer text-themed border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-700"
						title={t('theater.sorter.restart')}
					>
						<RotateCcw size={14} />
					</button>
				</div>
			</div>

			<!-- Scrollable content area -->
			<div
				class="flex-1 overflow-y-auto px-4 pt-20 sm:pt-24 pb-8 sm:pb-8 flex flex-col items-center"
			>
				<div
					class={`w-full space-y-8 px-1.5 sm:px-4 mx-auto pb-24 ${layoutMode === 'list' ? 'max-w-3xl' : 'max-w-6xl'}`}
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
		</div>
	{/if}
</div>

<style>
</style>
