<script lang="ts">
	import { Trophy, LayoutGrid, List, Share2, RotateCcw } from 'lucide-svelte';
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
		onshare?: () => void;
		onrestart?: () => void;
		onchangeLayout?: (mode: 'card' | 'list') => void;
	}

	let {
		results,
		layoutMode = 'card',
		variant = 'public',
		onshare,
		onrestart,
		onchangeLayout
	}: Props = $props();

	function shareResults() {
		onshare?.();
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
		<div class="flex items-center gap-4">
			<div
				class={`w-12 h-12 rounded-2xl flex items-center justify-center text-white shadow-xl shrink-0 ${isPublic ? 'bg-red-600 shadow-red-500/20' : 'bg-rose-500 shadow-rose-500/20'}`}
			>
				<Trophy size={22} />
			</div>
			<div class="space-y-0.5">
				<h1
					class={`text-2xl md:text-3xl font-black tracking-tighter uppercase leading-none ${isPublic ? 'text-slate-900 dark:text-white' : 'text-themed'}`}
				>
					{t('theater.sorter.results')}
				</h1>
				<p
					class={`text-[10px] font-bold uppercase tracking-widest ${isPublic ? 'text-slate-400' : 'text-themed-secondary'}`}
				>
					{t('theater.sorter.resultsSubtitle')}
				</p>
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
				class={`h-9 sm:h-11 px-3 sm:px-6 text-white font-black rounded-full transition-all shadow-lg flex items-center gap-1.5 sm:gap-2 text-[10px] sm:text-xs cursor-pointer whitespace-nowrap overflow-hidden ${isPublic ? 'bg-red-600 hover:bg-red-700 shadow-red-500/20' : 'bg-rose-500 hover:bg-rose-600 shadow-rose-500/20'}`}
			>
				<Share2 size={14} class="sm:hidden" />
				<Share2 size={16} class="hidden sm:block" />
				{t('theater.sorter.share')}
			</button>
			<button
				onclick={restart}
				class={`h-9 sm:h-11 px-3 sm:px-6 bg-white dark:bg-zinc-800 font-black rounded-full transition-all shadow-md border flex items-center gap-1.5 sm:gap-2 text-[10px] sm:text-xs cursor-pointer whitespace-nowrap overflow-hidden ${isPublic ? 'text-slate-900 dark:text-white border-gray-100 dark:border-zinc-700' : 'text-themed border-zinc-100 dark:border-zinc-700'}`}
			>
				<RotateCcw size={14} class="sm:hidden" />
				<RotateCcw size={16} class="hidden sm:block" />
				{t('theater.sorter.restart')}
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
									<span class="text-[7px] sm:text-[8px] font-black text-white/70 uppercase tracking-widest block -mt-0.5"
										>{t('theater.sorter.genLabel', { gen: member.generation })}</span
									>
								</div>

								{#if i === 0}
									<div class="absolute top-1.5 right-1.5 sm:top-3 sm:right-3 z-30 scale-90 sm:scale-110">
										<Trophy size={16} class="sm:size-[18px] text-yellow-400 fill-current drop-shadow-lg" />
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
							class={`flex items-center gap-4 bg-white dark:bg-zinc-900 rounded-xl p-3 border-2 transition-all hover:scale-105 hover:shadow-2xl group relative overflow-hidden shadow-sm cursor-pointer mx-auto w-full max-w-2xl ${isPublic ? 'hover:border-red-600' : 'hover:border-rose-500'} ${i === 0 ? 'border-yellow-400 shadow-xl shadow-yellow-400/20' : i === 1 ? 'border-slate-300 shadow-xl shadow-slate-300/20' : 'border-amber-600 shadow-xl shadow-amber-700/10'}`}
						>
							<div
								class={`rank-badge w-8 h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center font-black text-sm md:text-base shrink-0 z-30 shadow-sm ${i === 0 ? 'bg-yellow-400 text-yellow-900' : i === 1 ? 'bg-slate-300 text-slate-800' : 'bg-amber-700 text-white'}`}
							>
								{i + 1}
							</div>

							<div
								class={`relative w-12 sm:w-14 aspect-[3/4] rounded-lg overflow-hidden shrink-0 border border-slate-100 dark:border-zinc-800 transition-transform duration-500 z-30 shadow-sm ${i <= 2 ? 'shiny-card' : ''}`}
							>
								<OptimizedImage
									src={getExternalMediaUrl(member.img) || ''}
									alt={member.name}
									class="w-full h-full object-cover"
								/>
								<img
									src={getMemberFrame(member.member_type) || ''}
									alt="member frame"
									class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
								/>
							</div>

							<div class="flex flex-col gap-0.5 z-30 min-w-0">
								<h4
									class={`font-black text-sm md:text-lg tracking-tight leading-tight line-clamp-2 ${isPublic ? 'text-slate-900 dark:text-white' : 'text-themed'}`}
								>
									{member.name}
								</h4>
								<span
									class={`text-[9px] md:text-xs font-bold uppercase tracking-widest truncate ${isPublic ? 'text-slate-400' : 'text-themed-secondary'}`}
									>{t('theater.sorter.genLabel', { gen: member.generation })}</span
								>
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
