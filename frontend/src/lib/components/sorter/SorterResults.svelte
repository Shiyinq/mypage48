<script lang="ts">
	import { Trophy, LayoutGrid, List, Share2, RotateCcw, Pencil, Check, X } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import type { Member } from '$lib/apis/members';
	import { fly, fade } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import { getMemberFrame } from '$lib/constants';
	import { OptimizedImage } from '$lib/components/common';

	const { t } = useTranslation();

	interface ResultMember extends Member {
		rank: number;
	}

	interface Props {
		results: ResultMember[];
		layoutMode?: 'card' | 'list';
		variant?: 'public' | 'theater';
		selectedGenerations?: Set<string>;
		onshare?: (customTitle?: string, customSubtitle?: string) => void;
		onrestart?: () => void;
		onchangeLayout?: (mode: 'card' | 'list') => void;
	}

	let {
		results,
		layoutMode = 'card',
		variant = 'public',
		selectedGenerations = new Set(),
		onshare,
		onrestart,
		onchangeLayout
	}: Props = $props();

	// Derived Sorted Generations for display
	let sortedSelectedGens = $derived(
		[...selectedGenerations].sort((a, b) => parseInt(a) - parseInt(b))
	);

	// Custom Title & Subtitle State
	let customTitle = $state(t('theater.sorter.results'));
	let customSubtitle = $state(t('theater.sorter.resultsSubtitle'));

	let isEditingTitle = $state(false);
	let isEditingSubtitle = $state(false);

	let tempTitle = $state('');
	let tempSubtitle = $state('');

	const TITLE_LIMIT = 50;
	const SUBTITLE_LIMIT = 100;

	function startEditTitle() {
		tempTitle = customTitle;
		isEditingTitle = true;
	}

	function saveTitle() {
		if (tempTitle.trim()) {
			customTitle = tempTitle.trim().slice(0, TITLE_LIMIT);
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

	function saveSubtitle() {
		if (tempSubtitle.trim()) {
			customSubtitle = tempSubtitle.trim().slice(0, SUBTITLE_LIMIT);
		}
		isEditingSubtitle = false;
	}

	function cancelSubtitle() {
		isEditingSubtitle = false;
	}

	function autofocus(node: HTMLInputElement) {
		node.focus();
		node.select();
	}

	function shareResults() {
		onshare?.(customTitle, customSubtitle);
	}

	function restart() {
		onrestart?.();
	}

	function setLayout(mode: 'card' | 'list') {
		onchangeLayout?.(mode);
	}

	let isPublic = $derived(variant === 'public');
</script>

<div
	in:fade
	class={`w-full space-y-8 px-1.5 sm:px-4 mx-auto ${layoutMode === 'list' ? 'max-w-3xl' : 'max-w-6xl'}`}
>
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
		<div class="flex items-center gap-4 flex-1 min-w-0 w-full">
			<div class="space-y-1 min-w-0 flex-1 w-full">
				{#if isEditingTitle}
					<div class="flex items-start gap-2 w-full sm:max-w-md">
						<div class="flex flex-col gap-0.5 flex-1 min-w-0">
							<input
								type="text"
								bind:value={tempTitle}
								maxlength={TITLE_LIMIT}
								class={`w-full text-lg sm:text-2xl font-black tracking-tighter uppercase bg-slate-100/80 dark:bg-zinc-800 border border-slate-300 dark:border-zinc-700 rounded-lg px-2.5 py-0.5 focus:outline-none focus:ring-2 ${isPublic ? 'focus:ring-red-500/25 focus:border-red-600 text-slate-900 dark:text-white' : 'focus:ring-rose-500/25 focus:border-rose-500 text-themed'}`}
								onkeydown={(e) => {
									if (e.key === 'Enter') saveTitle();
									if (e.key === 'Escape') cancelTitle();
								}}
								use:autofocus
							/>
							<span class="text-[9px] font-bold text-slate-400 self-end px-1">
								{tempTitle.length}/{TITLE_LIMIT}
							</span>
						</div>
						<div class="flex items-center gap-1 shrink-0 mt-0.5">
							<button
								onclick={saveTitle}
								class="p-1.5 rounded-lg bg-green-500 hover:bg-green-600 text-white shadow-sm transition-all cursor-pointer"
								title={t('theater.sorter.save')}
							>
								<Check size={14} />
							</button>
							<button
								onclick={cancelTitle}
								class="p-1.5 rounded-lg bg-slate-200 dark:bg-zinc-800 hover:bg-slate-300 dark:hover:bg-zinc-700 text-slate-700 dark:text-zinc-300 transition-all cursor-pointer"
								title={t('theater.sorter.cancel')}
							>
								<X size={14} />
							</button>
						</div>
					</div>
				{:else}
					<div class="flex items-center gap-2 group/title w-full min-w-0">
						<h1
							class={`text-2xl md:text-3xl font-black tracking-tighter uppercase leading-tight break-words min-w-0 ${isPublic ? 'text-slate-900 dark:text-white' : 'text-themed'}`}
						>
							{customTitle}
						</h1>
						<button
							onclick={startEditTitle}
							class={`p-1 rounded-md transition-all cursor-pointer shrink-0 ${isPublic ? 'text-slate-400 hover:text-red-600 hover:bg-slate-100 dark:hover:bg-zinc-800' : 'text-zinc-400 hover:text-rose-500 hover:bg-slate-100 dark:hover:bg-zinc-800'}`}
							title={t('theater.sorter.editTitle')}
						>
							<Pencil size={14} />
						</button>
					</div>
				{/if}

				{#if isEditingSubtitle}
					<div class="flex items-start gap-2 w-full sm:max-w-xl">
						<div class="flex flex-col gap-0.5 flex-1 min-w-0">
							<input
								type="text"
								bind:value={tempSubtitle}
								maxlength={SUBTITLE_LIMIT}
								class={`w-full text-[10px] font-bold uppercase tracking-widest bg-slate-100/80 dark:bg-zinc-800 border border-slate-300 dark:border-zinc-700 rounded-lg px-2.5 py-0.5 focus:outline-none focus:ring-2 ${isPublic ? 'focus:ring-red-500/25 focus:border-red-600 text-slate-500 dark:text-slate-400' : 'focus:ring-rose-500/25 focus:border-rose-500 text-themed-secondary'}`}
								onkeydown={(e) => {
									if (e.key === 'Enter') saveSubtitle();
									if (e.key === 'Escape') cancelSubtitle();
								}}
								use:autofocus
							/>
							<span class="text-[9px] font-bold text-slate-400 self-end px-1">
								{tempSubtitle.length}/{SUBTITLE_LIMIT}
							</span>
						</div>
						<div class="flex items-center gap-1 shrink-0 mt-0.5">
							<button
								onclick={saveSubtitle}
								class="p-1.5 rounded-lg bg-green-500 hover:bg-green-600 text-white shadow-sm transition-all cursor-pointer"
								title={t('theater.sorter.save')}
							>
								<Check size={12} />
							</button>
							<button
								onclick={cancelSubtitle}
								class="p-1.5 rounded-lg bg-slate-200 dark:bg-zinc-800 hover:bg-slate-300 dark:hover:bg-zinc-700 text-slate-700 dark:text-zinc-300 transition-all cursor-pointer"
								title={t('theater.sorter.cancel')}
							>
								<X size={12} />
							</button>
						</div>
					</div>
				{:else}
					<div class="flex items-center gap-2 group/subtitle w-full min-w-0">
						<p
							class={`text-[10px] font-bold uppercase tracking-widest break-words min-w-0 leading-tight ${isPublic ? 'text-slate-400' : 'text-themed-secondary'}`}
						>
							{customSubtitle}
						</p>
						<button
							onclick={startEditSubtitle}
							class={`p-1 rounded-md transition-all cursor-pointer shrink-0 ${isPublic ? 'text-slate-400 hover:text-red-600 hover:bg-slate-100 dark:hover:bg-zinc-800' : 'text-zinc-400 hover:text-rose-500 hover:bg-slate-100 dark:hover:bg-zinc-800'}`}
							title={t('theater.sorter.editSubtitle')}
						>
							<Pencil size={12} />
						</button>
					</div>
				{/if}

				{#if sortedSelectedGens.length > 0}
					<div class="flex flex-wrap gap-1.5 pt-2">
						{#each sortedSelectedGens as gen}
							<span
								class={`px-2.5 py-0.5 rounded-full text-[9px] font-black tracking-wider uppercase border transition-all hover:scale-105 select-none ${isPublic ? 'bg-red-50/50 dark:bg-red-950/20 border-red-100 dark:border-red-900/30 text-red-600 dark:text-red-400' : 'bg-rose-50/50 dark:bg-rose-950/20 border-rose-100 dark:border-rose-900/30 text-rose-500 dark:text-rose-400'}`}
							>
								{t('theater.sorter.genLabel', { gen })}
							</span>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<div
			class="flex items-center gap-1.5 sm:gap-2 w-full sm:w-auto overflow-x-auto scrollbar-hide no-scrollbar pb-1"
		>
			<div
				class={`flex bg-white dark:bg-zinc-900 rounded-full p-1 border shadow-sm ${isPublic ? 'border-gray-100 dark:border-zinc-800' : 'border-zinc-100 dark:border-zinc-800'}`}
			>
				<button
					onclick={() => setLayout('card')}
					class={`p-1.5 sm:p-2 rounded-full transition-all cursor-pointer ${layoutMode === 'card' ? (isPublic ? 'bg-red-600 text-white shadow-lg shadow-red-500/20' : 'bg-rose-500 text-white shadow-lg shadow-rose-500/20') : isPublic ? 'text-slate-400 hover:text-red-600' : 'text-zinc-400 hover:text-rose-500'}`}
					title="Grid View"
				>
					<LayoutGrid size={16} class="sm:hidden" />
					<LayoutGrid size={18} class="hidden sm:block" />
				</button>
				<button
					onclick={() => setLayout('list')}
					class={`p-1.5 sm:p-2 rounded-full transition-all cursor-pointer ${layoutMode === 'list' ? (isPublic ? 'bg-red-600 text-white shadow-lg shadow-red-500/20' : 'bg-rose-500 text-white shadow-lg shadow-rose-500/20') : isPublic ? 'text-slate-400 hover:text-red-600' : 'text-zinc-400 hover:text-rose-500'}`}
					title="List View"
				>
					<List size={16} class="sm:hidden" />
					<List size={18} class="hidden sm:block" />
				</button>
			</div>

			<button
				onclick={shareResults}
				class={`w-9 h-9 sm:w-11 sm:h-11 text-white font-black rounded-full transition-all shadow-lg flex items-center justify-center cursor-pointer overflow-hidden ${isPublic ? 'bg-red-600 hover:bg-red-700 shadow-red-500/20' : 'bg-rose-500 hover:bg-rose-600 shadow-rose-500/20'}`}
				title={t('theater.sorter.share')}
			>
				<Share2 size={14} class="sm:hidden" />
				<Share2 size={18} class="hidden sm:block" />
			</button>
			<button
				onclick={restart}
				class={`w-9 h-9 sm:w-11 sm:h-11 bg-white dark:bg-zinc-800 font-black rounded-full transition-all shadow-md border flex items-center justify-center cursor-pointer overflow-hidden ${isPublic ? 'text-slate-900 dark:text-white border-gray-100 dark:border-zinc-700' : 'text-themed border-zinc-100 dark:border-zinc-700'}`}
				title={t('theater.sorter.restart')}
			>
				<RotateCcw size={14} class="sm:hidden" />
				<RotateCcw size={18} class="hidden sm:block" />
			</button>
		</div>
	</div>

	{#key layoutMode}
		<div in:fade={{ duration: 400 }}>
			{#if layoutMode === 'card'}
				<div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-2 sm:gap-4">
					{#each results as member, i (member.id)}
						<div
							in:fly={{ y: 20, delay: i * 30, duration: 500, easing: quintOut }}
							class="relative group"
						>
							<div
								class={`aspect-[3/4] rounded-xl overflow-hidden border-2 transition-all group-hover:scale-105 group-hover:shadow-2xl cursor-pointer relative ${i <= 2 ? 'shiny-card' : ''} ${i === 0 ? 'border-yellow-400 shadow-xl shadow-yellow-400/20' : i === 1 ? 'border-slate-300 shadow-xl shadow-slate-300/20' : i === 2 ? 'border-amber-600 shadow-xl shadow-amber-700/10' : isPublic ? 'border-slate-100 dark:border-zinc-800 shadow-lg' : 'border-zinc-100 dark:border-zinc-800 shadow-lg'}`}
							>
								<OptimizedImage
									src={getExternalMediaUrl(member.img) || ''}
									alt={member.name}
									class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
								/>

								<img
									src={getMemberFrame(member.member_type) || ''}
									alt="member frame"
									class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
								/>

								<div
									class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
								></div>

								<div
									class={`absolute top-1.5 left-1.5 sm:top-3 sm:left-3 w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center font-black text-[10px] sm:text-sm z-30 shadow-lg ${i === 0 ? 'bg-yellow-400 text-yellow-900 border-2 border-yellow-200' : i === 1 ? 'bg-slate-300 text-slate-800 border-2 border-slate-100' : i === 2 ? 'bg-amber-700 text-white border-2 border-amber-500' : isPublic ? 'bg-white dark:bg-zinc-900 text-slate-900 dark:text-white border-2 border-slate-50 dark:border-zinc-800' : 'bg-white dark:bg-zinc-900 text-themed border-2 border-zinc-50 dark:border-zinc-800'}`}
								>
									{i + 1}
								</div>

								<div class="absolute bottom-2 left-2 right-2 sm:bottom-4 sm:left-4 sm:right-4 z-30">
									<h4
										class="font-black text-white text-[11px] leading-tight line-clamp-2 drop-shadow-md"
									>
										<span class="sm:hidden">{member.nickname}</span>
										<span class="hidden sm:inline">{member.name}</span>
									</h4>
									<span
										class="text-[7px] sm:text-[8px] font-black text-white/70 uppercase tracking-widest block -mt-0.5"
										>{t('theater.sorter.genLabel', { gen: member.generation })}</span
									>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="flex flex-col gap-0 max-w-3xl mx-auto w-full">
					<!-- Top 3 Podium -->
					<div class="grid grid-cols-3 items-end gap-2 sm:gap-4 mb-3 px-1 sm:px-4 max-w-xl mx-auto">
						<!-- Rank 1 -->
						{#if results[0]}
							<div
								in:fly={{ y: 20, delay: 0, duration: 500, easing: quintOut }}
								class="flex flex-col items-center group cursor-pointer -mt-12 sm:-mt-16 z-40 relative"
							>
								<div
									class={`relative w-full aspect-[3/4] rounded-xl overflow-hidden border-2 border-yellow-400 shadow-2xl shadow-yellow-400/30 transition-all group-hover:scale-105 group-hover:shadow-yellow-400/50 shiny-card`}
								>
									<OptimizedImage
										src={getExternalMediaUrl(results[0].img) || ''}
										alt={results[0].name}
										class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
									/>
									<img
										src={getMemberFrame(results[0].member_type) || ''}
										alt="frame"
										class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
									/>
									<div
										class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
									></div>
									<div
										class="absolute top-1.5 left-1.5 sm:top-3 sm:left-3 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-yellow-400 text-yellow-900 flex items-center justify-center font-black text-[10px] sm:text-sm z-30 border-2 border-yellow-200 shadow-lg"
									>
										1
									</div>

									<div
										class="absolute bottom-2 left-2 right-2 sm:bottom-4 sm:left-4 sm:right-4 z-30 text-left"
									>
										<h4
											class="font-black text-white text-[11px] leading-tight line-clamp-2 drop-shadow-md"
										>
											{results[0].name}
										</h4>
										<span
											class="text-[7px] sm:text-[8px] font-black text-white/70 uppercase tracking-widest block -mt-0.5"
											>{t('theater.sorter.genLabel', { gen: results[0].generation })}</span
										>
									</div>
								</div>
							</div>
						{/if}

						<!-- Rank 2 -->
						{#if results[1]}
							<div
								in:fly={{ y: 20, delay: 100, duration: 500, easing: quintOut }}
								class="flex flex-col items-center group cursor-pointer"
							>
								<div
									class={`relative w-full aspect-[3/4] rounded-xl overflow-hidden border-2 border-slate-300 shadow-xl shadow-slate-300/20 transition-all group-hover:scale-105 shiny-card`}
								>
									<OptimizedImage
										src={getExternalMediaUrl(results[1].img) || ''}
										alt={results[1].name}
										class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
									/>
									<img
										src={getMemberFrame(results[1].member_type) || ''}
										alt="frame"
										class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
									/>
									<div
										class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
									></div>
									<div
										class="absolute top-1.5 left-1.5 sm:top-3 sm:left-3 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-slate-300 text-slate-800 flex items-center justify-center font-black text-[10px] sm:text-sm z-30 border-2 border-slate-100 shadow-lg"
									>
										2
									</div>
									<div
										class="absolute bottom-2 left-2 right-2 sm:bottom-4 sm:left-4 sm:right-4 z-30 text-left"
									>
										<h4
											class="font-black text-white text-[11px] leading-tight line-clamp-2 drop-shadow-md"
										>
											{results[1].name}
										</h4>
										<span
											class="text-[7px] sm:text-[8px] font-black text-white/70 uppercase tracking-widest block -mt-0.5"
											>{t('theater.sorter.genLabel', { gen: results[1].generation })}</span
										>
									</div>
								</div>
							</div>
						{/if}

						<!-- Rank 3 -->
						{#if results[2]}
							<div
								in:fly={{ y: 20, delay: 200, duration: 500, easing: quintOut }}
								class="flex flex-col items-center group cursor-pointer"
							>
								<div
									class={`relative w-full aspect-[3/4] rounded-xl overflow-hidden border-2 border-amber-600 shadow-xl shadow-amber-700/10 transition-all group-hover:scale-105 group-hover:shadow-2xl shiny-card`}
								>
									<OptimizedImage
										src={getExternalMediaUrl(results[2].img) || ''}
										alt={results[2].name}
										class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
									/>
									<img
										src={getMemberFrame(results[2].member_type) || ''}
										alt="frame"
										class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
									/>
									<div
										class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
									></div>
									<div
										class="absolute top-1.5 left-1.5 sm:top-3 sm:left-3 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-amber-700 text-white flex items-center justify-center font-black text-[10px] sm:text-sm z-30 border-2 border-amber-500 shadow-lg"
									>
										3
									</div>
									<div
										class="absolute bottom-2 left-2 right-2 sm:bottom-4 sm:left-4 sm:right-4 z-30 text-left"
									>
										<h4
											class="font-black text-white text-[11px] leading-tight line-clamp-2 drop-shadow-md"
										>
											{results[2].name}
										</h4>
										<span
											class="text-[7px] sm:text-[8px] font-black text-white/70 uppercase tracking-widest block -mt-0.5"
											>{t('theater.sorter.genLabel', { gen: results[2].generation })}</span
										>
									</div>
								</div>
							</div>
						{/if}
					</div>

					{#if results.length > 3}
						<div class="grid grid-cols-1 md:grid-cols-2 gap-3 w-full">
							{#each results.slice(3) as member, i (member.id)}
								<div
									in:fly={{ y: 20, delay: (i + 3) * 30, duration: 500, easing: quintOut }}
									class={`flex items-center gap-3 bg-white dark:bg-zinc-900 rounded-xl p-2.5 border transition-all hover:scale-[1.02] hover:shadow-xl group relative overflow-hidden shadow-sm cursor-pointer ${isPublic ? 'border-slate-100 dark:border-zinc-800 hover:border-red-600' : 'border-zinc-100 dark:border-zinc-800 hover:border-rose-500'}`}
								>
									<div
										class={`rank-badge w-8 h-8 rounded-full flex items-center justify-center font-black text-xs shrink-0 z-30 bg-slate-100 dark:bg-zinc-800 border shadow-sm ${isPublic ? 'text-slate-900 dark:text-white border-slate-200 dark:border-zinc-700' : 'text-themed border-zinc-200 dark:border-zinc-700'}`}
									>
										{i + 4}
									</div>

									<div
										class="relative w-11 aspect-[3/4] rounded-lg overflow-hidden shrink-0 border border-slate-100 dark:border-zinc-800 transition-transform duration-500 z-30 shadow-sm"
									>
										<OptimizedImage
											src={getExternalMediaUrl(member.img) || ''}
											alt={member.name}
											class="w-full h-full object-cover"
										/>
										<img
											src={getMemberFrame(member.member_type) || ''}
											alt="member frame"
											class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10 opacity-80"
										/>
									</div>

									<div class="flex flex-col gap-0.5 z-30 min-w-0">
										<h4
											class={`font-black text-xs sm:text-sm tracking-tight leading-tight line-clamp-2 ${isPublic ? 'text-slate-900 dark:text-white' : 'text-themed'}`}
										>
											{member.name}
										</h4>
										<span
											class={`text-[9px] font-bold uppercase tracking-widest truncate ${isPublic ? 'text-slate-400' : 'text-themed-secondary'}`}
											>{t('theater.sorter.genLabel', { gen: member.generation })}</span
										>
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

<style>
	.shiny-card::after {
		content: '';
		position: absolute;
		top: -50%;
		left: -50%;
		width: 200%;
		height: 200%;
		background: linear-gradient(
			45deg,
			transparent 20%,
			rgba(255, 255, 255, 0.1) 35%,
			rgba(255, 255, 255, 0.2) 40%,
			rgba(255, 255, 255, 0.1) 45%,
			transparent 60%
		);
		transform: rotate(-45deg);
		animation: shine 6s infinite;
		pointer-events: none;
		z-index: 25;
	}

	@keyframes shine {
		0% {
			transform: translateX(-100%) rotate(-45deg);
		}
		20%,
		100% {
			transform: translateX(100%) rotate(-45deg);
		}
	}
</style>
