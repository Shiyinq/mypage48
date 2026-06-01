<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { isImmersive } from '$lib/stores';
	import { ChevronLeft, LayoutGrid, List, Calendar } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { fly, fade } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import { getMemberFrame } from '$lib/constants';
	import { OptimizedImage } from '$lib/components/common';
	import { membersStore } from '$lib/stores/theater.svelte';
	import type { SorterResponse } from '$lib/apis/sorter';

	const { t, locale } = useTranslation();

	function formatDateTime(dateStr: string) {
		try {
			const d = new Date(dateStr);
			const localeMap: Record<string, string> = {
				id: 'id-ID',
				en: 'en-US',
				ja: 'ja-JP'
			};
			return d.toLocaleString(localeMap[locale.value] || 'id-ID', {
				dateStyle: 'medium',
				timeStyle: 'short'
			});
		} catch {
			return dateStr;
		}
	}

	interface Props {
		historyItem: SorterResponse;
		onback?: () => void;
	}

	let { historyItem, onback }: Props = $props();

	let layoutMode = $state<'card' | 'list'>('card');

	function resolveMember(id: string, name: string) {
		const found = membersStore.list.find((m) => String(m.id) === String(id));
		return {
			id,
			name: found?.name || name,
			nickname: found?.nickname || name,
			img: found?.img || '',
			member_type: found?.member_type || 'JKT48',
			generation: found?.generation || ''
		};
	}

	let resolvedResults = $derived(
		historyItem.results.map((item) => ({
			...item,
			...resolveMember(item.id, item.name)
		}))
	);

	onMount(() => {
		isImmersive.set(true);
		if (typeof window !== 'undefined') {
			document.body.style.overflow = 'hidden';
		}
	});

	onDestroy(() => {
		isImmersive.set(false);
		if (typeof window !== 'undefined') {
			document.body.style.overflow = '';
		}
	});
</script>

<div
	class="fixed inset-0 bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 flex flex-col overflow-hidden z-[40]"
	in:fade
>
	<!-- Top Navbar -->
	<div
		class="h-14 border-b border-gray-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md flex items-center justify-between px-4 z-50 shrink-0"
	>
		<div class="flex items-center gap-4">
			<button
				onclick={onback}
				class="flex items-center gap-2 text-slate-900 dark:text-white hover:text-red-600 dark:hover:text-red-400 transition-colors bg-transparent border-none p-0 cursor-pointer font-bold"
			>
				<ChevronLeft size={20} />
				<span class="font-black tracking-tighter text-sm uppercase"
					>{t('theater.sorter.backToHistory')}</span
				>
			</button>
		</div>

		<!-- Layout controllers -->
		<div class="flex items-center gap-2 sm:gap-3">
			<div
				class="flex bg-gray-50/50 dark:bg-zinc-800/30 backdrop-blur-md rounded-full p-1 border border-zinc-200 dark:border-zinc-800 shadow-inner"
			>
				<button
					onclick={() => (layoutMode = 'card')}
					class={`p-1.5 rounded-full transition-all cursor-pointer ${layoutMode === 'card' ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}
					title={t('theater.sorter.gridView')}
				>
					<LayoutGrid size={16} />
				</button>
				<button
					onclick={() => (layoutMode = 'list')}
					class={`p-1.5 rounded-full transition-all cursor-pointer ${layoutMode === 'list' ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}
					title={t('theater.sorter.listView')}
				>
					<List size={16} />
				</button>
			</div>
		</div>
	</div>

	<!-- Scrollable Content -->
	<div class="flex-1 overflow-y-auto px-4 py-8 flex flex-col items-center">
		<div
			class={`w-full space-y-8 px-1.5 sm:px-4 mx-auto pb-24 ${layoutMode === 'list' ? 'max-w-3xl' : 'max-w-6xl'}`}
		>
			<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
				<div class="flex items-center gap-4 flex-1 min-w-0 w-full">
					<div class="space-y-1 min-w-0 flex-1 w-full text-left">
						<div
							class="flex items-center gap-1.5 text-[10px] font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider mb-1"
						>
							<Calendar size={12} class="text-rose-500" />
							<span>{formatDateTime(historyItem.created_at)}</span>
						</div>
						<div class="flex items-center gap-2 w-full min-w-0">
							<h1
								class="text-2xl md:text-3xl font-black tracking-tighter uppercase leading-tight break-words min-w-0 text-themed"
							>
								{historyItem.title}
							</h1>
						</div>

						{#if historyItem.description}
							<div class="flex items-center gap-2 w-full min-w-0">
								<p
									class="text-xs font-semibold text-themed-secondary break-words min-w-0 leading-relaxed"
								>
									{historyItem.description}
								</p>
							</div>
						{/if}

						{#if historyItem.filters.length > 0}
							<div class="flex flex-wrap gap-1.5 pt-2">
								{#each historyItem.filters as gen}
									<span
										class="px-2.5 py-0.5 rounded-full text-[9px] font-black tracking-wider uppercase border bg-rose-50/50 dark:bg-rose-950/20 border-rose-100 dark:border-rose-900/30 text-rose-500 dark:text-rose-400 transition-all hover:scale-105 select-none"
									>
										{t('theater.sorter.genLabel', { gen })}
									</span>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			</div>

			{#key layoutMode}
				<div in:fade={{ duration: 400 }}>
					{#if layoutMode === 'card'}
						<div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-2 sm:gap-4">
							{#each resolvedResults as member, i (member.id)}
								<div
									in:fly={{ y: 20, delay: i * 20, duration: 500, easing: quintOut }}
									class="relative group"
								>
									<div
										class={`aspect-[3/4] rounded-xl overflow-hidden border-2 transition-all group-hover:scale-105 group-hover:shadow-2xl cursor-pointer relative ${i <= 2 ? 'shiny-card' : ''} ${i === 0 ? 'border-yellow-400 shadow-xl shadow-yellow-400/20' : i === 1 ? 'border-slate-300 shadow-xl shadow-slate-300/20' : i === 2 ? 'border-amber-600 shadow-xl shadow-amber-700/10' : 'border-zinc-100 dark:border-zinc-800 shadow-lg'}`}
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
											class={`absolute top-1.5 left-1.5 sm:top-3 sm:left-3 w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center font-black text-[10px] sm:text-sm z-30 shadow-lg ${i === 0 ? 'bg-yellow-400 text-yellow-900 border-2 border-yellow-200' : i === 1 ? 'bg-slate-300 text-slate-800 border-2 border-slate-100' : i === 2 ? 'bg-amber-700 text-white border-2 border-amber-500' : 'bg-white dark:bg-zinc-900 text-themed border-2 border-zinc-50 dark:border-zinc-800'}`}
										>
											{i + 1}
										</div>

										<div
											class="absolute bottom-2 left-2 right-2 sm:bottom-4 sm:left-4 sm:right-4 z-30 text-left"
										>
											<h4
												class="font-black text-white text-[11px] leading-tight line-clamp-2 drop-shadow-md"
											>
												<span class="sm:hidden">{member.nickname}</span>
												<span class="hidden sm:inline">{member.name}</span>
											</h4>
											<span
												class="text-[7px] sm:text-[8px] font-black text-white/70 uppercase tracking-widest block -mt-0.5"
												>{t('theater.sorter.genLabel', { gen: member.generation }) ||
													member.generation}</span
											>
										</div>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div class="flex flex-col gap-0 max-w-3xl mx-auto w-full">
							<!-- Top 3 Podium -->
							<div
								class="grid grid-cols-3 items-end gap-2 sm:gap-4 mb-3 px-1 sm:px-4 max-w-xl mx-auto"
							>
								<!-- Rank 1 -->
								{#if resolvedResults[0]}
									<div
										in:fly={{ y: 20, delay: 0, duration: 500, easing: quintOut }}
										class="flex flex-col items-center group cursor-pointer -mt-12 sm:-mt-16 z-40 relative"
									>
										<div
											class="relative w-full aspect-[3/4] rounded-xl overflow-hidden border-2 border-yellow-400 shadow-2xl shadow-yellow-400/30 transition-all group-hover:scale-105 group-hover:shadow-yellow-400/50 shiny-card"
										>
											<OptimizedImage
												src={getExternalMediaUrl(resolvedResults[0].img) || ''}
												alt={resolvedResults[0].name}
												class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
											/>
											<img
												src={getMemberFrame(resolvedResults[0].member_type) || ''}
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
													{resolvedResults[0].name}
												</h4>
												<span
													class="text-[7px] sm:text-[8px] font-black text-white/70 uppercase tracking-widest block -mt-0.5"
													>{t('theater.sorter.genLabel', { gen: resolvedResults[0].generation }) ||
														resolvedResults[0].generation}</span
												>
											</div>
										</div>
									</div>
								{/if}

								<!-- Rank 2 -->
								{#if resolvedResults[1]}
									<div
										in:fly={{ y: 20, delay: 100, duration: 500, easing: quintOut }}
										class="flex flex-col items-center group cursor-pointer"
									>
										<div
											class="relative w-full aspect-[3/4] rounded-xl overflow-hidden border-2 border-slate-300 shadow-xl shadow-slate-300/20 transition-all group-hover:scale-105 shiny-card"
										>
											<OptimizedImage
												src={getExternalMediaUrl(resolvedResults[1].img) || ''}
												alt={resolvedResults[1].name}
												class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
											/>
											<img
												src={getMemberFrame(resolvedResults[1].member_type) || ''}
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
													{resolvedResults[1].name}
												</h4>
												<span
													class="text-[7px] sm:text-[8px] font-black text-white/70 uppercase tracking-widest block -mt-0.5"
													>{t('theater.sorter.genLabel', { gen: resolvedResults[1].generation }) ||
														resolvedResults[1].generation}</span
												>
											</div>
										</div>
									</div>
								{/if}

								<!-- Rank 3 -->
								{#if resolvedResults[2]}
									<div
										in:fly={{ y: 20, delay: 200, duration: 500, easing: quintOut }}
										class="flex flex-col items-center group cursor-pointer"
									>
										<div
											class="relative w-full aspect-[3/4] rounded-xl overflow-hidden border-2 border-amber-600 shadow-xl shadow-amber-700/10 transition-all group-hover:scale-105 group-hover:shadow-2xl shiny-card"
										>
											<OptimizedImage
												src={getExternalMediaUrl(resolvedResults[2].img) || ''}
												alt={resolvedResults[2].name}
												class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
											/>
											<img
												src={getMemberFrame(resolvedResults[2].member_type) || ''}
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
													{resolvedResults[2].name}
												</h4>
												<span
													class="text-[7px] sm:text-[8px] font-black text-white/70 uppercase tracking-widest block -mt-0.5"
													>{t('theater.sorter.genLabel', { gen: resolvedResults[2].generation }) ||
														resolvedResults[2].generation}</span
												>
											</div>
										</div>
									</div>
								{/if}
							</div>

							{#if resolvedResults.length > 3}
								<div class="grid grid-cols-1 md:grid-cols-2 gap-3 w-full">
									{#each resolvedResults.slice(3) as member, i (member.id)}
										<div
											in:fly={{ y: 20, delay: (i + 3) * 20, duration: 500, easing: quintOut }}
											class="flex items-center gap-3 bg-white dark:bg-zinc-900 rounded-xl p-2.5 border border-zinc-100 dark:border-zinc-800 hover:border-rose-500 transition-all hover:scale-[1.02] hover:shadow-xl group relative overflow-hidden shadow-sm cursor-pointer"
										>
											<div
												class="rank-badge w-8 h-8 rounded-full flex items-center justify-center font-black text-xs shrink-0 z-30 bg-slate-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-themed shadow-sm"
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

											<div class="flex flex-col gap-0.5 z-30 min-w-0 text-left">
												<h4
													class="font-black text-xs sm:text-sm tracking-tight leading-tight line-clamp-2 text-themed"
												>
													{member.name}
												</h4>
												<span
													class="text-[9px] font-bold uppercase tracking-widest truncate text-themed-secondary"
													>{t('theater.sorter.genLabel', { gen: member.generation }) ||
														member.generation}</span
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
	</div>
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
