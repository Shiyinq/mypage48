<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { Member } from '$lib/apis/members';
	import { membersStore } from '$lib/stores/theater';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { showToast } from '$lib/stores';
	import { Play, RotateCcw, Equal, Share2, ArrowLeft, Trophy, LayoutGrid, List } from 'lucide-svelte';
	import { fly, fade } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import SEO from '$lib/components/SEO.svelte';

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
	let finishSize = 0;
	let finishFlag = 0;

	// Results
	interface ResultMember extends Member {
		rank: number;
	}
	let results: ResultMember[] = [];
	let layoutMode: 'card' | 'list' = 'card';

	// History for Undo
	let history: any[] = [];

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
		selectedMembers = allMembers.filter(m => selectedGenerations.has(m.generation));
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
	$: progress = finishFlag ? 100 : Math.floor((finishSize / (selectedMembers.length * Math.log2(selectedMembers.length) * 0.7)) * 100);
	$: displayProgress = Math.min(progress, 99);

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
		const text = results.slice(0, 10).map(r => `#${r.rank} ${r.name}`).join('\n');
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

<SEO
	title={$t('theater.sorter.title')}
	path="/jkt48/sorter"
	description={$t('theater.sorter.subtitle')}
/>

<div class="w-full flex flex-col items-center justify-start min-h-[calc(100svh-120px)] pt-4 md:pt-6 pb-12">
	{#if currentState === 'landing'}
		<div class="text-center space-y-4 mb-8">
			<h1 class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter uppercase mb-3">
				{$t('theater.sorter.title')}
			</h1>
			<p class="text-base md:text-lg text-slate-500 dark:text-slate-400 font-medium max-w-2xl mx-auto uppercase tracking-widest leading-relaxed">
				{$t('theater.sorter.subtitle')}
			</p>
		</div>

		<div in:fade={{ duration: 300 }} class="w-full max-w-2xl space-y-6">
			<div class="bg-white dark:bg-zinc-900 rounded-2xl p-6 shadow-xl border border-gray-100 dark:border-zinc-800 space-y-6">
				<div class="flex items-center justify-between">
					<h3 class="font-black text-themed uppercase tracking-widest text-sm text-slate-400">{$t('theater.sorter.generation')}</h3>
					<div class="flex gap-4 font-black">
						<button on:click={selectAllGenerations} class="text-xs text-red-600 hover:scale-105 transition-transform cursor-pointer uppercase tracking-widest">{$t('theater.sorter.selectAll')}</button>
						<button on:click={deselectAllGenerations} class="text-xs text-slate-400 hover:text-themed transition-colors cursor-pointer uppercase tracking-widest">{$t('theater.sorter.clear')}</button>
					</div>
				</div>

				<div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
					{#if loadingGenerations}
						{#each Array(8) as _}
							<div class="h-12 bg-slate-50 dark:bg-zinc-800 animate-pulse rounded-2xl"></div>
						{/each}
					{:else}
						{#each generations as gen}
							<button
								on:click={() => toggleGeneration(gen)}
								class={`px-4 py-3 rounded-2xl text-sm font-black transition-all border-2 cursor-pointer shadow-sm ${
									selectedGenerations.has(gen)
										? 'bg-red-600 border-red-600 text-white shadow-lg shadow-red-500/30 ring-4 ring-red-500/10'
										: 'bg-white dark:bg-zinc-800 border-gray-50 dark:border-zinc-700 text-slate-500 hover:border-red-600/30'
								}`}
							>
								{$t('theater.sorter.genLabel', { gen })}
							</button>
						{/each}
					{/if}
				</div>

				<div class="pt-6 border-t border-gray-50 dark:border-zinc-800 flex items-center justify-between">
					<span class="text-xs font-black uppercase tracking-widest text-slate-400">{$t('theater.sorter.selectedMembers')}</span>
					<div class="flex items-baseline gap-2">
						<span class="font-black text-red-600 text-3xl">
							{allMembers.filter(m => selectedGenerations.has(m.generation)).length}
						</span>
						<span class="text-[10px] font-black uppercase border-b-2 border-red-600">{$t('theater.sorter.ready')}</span>
					</div>
				</div>
			</div>

			<button
				on:click={startSort}
				disabled={loadingGenerations || allMembers.filter(m => selectedGenerations.has(m.generation)).length < 2}
				class="w-full sm:w-80 h-16 bg-red-600 hover:bg-red-700 text-white rounded-full font-black text-xl shadow-xl shadow-red-500/30 hover:-translate-y-1 transition-all duration-300 flex items-center justify-center gap-3 group disabled:opacity-50 disabled:grayscale mx-auto cursor-pointer"
			>
				<Play class="w-6 h-6 fill-current group-hover:translate-x-1 transition-transform" />
				{$t('theater.sorter.start')}
			</button>
		</div>
	{:else if currentState === 'sorting'}
		<div in:fade class="w-full max-w-2xl space-y-6 flex flex-col items-center">
			<div class="w-full space-y-2">
				<div class="flex justify-between items-end px-2">
					<div class="space-y-0.5">
						<h2 class="text-slate-900 dark:text-white font-black text-lg uppercase tracking-tighter">{$t('theater.sorter.sorting')}</h2>
						<p class="text-slate-400 text-[8px] font-black uppercase tracking-widest">{$t('theater.sorter.questionLabel', { num: numQuestion })}</p>
					</div>
					<div class="text-right">
						<span class="text-red-600 font-black text-2xl italic tracking-tighter">{displayProgress}%</span>
					</div>
				</div>
				<div class="h-3 w-full bg-slate-100 dark:bg-zinc-800 rounded-full overflow-hidden p-1 shadow-inner ring-1 ring-slate-100 dark:ring-zinc-700">
					<div class="h-full bg-gradient-to-r from-red-500 to-red-600 transition-all duration-500 ease-out rounded-full shadow-lg shadow-red-500/40" style="width: {displayProgress}%"></div>
				</div>
			</div>

			<div class="grid grid-cols-[1fr_auto_1fr] items-center gap-4 md:gap-8 w-full max-w-2xl">
				<button on:click={() => sortList(1)} class="group relative aspect-[2/3] rounded-xl overflow-hidden border-4 border-transparent hover:border-red-600 transition-all hover:shadow-2xl hover:shadow-red-500/20 active:scale-95 bg-slate-100 dark:bg-zinc-800 cursor-pointer shadow-xl">
					<img src={getExternalMediaUrl(leftMember?.img)} alt={leftMember?.name} class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" on:error={handleImageError} />
					<img src={leftMember?.member_type?.toLowerCase() === 'trainee' ? TRAINEE_FRAME : MEMBER_FRAME} alt="frame" class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10" />
					<div class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"></div>
					<div class="absolute bottom-3 left-3 right-3 text-left z-30">
						<span class="px-1.5 py-0.5 bg-red-600 text-white text-[7px] font-black rounded-md uppercase tracking-widest mb-1 block w-fit">Gen {leftMember?.generation}</span>
						<h3 class="text-white text-xs font-black leading-tight drop-shadow-md truncate">{leftMember?.name}</h3>
					</div>
				</button>

				<div class="z-10 w-10 h-10 flex items-center justify-center bg-white dark:bg-zinc-900 rounded-full shadow-2xl border-2 border-red-600 text-red-600 font-black italic text-[10px] animate-pulse">VS</div>

				<button on:click={() => sortList(-1)} class="group relative aspect-[2/3] rounded-xl overflow-hidden border-4 border-transparent hover:border-red-600 transition-all hover:shadow-2xl hover:shadow-red-500/20 active:scale-95 bg-slate-100 dark:bg-zinc-800 cursor-pointer shadow-xl">
					<img src={getExternalMediaUrl(rightMember?.img)} alt={rightMember?.name} class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" on:error={handleImageError} />
					<img src={rightMember?.member_type?.toLowerCase() === 'trainee' ? TRAINEE_FRAME : MEMBER_FRAME} alt="frame" class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10" />
					<div class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"></div>
					<div class="absolute bottom-3 left-3 right-3 text-left z-30">
						<span class="px-1.5 py-0.5 bg-red-600 text-white text-[7px] font-black rounded-md uppercase tracking-widest mb-1 block w-fit">Gen {rightMember?.generation}</span>
						<h3 class="text-white text-xs font-black leading-tight drop-shadow-md truncate">{rightMember?.name}</h3>
					</div>
				</button>
			</div>

			<div class="flex justify-center gap-3">
				<button on:click={() => sortList(0)} class="h-12 px-8 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-900 dark:text-white font-black rounded-full transition-all text-sm cursor-pointer whitespace-nowrap flex items-center gap-2 shadow-sm">
					<Equal size={18} />
					{$t('theater.sorter.tie')}
				</button>
				<button on:click={undo} disabled={history.length === 0} class="h-12 px-8 bg-amber-50 dark:bg-amber-950/20 text-amber-600 font-black rounded-full transition-all text-sm cursor-pointer disabled:opacity-30 whitespace-nowrap flex items-center gap-2 shadow-sm">
					<RotateCcw size={18} />
					{$t('theater.sorter.undo')}
				</button>
				<button on:click={restart} class="h-12 px-8 text-red-600 font-black rounded-full transition-all text-sm cursor-pointer hover:bg-red-50 dark:hover:bg-red-950/20 whitespace-nowrap flex items-center gap-2">
					<ArrowLeft size={18} />
					{$t('theater.sorter.exit')}
				</button>
			</div>
		</div>
	{:else if currentState === 'results'}
		<div in:fade class={`w-full space-y-8 px-4 mx-auto ${layoutMode === 'list' ? 'max-w-3xl' : 'max-w-6xl'}`}>
			<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
				<div class="flex items-center gap-4">
					<div class="w-12 h-12 rounded-2xl bg-red-600 flex items-center justify-center text-white shadow-xl shadow-red-500/20 shrink-0">
						<Trophy size={22} />
					</div>
					<div class="space-y-0.5">
						<h1 class="text-2xl md:text-3xl font-black text-slate-900 dark:text-white tracking-tighter uppercase leading-none">{$t('theater.sorter.results')}</h1>
						<p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{$t('theater.sorter.resultsSubtitle')}</p>
					</div>
				</div>

				<div class="flex items-center gap-2">
					<div class="flex bg-white dark:bg-zinc-900 rounded-full p-1 border border-gray-100 dark:border-zinc-800 shadow-sm mr-2">
						<button 
							on:click={() => layoutMode = 'card'}
							class={`p-2 rounded-full transition-all cursor-pointer ${layoutMode === 'card' ? 'bg-red-600 text-white shadow-lg shadow-red-500/20' : 'text-slate-400 hover:text-red-600'}`}
							title="Grid View"
						>
							<LayoutGrid size={18} />
						</button>
						<button 
							on:click={() => layoutMode = 'list'}
							class={`p-2 rounded-full transition-all cursor-pointer ${layoutMode === 'list' ? 'bg-red-600 text-white shadow-lg shadow-red-500/20' : 'text-slate-400 hover:text-red-600'}`}
							title="List View"
						>
							<List size={18} />
						</button>
					</div>

					<button on:click={shareResults} class="h-11 px-6 bg-red-600 hover:bg-red-700 text-white font-black rounded-full transition-all shadow-lg shadow-red-500/20 flex items-center gap-2 text-xs cursor-pointer">
						<Share2 size={16} />
						{$t('theater.sorter.share')}
					</button>
					<button on:click={restart} class="h-11 px-6 bg-white dark:bg-zinc-800 text-slate-900 dark:text-white font-black rounded-full transition-all shadow-md border border-gray-100 dark:border-zinc-700 flex items-center gap-2 text-xs cursor-pointer">
						<RotateCcw size={16} />
						{$t('theater.sorter.restart')}
					</button>
				</div>
			</div>

			{#key layoutMode}
				<div in:fade={{ duration: 400 }}>
					{#if layoutMode === 'card'}
						<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
					{#each results as member, i (member.id) }
						<div in:fly={{ y: 20, delay: i * 30, duration: 500, easing: quintOut }} class="relative group">
							<div class={`aspect-[3/4] rounded-xl overflow-hidden border-2 transition-all group-hover:scale-105 group-hover:shadow-2xl cursor-pointer relative ${i <= 2 ? 'shiny-card' : ''} ${i === 0 ? 'border-yellow-400 shadow-xl shadow-yellow-400/20' : i === 1 ? 'border-slate-300 shadow-xl shadow-slate-300/20' : i === 2 ? 'border-amber-600 shadow-xl shadow-amber-700/10' : 'border-slate-100 dark:border-zinc-800 shadow-lg'}`}>
								<img src={getExternalMediaUrl(member.img)} alt={member.name} class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" on:error={handleImageError} />
								
								<img src={member.member_type?.toLowerCase() === 'trainee' ? TRAINEE_FRAME : MEMBER_FRAME} alt="frame" class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10" />

								<div class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"></div>
								
								<div class={`absolute top-3 left-3 w-8 h-8 rounded-full flex items-center justify-center font-black text-sm z-30 shadow-lg ${i === 0 ? 'bg-yellow-400 text-yellow-900 border-2 border-yellow-200' : i === 1 ? 'bg-slate-300 text-slate-800 border-2 border-slate-100' : i === 2 ? 'bg-amber-700 text-white border-2 border-amber-500' : 'bg-white dark:bg-zinc-900 text-slate-900 dark:text-white border-2 border-slate-50 dark:border-zinc-800'}`}>
									{i + 1}
								</div>

								<div class="absolute bottom-4 left-4 right-4 z-30">
									<h4 class="font-black text-white text-[11px] leading-tight line-clamp-2 drop-shadow-md mb-0.5 uppercase">{member.name}</h4>
									<span class="text-[8px] font-black text-white/70 uppercase tracking-widest">Gen {member.generation}</span>
								</div>

								{#if i === 0}
									<div class="absolute top-3 right-3 z-30 scale-110">
										<Trophy size={18} class="text-yellow-400 fill-current drop-shadow-lg" />
									</div>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="flex flex-col gap-3 max-w-3xl mx-auto w-full">
					<!-- Top 3 -->
					{#each results.slice(0, 3) as member, i (member.id)}
						<div 
							in:fly={{ y: 20, delay: i * 30, duration: 500, easing: quintOut }} 
							class={`flex items-center gap-4 bg-white dark:bg-zinc-900 rounded-xl p-3 border-2 transition-all hover:scale-105 hover:shadow-2xl hover:border-red-600 group relative overflow-hidden shadow-sm cursor-pointer mx-auto w-full max-w-2xl ${i === 0 ? 'border-yellow-400 shadow-xl shadow-yellow-400/20' : i === 1 ? 'border-slate-300 shadow-xl shadow-slate-300/20' : 'border-amber-600 shadow-xl shadow-amber-700/10'}`}
						>
							<div class={`rank-badge w-10 h-10 rounded-full flex items-center justify-center font-black text-base shrink-0 z-30 shadow-sm ${i === 0 ? 'bg-yellow-400 text-yellow-900' : i === 1 ? 'bg-slate-300 text-slate-800' : 'bg-amber-700 text-white'}`}>
								{i + 1}
							</div>

							<div class={`relative w-14 aspect-[3/4] rounded-lg overflow-hidden shrink-0 border border-slate-100 dark:border-zinc-800 transition-transform duration-500 z-30 shadow-sm ${i <= 2 ? 'shiny-card' : ''}`}>
								<img src={getExternalMediaUrl(member.img)} alt={member.name} class="w-full h-full object-cover" on:error={handleImageError} />
								<img src={member.member_type?.toLowerCase() === 'trainee' ? TRAINEE_FRAME : MEMBER_FRAME} alt="frame" class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10" />
							</div>

							<div class="flex flex-col gap-0.5 z-30">
								<h4 class="font-black text-slate-900 dark:text-white text-base md:text-lg uppercase tracking-tight leading-none truncate max-w-[200px] sm:max-w-none">{member.name}</h4>
								<span class="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-widest truncate">{member.generation.length > 5 ? member.generation : 'Gen ' + member.generation}</span>
							</div>

							{#if i === 0}
								<div class="ml-auto mr-4 z-30">
									<Trophy size={22} class="text-yellow-400 fill-current drop-shadow-md" />
								</div>
							{:else if i === 1}
								<div class="ml-auto mr-4 z-30">
									<Trophy size={20} class="text-slate-300 fill-current drop-shadow-md" />
								</div>
							{:else if i === 2}
								<div class="ml-auto mr-4 z-30">
									<Trophy size={20} class="text-amber-600 fill-current drop-shadow-md" />
								</div>
							{/if}
						</div>
					{/each}

					<!-- Rank 4+ (2 Columns) -->
					{#if results.length > 3}
						<div class="grid grid-cols-1 md:grid-cols-2 gap-3 w-full mt-1">
							{#each results.slice(3) as member, i (member.id)}
								<div 
									in:fly={{ y: 20, delay: (i + 3) * 30, duration: 500, easing: quintOut }} 
									class="flex items-center gap-3 bg-white dark:bg-zinc-900 rounded-xl p-2.5 border border-slate-100 dark:border-zinc-800 transition-all hover:scale-[1.02] hover:shadow-xl hover:border-red-600 group relative overflow-hidden shadow-sm cursor-pointer"
								>
									<div class="rank-badge w-8 h-8 rounded-full flex items-center justify-center font-black text-xs shrink-0 z-30 bg-slate-100 dark:bg-zinc-800 text-slate-900 dark:text-white border border-slate-200 dark:border-zinc-700 shadow-sm">
										{i + 4}
									</div>

									<div class="relative w-11 aspect-[3/4] rounded-lg overflow-hidden shrink-0 border border-slate-100 dark:border-zinc-800 transition-transform duration-500 z-30 shadow-sm">
										<img src={getExternalMediaUrl(member.img)} alt={member.name} class="w-full h-full object-cover" on:error={handleImageError} />
										<img src={member.member_type?.toLowerCase() === 'trainee' ? TRAINEE_FRAME : MEMBER_FRAME} alt="frame" class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10 opacity-80" />
									</div>

									<div class="flex flex-col gap-0.5 z-30 min-w-0">
										<h4 class="font-black text-slate-900 dark:text-white text-xs sm:text-sm uppercase tracking-tight leading-none truncate">{member.name}</h4>
										<span class="text-[9px] font-bold text-slate-400 uppercase tracking-widest truncate">Gen {member.generation}</span>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{/key}
</div>
{/if}
</div>

<style>
	.shiny-card::after {
		content: '';
		position: absolute;
		top: -50%;
		left: -50%;
		width: 200%;
		height: 200%;
		background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.3), transparent);
		transform: rotate(45deg);
		animation: shine 4s infinite;
		pointer-events: none;
		z-index: 25;
	}

	@keyframes shine {
		0% {
			transform: translateX(-100%) translateY(-100%) rotate(45deg);
		}
		20%,
		100% {
			transform: translateX(100%) translateY(100%) rotate(45deg);
		}
	}
</style>
