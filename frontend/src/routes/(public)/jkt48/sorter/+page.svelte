<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { Member } from '$lib/apis/members';
	import { membersStore } from '$lib/stores/theater';
	import { showToast } from '$lib/stores';
	import { fade } from 'svelte/transition';
	import SEO from '$lib/components/SEO.svelte';
	import SorterGenerationSelect from '$lib/components/sorter/SorterGenerationSelect.svelte';
	import SorterProcess from '$lib/components/sorter/SorterProcess.svelte';
	import SorterResults from '$lib/components/sorter/SorterResults.svelte';

	const { t } = useTranslation();

	// Sorter State
	type SorterState = 'landing' | 'sorting' | 'results';
	let currentState: SorterState = $state('landing');

	let allMembers: Member[] = $state([]);
	let selectedMembers: Member[] = $state([]);
	let generations: string[] = $state([]);
	let selectedGenerations: Set<string> = $state(new Set());
	let loadingGenerations = $state(true);

	// Sorting Logic State
	let lstMember: any[] = $state([]);
	let parent: number[] = [];
	let rec: number[] = [];
	let cmp1 = $state(0);
	let cmp2 = $state(0);
	let head1 = $state(0);
	let head2 = $state(0);
	let nrec = 0;
	let numQuestion = $state(0);
	let finishSize = $state(0);
	let finishFlag = $state(0);

	// Results
	interface ResultMember extends Member {
		rank: number;
	}
	let results: ResultMember[] = $state([]);
	let layoutMode: 'card' | 'list' = $state('card');

	// History for Undo
	let history: any[] = $state([]);

	// Animation State
	let isAnimating = $state(false);
	let lastSelectedSide: 'left' | 'right' | 'tie' | null = $state(null);

	async function handleSelect(flag: number) {
		if (isAnimating) return;

		lastSelectedSide = flag === 1 ? 'left' : flag === -1 ? 'right' : 'tie';
		isAnimating = true;

		// Wait for animation to play
		await new Promise((resolve) => setTimeout(resolve, 450));

		sortList(flag);

		isAnimating = false;
		lastSelectedSide = null;
	}

	async function fetchMembers() {
		try {
			await membersStore.load({ limit: 100 }, true);
			allMembers = $membersStore.list;
			const gens = await membersStore.getGenerations();
			generations = gens.sort((a, b) => parseInt(a) - parseInt(b));
			selectedGenerations = new Set();
		} catch (e) {
			showToast($t('theater.members.errorTitle') || 'Failed to load members', 'error');
		} finally {
			loadingGenerations = false;
		}
	}

	function toggleGeneration(gen: string) {
		if (selectedGenerations.has(gen)) {
			selectedGenerations.delete(gen);
		} else {
			selectedGenerations.add(gen);
		}
		selectedGenerations = selectedGenerations;
	}

	function selectAllGenerations() {
		selectedGenerations = new Set(generations);
	}

	function deselectAllGenerations() {
		selectedGenerations = new Set();
	}

	function startSort() {
		selectedMembers = allMembers.filter((m) => selectedGenerations.has(m.generation));
		if (selectedMembers.length < 2) {
			showToast($t('theater.sorter.minSelection'), 'error');
			return;
		}
		selectedMembers = [...selectedMembers].sort(() => Math.random() - 0.5);
		lstMember = selectedMembers.map((_, i) => [i]);
		parent = [];
		rec = [];
		nrec = 0;
		numQuestion = 1;
		cmp1 = 0;
		cmp2 = 1;
		head1 = 0;
		head2 = 0;
		finishSize = 0;
		finishFlag = 0;
		history = [];
		currentState = 'sorting';
	}

	function saveHistory() {
		history = [
			...history,
			JSON.parse(
				JSON.stringify({
					lstMember,
					parent,
					rec,
					cmp1,
					cmp2,
					head1,
					head2,
					nrec,
					numQuestion,
					finishSize,
					finishFlag
				})
			)
		];
		if (history.length > 30) history = history.slice(1);
	}

	function undo() {
		if (history.length === 0) return;
		const last = history[history.length - 1];
		history = history.slice(0, -1);
		lstMember = last.lstMember;
		parent = last.parent;
		rec = last.rec;
		cmp1 = last.cmp1;
		cmp2 = last.cmp2;
		head1 = last.head1;
		head2 = last.head2;
		nrec = last.nrec;
		numQuestion = last.numQuestion;
		finishSize = last.finishSize;
		finishFlag = last.finishFlag;
	}

	function sortList(flag: number) {
		saveHistory();
		if (flag === 1) {
			rec[nrec] = lstMember[cmp1][head1];
			head1++;
			nrec++;
			finishSize++;
		} else if (flag === -1) {
			rec[nrec] = lstMember[cmp2][head2];
			head2++;
			nrec++;
			finishSize++;
		} else {
			rec[nrec] = lstMember[cmp1][head1];
			head1++;
			nrec++;
			finishSize++;
			rec[nrec] = lstMember[cmp2][head2];
			head2++;
			nrec++;
			finishSize++;
		}

		if (head1 < lstMember[cmp1].length && head2 < lstMember[cmp2].length) {
			numQuestion++;
		} else {
			while (head1 < lstMember[cmp1].length) {
				rec[nrec] = lstMember[cmp1][head1];
				head1++;
				nrec++;
				finishSize++;
			}
			while (head2 < lstMember[cmp2].length) {
				rec[nrec] = lstMember[cmp2][head2];
				head2++;
				nrec++;
				finishSize++;
			}
			lstMember.splice(cmp1, 2, [...rec]);
			cmp1 = cmp1 + 1;
			cmp2 = cmp1 + 1;
			head1 = 0;
			head2 = 0;
			rec = [];
			nrec = 0;
			if (cmp1 >= lstMember.length - 1) {
				if (lstMember.length === 1) {
					finishFlag = 1;
					showResults();
					return;
				}
				cmp1 = 0;
				cmp2 = 1;
			}
			numQuestion++;
		}
	}

	function showResults() {
		const finalOrder = lstMember[0];
		results = finalOrder.map((idx: number, i: number) => ({
			...selectedMembers[idx],
			rank: i + 1
		}));
		currentState = 'results';
	}

	function restart() {
		currentState = 'landing';
		history = [];
	}

	onMount(() => {
		fetchMembers();
	});

	let leftMember = $derived(selectedMembers[lstMember[cmp1]?.[head1]]);
	let rightMember = $derived(selectedMembers[lstMember[cmp2]?.[head2]]);
	let progress = $derived(
		finishFlag
			? 100
			: Math.floor(
					(finishSize / (selectedMembers.length * Math.log2(selectedMembers.length) * 0.7)) * 100
				)
	);
	let displayProgress = $derived(Math.min(progress, 99));

	async function copyToClipboard(text: string): Promise<boolean> {
		try {
			if (navigator.clipboard?.writeText) {
				await navigator.clipboard.writeText(text);
				return true;
			}
		} catch {}
		try {
			const textarea = document.createElement('textarea');
			textarea.value = text;
			textarea.setAttribute('readonly', '');
			textarea.style.position = 'fixed';
			textarea.style.left = '-9999px';
			document.body.appendChild(textarea);
			textarea.select();
			const ok = document.execCommand('copy');
			document.body.removeChild(textarea);
			return ok;
		} catch {
			return false;
		}
	}

	async function shareResults() {
		const text = results
			.slice(0, 10)
			.map((r) => `#${r.rank} ${r.name}`)
			.join('\n');
		const shareText = `${$t('theater.sorter.shareTextHeader')}\n${text}\n\n${$t('theater.sorter.shareTextFooter')} ${window.location.origin}/jkt48/sorter`;
		if (navigator.share) {
			try {
				await navigator.share({
					title: $t('theater.sorter.shareTitle'),
					text: shareText,
					url: window.location.href
				});
				return;
			} catch (err) {
				if (err instanceof DOMException && err.name === 'AbortError') return;
			}
		}
		const copied = await copyToClipboard(shareText);
		if (copied) showToast($t('theater.sorter.copySuccess'), 'success');
		else showToast($t('theater.sorter.copyFailed'), 'error');
	}
</script>

<SEO title={$t('theater.sorter.title')} path="/jkt48/sorter" description={$t('seo.sorter')} />

<div
	class="w-full flex flex-col items-center justify-start min-h-[calc(100svh-120px)] pt-4 md:pt-6 pb-12"
>
	{#if currentState === 'landing'}
		<div class="text-center space-y-4 mb-8">
			<h1
				class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter uppercase mb-3"
			>
				{$t('theater.sorter.title')}
			</h1>
			<p
				class="text-base md:text-lg text-slate-500 dark:text-slate-400 font-medium max-w-2xl mx-auto uppercase tracking-widest leading-relaxed"
			>
				{$t('theater.sorter.subtitle')}
			</p>
		</div>

		<SorterGenerationSelect
			{generations}
			{selectedGenerations}
			{loadingGenerations}
			selectedMembersCount={allMembers.filter((m) => selectedGenerations.has(m.generation)).length}
			ontoggle={toggleGeneration}
			onselectAll={selectAllGenerations}
			ondeselectAll={deselectAllGenerations}
			onstart={startSort}
			variant="public"
		/>
	{:else if currentState === 'sorting'}
		<SorterProcess
			{numQuestion}
			{displayProgress}
			{leftMember}
			{rightMember}
			{isAnimating}
			{lastSelectedSide}
			hasHistory={history.length > 0}
			onselect={handleSelect}
			onundo={undo}
			onexit={restart}
			variant="public"
		/>
	{:else if currentState === 'results'}
		<SorterResults
			{results}
			{layoutMode}
			onshare={shareResults}
			onrestart={restart}
			onchangeLayout={(mode) => (layoutMode = mode)}
			variant="public"
		/>
	{/if}
</div>

<style>
</style>
