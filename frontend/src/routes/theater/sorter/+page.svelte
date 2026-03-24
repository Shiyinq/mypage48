<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import type { Member } from '$lib/apis/members';
	import { membersStore, isMembersLoading } from '$lib/stores/theater';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { ErrorState } from '$lib/components';
	import { showToast } from '$lib/stores';
	import { Play, RotateCcw, Equal, Share2, ArrowLeft, Trophy } from 'lucide-svelte';
	import { fly, fade } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';

	const { t } = useTranslation();

	// Sorter State
	type SorterState = 'landing' | 'sorting' | 'results';
	let currentState: SorterState = 'landing';

	let allMembers: Member[] = [];
	let selectedMembers: Member[] = [];
	let generations: string[] = [];
	let selectedGenerations: Set<string> = new Set();
	let loadingGenerations = true;
	
	const MEMBER_FRAME = 'https://jkt48.com/images/member/bg-member-item-frame-transparent.png';
	const TRAINEE_FRAME = 'https://jkt48.com/images/member/bg-member-trainee-frame-transparent.png';

	// Sorting Logic State
	let lstMember: any[] = [];
	let parent: number[] = [];
	let rec: number[] = [];
	let cmp1 = 0;
	let cmp2 = 0;
	let head1 = 0;
	let head2 = 0;
	let nrec = 0;
	let numQuestion = 0;
	let totalQuestion = 0;
	let finishSize = 0;
	let finishFlag = 0;

	// Results
	interface ResultMember extends Member {
		rank: number;
	}
	let results: ResultMember[] = [];

	// History for Undo
	let history: any[] = [];

	async function fetchMembers() {
		try {
			// Limit to 100 to avoid 422 error
			await membersStore.load({ limit: 100 }, true);
			allMembers = $membersStore.list;
			
			// Extract generations
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

	// Initialize Sorting
	function startSort() {
		selectedMembers = allMembers.filter(m => selectedGenerations.has(m.generation));
		if (selectedMembers.length < 2) {
			showToast($t('theater.sorter.minSelection'), 'error');
			return;
		}

		// Fisher-Yates shuffle
		selectedMembers = [...selectedMembers].sort(() => Math.random() - 0.5);

		// Implementation of the sorter algorithm
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

		// Estimate total questions
		totalQuestion = Math.ceil(selectedMembers.length * Math.log2(selectedMembers.length));

		currentState = 'sorting';
	}

	function saveHistory() {
		history = [...history, JSON.parse(JSON.stringify({
			lstMember, parent, rec, cmp1, cmp2, head1, head2, nrec, numQuestion, finishSize, finishFlag
		}))];
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
		
		// 1: left win, -1: right win, 0: tie
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

		// Check if one of sub-lists is empty
		if (head1 < lstMember[cmp1].length && head2 < lstMember[cmp2].length) {
			numQuestion++;
		} else {
			// Copy remaining items
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

			// Replace both lists with the merged one
			lstMember.splice(cmp1, 2, [...rec]);
			
			// Next pair in same level
			// Since we spliced 2 into 1, the "next pair" starts at cmp1 + 1
			cmp1 = cmp1 + 1;
			cmp2 = cmp1 + 1;

			// Reset heads
			head1 = 0;
			head2 = 0;
			rec = [];
			nrec = 0;

			// Check if we reached the end of current level
			if (cmp1 >= lstMember.length - 1) {
				if (lstMember.length === 1) {
					finishFlag = 1;
					showResults();
					return;
				}
				// Start next level
				cmp1 = 0;
				cmp2 = 1;
			}
			numQuestion++;
		}
	}

	function handleImageError(e: Event) {
		const target = e.currentTarget as HTMLImageElement;
		target.src = 'https://jkt48.com/images/member/member_256x256_full.png';
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

	$: leftMember = selectedMembers[lstMember[cmp1]?.[head1]];
	$: rightMember = selectedMembers[lstMember[cmp2]?.[head2]];
	$: progress = finishFlag ? 100 : Math.floor((finishSize / (selectedMembers.length * Math.log2(selectedMembers.length) * 0.7)) * 100); // Heuristic progress
	$: displayProgress = Math.min(progress, 99); // Don't show 100 until finished

	async function copyToClipboard(text: string): Promise<boolean> {
		try {
			if (navigator.clipboard?.writeText) {
				await navigator.clipboard.writeText(text);
				return true;
			}
		} catch {
			// Fallback below for browsers that block Clipboard API
		}

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
		const text = results.slice(0, 10).map(r => `#${r.rank} ${r.name}`).join('\n');
		const shareText = `${$t('theater.sorter.shareTextHeader')}\n${text}\n\n${$t('theater.sorter.shareTextFooter')} ${window.location.origin}/theater/sorter`;

		if (navigator.share) {
			try {
				await navigator.share({
					title: $t('theater.sorter.shareTitle'),
					text: shareText,
					url: window.location.href
				});
				return;
			} catch (err) {
				// User cancel share: don't show error toast
				if (err instanceof DOMException && err.name === 'AbortError') return;
			}
		}

		const copied = await copyToClipboard(shareText);
		if (copied) {
			showToast($t('theater.sorter.copySuccess'), 'success');
		} else {
			showToast($t('theater.sorter.copyFailed'), 'error');
		}
	}
</script>

<SEO
	title={$t('theater.sorter.title')}
	path="/theater/sorter"
	description={$t('theater.sorter.subtitle')}
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
	class={`w-full flex flex-col items-center justify-start min-h-[calc(100svh-120px)] ${currentState === 'results' ? 'pt-8 pb-12' : 'pt-3 md:pt-5 pb-4 overflow-hidden'}`}
>
	{#if currentState === 'landing'}
		<div in:fade={{ duration: 300 }} class="w-full max-w-2xl text-center space-y-6 py-4 overflow-y-auto no-scrollbar">
			<!-- Title and subtitle removed as they are redundant with the layout header -->
			<div class="h-0"></div>

			<div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-6 shadow-sm transition-all duration-300 space-y-6">
				<div class="flex items-center justify-between">
					<h3 class="font-bold text-themed">{$t('theater.sorter.generation')}</h3>
					<div class="flex gap-2 font-black">
						<button on:click={selectAllGenerations} class="text-xs text-rose-500 hover:text-rose-600 transition-colors cursor-pointer">{$t('theater.sorter.selectAll')}</button>
						<span class="text-zinc-300">|</span>
						<button on:click={deselectAllGenerations} class="text-xs text-zinc-400 hover:text-themed transition-colors cursor-pointer">{$t('theater.sorter.clear')}</button>
					</div>
				</div>

				<div class="grid grid-cols-3 sm:grid-cols-4 gap-2">
					{#if loadingGenerations}
						{#each Array(9) as _}
							<div class="h-10 bg-zinc-100 dark:bg-zinc-800 animate-pulse rounded-xl"></div>
						{/each}
					{:else}
						{#each generations as gen}
							<button
								on:click={() => toggleGeneration(gen)}
								class={`px-3 py-2 rounded-xl text-sm font-bold transition-all border cursor-pointer shadow-sm hover:shadow-md ${
									selectedGenerations.has(gen)
										? 'bg-rose-500 border-rose-600 text-white scale-105'
										: 'bg-zinc-50 dark:bg-zinc-800 border-zinc-100 dark:border-zinc-700 text-zinc-500 dark:text-zinc-400 hover:border-rose-300'
								}`}
							>
								{$t('theater.sorter.genLabel', { gen })}
							</button>
						{/each}
					{/if}
				</div>

				<div class="pt-4 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between text-sm text-themed-secondary">
					<span>{$t('theater.sorter.selectedMembers')}</span>
					<div class="flex items-baseline gap-1">
						<span class="font-black text-rose-500 text-2xl">
							{allMembers.filter(m => selectedGenerations.has(m.generation)).length}
						</span>
						<span class="text-[10px] font-bold uppercase tracking-widest">{$t('theater.sorter.ready')}</span>
					</div>
				</div>
			</div>

			<button
				on:click={startSort}
				disabled={loadingGenerations || allMembers.filter(m => selectedGenerations.has(m.generation)).length < 2}
				class="w-full sm:w-64 py-4 bg-rose-500 hover:bg-rose-600 text-white rounded-full font-black text-lg shadow-none hover:shadow-none transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.99] flex items-center justify-center gap-2 group disabled:opacity-50 disabled:grayscale disabled:hover:translate-y-0 disabled:hover:shadow-none cursor-pointer mx-auto"
			>
				<Play class="w-6 h-6 fill-current group-hover:translate-x-1 transition-transform" />
				{$t('theater.sorter.start')}
			</button>
		</div>
	{:else if currentState === 'sorting'}
		<div in:fade class="w-full max-w-5xl flex flex-col px-4 overflow-hidden gap-2 md:gap-3">
			<!-- Progress Header -->
			<div class="space-y-0.5 md:space-y-1">
				<div class="flex justify-between items-end">
					<div class="space-y-0">
						<h2 class="text-themed font-black text-lg md:text-xl uppercase tracking-wider">{$t('theater.sorter.sorting')}</h2>
						<p class="text-themed-secondary text-[10px]">{$t('theater.sorter.questionLabel', { num: numQuestion })}</p>
					</div>
					<div class="text-right">
						<span class="text-rose-500 font-black text-2xl md:text-3xl">{displayProgress}%</span>
					</div>
				</div>
				<div class="h-2 md:h-3 w-full bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden shadow-inner border border-zinc-200/50 dark:border-zinc-700/50">
					<div 
						class="h-full bg-gradient-to-r from-rose-400 to-rose-600 transition-all duration-500 ease-out shadow-[0_0_10px_rgba(244,63,94,0.5)]" 
						style="width: {displayProgress}%"
					></div>
				</div>
			</div>

			<!-- Comparison View -->
			<div class="flex-none flex flex-col justify-center min-h-0 py-1">
				<div class="grid grid-cols-[1fr_auto_1fr] items-center w-full max-w-5xl mx-auto gap-2 md:gap-4 lg:gap-8">
					<!-- Member 1 Container -->
					<div class="flex justify-end p-0">
						<button
							on:click={() => sortList(1)}
							class="group relative aspect-[3/4] rounded-2xl overflow-hidden border-4 border-transparent hover:border-rose-500 transition-all hover:shadow-2xl hover:shadow-rose-500/20 active:scale-95 bg-zinc-200 dark:bg-zinc-800 w-auto h-full max-h-[47vh] min-h-[225px] cursor-pointer"
						>
							<img 
								src={getExternalMediaUrl(leftMember?.img)} 
								alt={leftMember?.name} 
								class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
								on:error={handleImageError}
							/>
							<img
								src={leftMember?.member_type?.toLowerCase() === 'trainee' ? TRAINEE_FRAME : MEMBER_FRAME}
								alt="frame"
								class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
							/>
							<div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent z-20"></div>
							<div class="absolute bottom-2 left-2 right-2 text-left z-30">
								<span class="px-1.5 py-0.5 bg-rose-500 text-white text-[7px] font-black rounded uppercase tracking-widest mb-0.5 block w-fit">{$t('theater.sorter.genLabel', { gen: leftMember?.generation })}</span>
								<h3 class="text-white text-[10px] md:text-sm font-black leading-tight drop-shadow-md truncate">{leftMember?.name}</h3>
							</div>
						</button>
					</div>

					<!-- VS Indicator -->
					<div class="z-10 w-8 h-8 md:w-10 md:h-10 self-center flex-shrink-0 flex items-center justify-center bg-white dark:bg-zinc-900 rounded-full shadow-2xl border-2 md:border-4 border-rose-500 text-rose-500 font-black text-[8px] md:text-[10px] italic animate-bounce-slow pointer-events-none">
						VS
					</div>

					<!-- Member 2 Container -->
					<div class="flex justify-start p-0">
						<button
							on:click={() => sortList(-1)}
							class="group relative aspect-[3/4] rounded-2xl overflow-hidden border-4 border-transparent hover:border-rose-500 transition-all hover:shadow-2xl hover:shadow-rose-500/20 active:scale-95 bg-zinc-200 dark:bg-zinc-800 w-auto h-full max-h-[47vh] min-h-[225px] cursor-pointer"
						>
							<img 
								src={getExternalMediaUrl(rightMember?.img)} 
								alt={rightMember?.name} 
								class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
								on:error={handleImageError}
							/>
							<img
								src={rightMember?.member_type?.toLowerCase() === 'trainee' ? TRAINEE_FRAME : MEMBER_FRAME}
								alt="frame"
								class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
							/>
							<div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent z-20"></div>
							<div class="absolute bottom-2 left-2 right-2 text-left z-30">
								<span class="px-1.5 py-0.5 bg-rose-500 text-white text-[7px] font-black rounded uppercase tracking-widest mb-0.5 block w-fit">{$t('theater.sorter.genLabel', { gen: rightMember?.generation })}</span>
								<h3 class="text-white text-[10px] md:text-sm font-black leading-tight drop-shadow-md truncate">{rightMember?.name}</h3>
							</div>
						</button>
					</div>
				</div>
			</div>

			<!-- Controls -->
			<div class="flex justify-center gap-2 mt-2 md:mt-3">
				<button
					on:click={() => sortList(0)}
					class="h-10 min-w-[112px] flex items-center justify-center gap-2 px-5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-100 font-bold rounded-full transition-all active:scale-95 text-sm cursor-pointer border border-slate-200/90 dark:border-slate-600/70"
				>
					<Equal class="w-4 h-4 text-slate-500 dark:text-slate-300" />
					{$t('theater.sorter.tie')}
				</button>
				<button
					on:click={undo}
					disabled={history.length === 0}
					class="h-10 min-w-[112px] flex items-center justify-center gap-2 px-5 bg-amber-50 dark:bg-amber-950/30 hover:bg-amber-100 dark:hover:bg-amber-900/40 text-amber-700 dark:text-amber-300 font-bold rounded-full transition-all active:scale-95 disabled:opacity-40 disabled:grayscale text-sm cursor-pointer border border-amber-200/80 dark:border-amber-700/40"
				>
					<RotateCcw class="w-4 h-4 text-amber-500 dark:text-amber-400" />
					{$t('theater.sorter.undo')}
				</button>
				<button
					on:click={restart}
					class="h-10 min-w-[112px] flex items-center justify-center gap-2 px-5 text-rose-500 font-bold hover:bg-rose-500/10 rounded-full transition-all text-sm cursor-pointer border border-transparent hover:border-rose-200 dark:hover:border-rose-900/40"
				>
					<ArrowLeft class="w-4 h-4" />
					{$t('theater.sorter.exit')}
				</button>
			</div>
		</div>
	{:else if currentState === 'results'}
		<div in:fade class="w-full max-w-6xl space-y-5 px-3 md:px-4">
			<div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
				<div class="flex items-center gap-3 text-left">
					<div class="w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0 bg-rose-500 ring-1 ring-rose-200/70 dark:ring-rose-900/50">
						<Trophy class="w-5 h-5 text-white fill-current" />
					</div>
					<div class="space-y-0.5">
						<h1 class="text-2xl md:text-3xl font-black text-themed leading-tight tracking-tight">{$t('theater.sorter.results')}</h1>
						<p class="text-sm text-themed-secondary">{$t('theater.sorter.resultsSubtitle')}</p>
					</div>
				</div>

				<div class="flex flex-wrap items-center gap-2 md:justify-end">
					<button
						on:click={shareResults}
						class="h-10 min-w-[112px] flex items-center justify-center gap-2 px-5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-themed font-bold rounded-full transition-all active:scale-95 text-sm cursor-pointer"
					>
						<Share2 class="w-4 h-4 text-zinc-500 dark:text-zinc-300" />
						{$t('theater.sorter.share')}
					</button>
					<button
						on:click={restart}
						class="h-10 min-w-[112px] flex items-center justify-center gap-2 px-5 text-rose-500 font-bold hover:bg-rose-500/10 rounded-full transition-all text-sm cursor-pointer border border-transparent hover:border-rose-200 dark:hover:border-rose-900/40"
					>
						<RotateCcw class="w-4 h-4" />
						{$t('theater.sorter.restart')}
					</button>
				</div>
			</div>

			<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 md:gap-4 px-0.5">
				{#each results as member, i (member.id) }
					<div 
						in:fly={{ y: 20, delay: i * 30, duration: 500, easing: quintOut }}
						class={`relative aspect-[3/4] rounded-2xl overflow-hidden border-2 transition-all group group hover:scale-105 hover:shadow-xl cursor-pointer ${
							i === 0 ? 'border-yellow-400 shadow-lg shadow-yellow-400/20' : 
							i === 1 ? 'border-slate-300 shadow-lg shadow-slate-300/30' :
							i === 2 ? 'border-amber-600 shadow-lg shadow-amber-700/15' :
							'border-zinc-100 dark:border-zinc-800'
						} ${i < 3 ? `rank-highlight rank-${i + 1}` : ''}`}
					>
						<img 
							src={getExternalMediaUrl(member.img)} 
							alt={member.name} 
							class="w-full h-full object-cover" 
							on:error={handleImageError} 
						/>
						<img
							src={member.member_type?.toLowerCase() === 'trainee' ? TRAINEE_FRAME : MEMBER_FRAME}
							alt="frame"
							class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
						/>
						
						<!-- Rank Badge -->
						<div class={`absolute top-2 left-2 w-8 h-8 rounded-full flex items-center justify-center font-black text-sm z-30 shadow-lg ${
							i === 0 ? 'bg-yellow-400 text-yellow-900' : 
							i === 1 ? 'bg-slate-300 text-slate-800' :
							i === 2 ? 'bg-amber-700 text-amber-50' :
							'bg-white dark:bg-zinc-900 text-themed'
						}`}>
							{i + 1}
						</div>

						<div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent z-20"></div>
						<div class="absolute bottom-3 left-3 right-3 text-left z-30">
							<h4 class="font-black text-white text-sm leading-tight line-clamp-2 drop-shadow-md">{member.name}</h4>
							<p class="text-zinc-300 text-[8px] uppercase font-bold tracking-widest mt-0.5">{$t('theater.sorter.genLabel', { gen: member.generation })}</p>
						</div>

						{#if i === 0}
							<div class="absolute top-2 right-2 z-30">
								<Trophy class="w-5 h-5 text-yellow-400 fill-current drop-shadow-lg" />
							</div>
						{/if}

					</div>
				{/each}
			</div>

		</div>
	{/if}
</div>

<style>
	:global(.animate-bounce-slow) {
		animation: bounce 3s infinite;
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(-3px); animation-timing-function: cubic-bezier(0.8, 0, 1, 1); }
		50% { transform: translateY(3px); animation-timing-function: cubic-bezier(0, 0, 0.2, 1); }
	}

	/* Glassmorphism effects */
	.bg-white {
		background-color: rgba(255, 255, 255, 0.8);
		backdrop-filter: blur(8px);
	}

	:global(.dark) .bg-zinc-900 {
		background-color: rgba(24, 24, 27, 0.8);
		backdrop-filter: blur(8px);
	}

	.no-scrollbar::-webkit-scrollbar {
		display: none;
	}
	.no-scrollbar {
		-ms-overflow-style: none;
		scrollbar-width: none;
	}

	.rank-highlight {
		position: relative;
		overflow: hidden;
		isolation: isolate;
	}

	.rank-highlight::before {
		content: '';
		position: absolute;
		inset: -1px;
		border-radius: 1rem;
		padding: 1px;
		background: linear-gradient(120deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.24));
		-webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
		-webkit-mask-composite: xor;
		mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
		mask-composite: exclude;
		animation: borderGloss 3.4s ease-in-out infinite;
		opacity: 0.7;
		z-index: 20;
		pointer-events: none;
	}

	.rank-highlight::after {
		content: '';
		position: absolute;
		top: -45%;
		left: -120%;
		width: 85%;
		height: 185%;
		background: linear-gradient(
			115deg,
			rgba(255, 255, 255, 0) 0%,
			rgba(255, 255, 255, 0.07) 36%,
			rgba(255, 255, 255, 0.34) 49%,
			rgba(255, 255, 255, 0.08) 62%,
			rgba(255, 255, 255, 0) 100%
		);
		transform: skewX(-16deg);
		animation: cardSheen 4.8s ease-in-out infinite;
		z-index: 26;
		pointer-events: none;
	}

	.rank-1 {
		box-shadow: 0 0 0 1px rgba(250, 204, 21, 0.36), 0 8px 24px rgba(250, 204, 21, 0.2);
	}

	.rank-2 {
		box-shadow: 0 0 0 1px rgba(203, 213, 225, 0.52), 0 10px 24px rgba(148, 163, 184, 0.3);
	}

	.rank-3 {
		box-shadow: 0 0 0 1px rgba(180, 83, 9, 0.28), 0 8px 18px rgba(146, 64, 14, 0.12);
	}

	@keyframes borderGloss {
		0%, 100% {
			opacity: 0.45;
			filter: saturate(0.95);
		}
		50% {
			opacity: 0.82;
			filter: saturate(1.12);
		}
	}

	@keyframes cardSheen {
		0%, 18% {
			left: -120%;
			opacity: 0;
		}
		28% {
			opacity: 0.9;
		}
		52% {
			left: 130%;
			opacity: 0.85;
		}
		62%, 100% {
			left: 130%;
			opacity: 0;
		}
	}
</style>
