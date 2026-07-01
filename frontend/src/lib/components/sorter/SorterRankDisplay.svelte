<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { getMemberFrame } from '$lib/constants';
	import { OptimizedImage } from '$lib/components/common';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SorterCardBack from './SorterCardBack.svelte';

	const { t } = useTranslation();

	interface ResultMember {
		id: string | number;
		name: string;
		nickname?: string;
		img?: string;
		member_type?: string;
		generation?: string;
		rank?: number;
	}

	interface Props {
		results: ResultMember[];
		layoutMode: 'card' | 'list';
		isPublic?: boolean;
	}

	let { results, layoutMode, isPublic = false }: Props = $props();

	let flippedCards: Record<number, boolean> = $state({});
	let autoRevealStarted = false;

	function toggleFlip(index: number) {
		flippedCards = { ...flippedCards, [index]: !flippedCards[index] };
	}

	let autoRevealTimers: number[] = [];

	$effect.pre(() => {
		if (results.length > 0 && !autoRevealStarted) {
			autoRevealStarted = true;

			const initial: Record<number, boolean> = {};
			for (let i = 0; i < results.length; i++) {
				initial[i] = true;
			}
			flippedCards = initial;
		}
	});

	onMount(() => {
		if (results.length > 0 && autoRevealStarted) {
			const lastIdx = results.length - 1;

			// Top 3: rank 3, 2, 1 each 1s apart
			const top3Order = [2, 1, 0];
			let currentTime = 1000;

			for (const idx of top3Order) {
				if (idx < results.length) {
					autoRevealTimers.push(
						window.setTimeout(() => {
							flippedCards = { ...flippedCards, [idx]: false };
						}, currentTime)
					);
					currentTime += 1000;
				}
			}

			// Domino from rank 4 to last, gradually accelerating
			const startGap = 350;
			const minGap = 100;
			for (let i = 3; i < results.length; i++) {
				const progress = (i - 3) / Math.max(1, lastIdx - 3);
				const gap = Math.max(minGap, startGap - progress * (startGap - minGap));

				const idx = i;
				autoRevealTimers.push(
					window.setTimeout(() => {
						flippedCards = { ...flippedCards, [idx]: false };
					}, currentTime)
				);
				currentTime += gap;
			}
		}

		return () => {
			autoRevealTimers.forEach((t) => window.clearTimeout(t));
		};
	});
</script>

<div class="w-full">
	{#key layoutMode}
		<div in:fade={{ duration: 400 }}>
			{#if layoutMode === 'card'}
				<div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-2 sm:gap-4">
					{#each results as member, i (member.id)}
						<div
							in:fly={{ y: 20, delay: i * 20, duration: 500, easing: quintOut }}
							class="relative group cursor-pointer"
							onclick={() => toggleFlip(i)}
							onkeydown={(e) => e.key === 'Enter' && toggleFlip(i)}
							role="button"
							tabindex="0"
						>
							<div
								class={`aspect-[3/4] rounded-xl overflow-hidden border-2 transition-all relative ${!flippedCards[i] ? 'group-hover:scale-105 group-hover:shadow-2xl' : ''} ${i === 0 ? 'border-yellow-400 shadow-xl shadow-yellow-400/20' : i === 1 ? 'border-slate-300 shadow-xl shadow-slate-300/20' : i === 2 ? 'border-amber-600 shadow-xl shadow-amber-700/10' : isPublic ? 'border-slate-100 dark:border-zinc-800 shadow-lg' : 'border-zinc-100 dark:border-zinc-800 shadow-lg'}`}
							>
								{#if flippedCards[i]}
									<div
										in:fade={{ duration: 200 }}
										out:fade={{ duration: 200 }}
										class="absolute inset-0"
									>
										<SorterCardBack rank={member.rank || i + 1} />
									</div>
								{:else}
									<div
										in:fade={{ duration: 200 }}
										out:fade={{ duration: 200 }}
										class="absolute inset-0"
										class:shiny-card={i <= 2}
									>
										<OptimizedImage
											src={getExternalMediaUrl(member.img || '') || ''}
											alt={member.name}
											class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
										/>

										<img
											src={getMemberFrame(member.member_type || '') || ''}
											alt="member frame"
											class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
										/>

										<div
											class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
										></div>

										<div
											class={`absolute top-1.5 left-1.5 sm:top-3 sm:left-3 w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center font-black text-[10px] sm:text-sm z-30 shadow-lg ${i === 0 ? 'bg-yellow-400 text-yellow-900 border-2 border-yellow-200' : i === 1 ? 'bg-slate-300 text-slate-800 border-2 border-slate-100' : i === 2 ? 'bg-amber-700 text-white border-2 border-amber-500' : isPublic ? 'bg-white dark:bg-zinc-900 text-slate-900 dark:text-white border-2 border-slate-50 dark:border-zinc-800' : 'bg-white dark:bg-zinc-900 text-themed border-2 border-zinc-50 dark:border-zinc-800'}`}
										>
											{member.rank || i + 1}
										</div>

										<div
											class="absolute bottom-2 left-2 right-2 sm:bottom-4 sm:left-4 sm:right-4 z-30 text-left"
										>
											<h4
												class="font-black text-white text-[11px] leading-tight line-clamp-2 drop-shadow-md"
											>
												<span class="sm:hidden">{member.nickname || member.name}</span>
												<span class="hidden sm:inline">{member.name}</span>
											</h4>
											<span
												class="text-[7px] sm:text-[8px] font-black text-white/70 uppercase tracking-widest block -mt-0.5"
												>{t('theater.sorter.genLabel', { gen: member.generation || '' }) ||
													member.generation}</span
											>
										</div>
									</div>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="flex flex-col gap-0 max-w-3xl mx-auto w-full">
					<!-- Top 3 Podium -->
					<div class="grid grid-cols-3 items-end gap-2 sm:gap-4 mb-3 max-w-xl mx-auto w-full">
						<!-- Rank 1 -->
						{#if results[0]}
							<div
								in:fly={{ y: 20, delay: 0, duration: 500, easing: quintOut }}
								class="flex flex-col items-center group cursor-pointer -mt-12 sm:-mt-16 z-40 relative w-full"
								onclick={() => toggleFlip(0)}
								onkeydown={(e) => e.key === 'Enter' && toggleFlip(0)}
								role="button"
								tabindex="0"
							>
								<div
									class={`relative w-full aspect-[3/4] rounded-xl overflow-hidden border-2 border-yellow-400 shadow-2xl shadow-yellow-400/30 transition-all ${!flippedCards[0] ? 'group-hover:scale-105 group-hover:shadow-yellow-400/50' : ''}`}
								>
									{#if flippedCards[0]}
										<div
											in:fade={{ duration: 200 }}
											out:fade={{ duration: 200 }}
											class="absolute inset-0"
										>
											<SorterCardBack rank={results[0].rank || 1} />
										</div>
									{:else}
										<div
											in:fade={{ duration: 200 }}
											out:fade={{ duration: 200 }}
											class="absolute inset-0 shiny-card"
										>
											<OptimizedImage
												src={getExternalMediaUrl(results[0].img || '') || ''}
												alt={results[0].name}
												class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
											/>
											<img
												src={getMemberFrame(results[0].member_type || '') || ''}
												alt="frame"
												class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
											/>
											<div
												class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
											></div>
											<div
												class="absolute top-1.5 left-1.5 sm:top-3 sm:left-3 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-yellow-400 text-yellow-900 flex items-center justify-center font-black text-[10px] sm:text-sm z-30 border-2 border-yellow-200 shadow-lg"
											>
												{results[0].rank || 1}
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
													>{t('theater.sorter.genLabel', {
														gen: results[0].generation || ''
													}) || results[0].generation}</span
												>
											</div>
										</div>
									{/if}
								</div>
							</div>
						{/if}

						<!-- Rank 2 -->
						{#if results[1]}
							<div
								in:fly={{ y: 20, delay: 100, duration: 500, easing: quintOut }}
								class="flex flex-col items-center group cursor-pointer w-full"
								onclick={() => toggleFlip(1)}
								onkeydown={(e) => e.key === 'Enter' && toggleFlip(1)}
								role="button"
								tabindex="0"
							>
								<div
									class={`relative w-full aspect-[3/4] rounded-xl overflow-hidden border-2 border-slate-300 shadow-xl shadow-slate-300/20 transition-all ${!flippedCards[1] ? 'group-hover:scale-105' : ''}`}
								>
									{#if flippedCards[1]}
										<div
											in:fade={{ duration: 200 }}
											out:fade={{ duration: 200 }}
											class="absolute inset-0"
										>
											<SorterCardBack rank={results[1].rank || 2} />
										</div>
									{:else}
										<div
											in:fade={{ duration: 200 }}
											out:fade={{ duration: 200 }}
											class="absolute inset-0 shiny-card"
										>
											<OptimizedImage
												src={getExternalMediaUrl(results[1].img || '') || ''}
												alt={results[1].name}
												class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
											/>
											<img
												src={getMemberFrame(results[1].member_type || '') || ''}
												alt="frame"
												class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
											/>
											<div
												class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
											></div>
											<div
												class="absolute top-1.5 left-1.5 sm:top-3 sm:left-3 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-slate-300 text-slate-800 flex items-center justify-center font-black text-[10px] sm:text-sm z-30 border-2 border-slate-100 shadow-lg"
											>
												{results[1].rank || 2}
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
													>{t('theater.sorter.genLabel', {
														gen: results[1].generation || ''
													}) || results[1].generation}</span
												>
											</div>
										</div>
									{/if}
								</div>
							</div>
						{/if}

						<!-- Rank 3 -->
						{#if results[2]}
							<div
								in:fly={{ y: 20, delay: 200, duration: 500, easing: quintOut }}
								class="flex flex-col items-center group cursor-pointer w-full"
								onclick={() => toggleFlip(2)}
								onkeydown={(e) => e.key === 'Enter' && toggleFlip(2)}
								role="button"
								tabindex="0"
							>
								<div
									class={`relative w-full aspect-[3/4] rounded-xl overflow-hidden border-2 border-amber-600 shadow-xl shadow-amber-700/10 transition-all ${!flippedCards[2] ? 'group-hover:scale-105 group-hover:shadow-2xl' : ''}`}
								>
									{#if flippedCards[2]}
										<div
											in:fade={{ duration: 200 }}
											out:fade={{ duration: 200 }}
											class="absolute inset-0"
										>
											<SorterCardBack rank={results[2].rank || 3} />
										</div>
									{:else}
										<div
											in:fade={{ duration: 200 }}
											out:fade={{ duration: 200 }}
											class="absolute inset-0 shiny-card"
										>
											<OptimizedImage
												src={getExternalMediaUrl(results[2].img || '') || ''}
												alt={results[2].name}
												class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
											/>
											<img
												src={getMemberFrame(results[2].member_type || '') || ''}
												alt="frame"
												class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
											/>
											<div
												class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
											></div>
											<div
												class="absolute top-1.5 left-1.5 sm:top-3 sm:left-3 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-amber-700 text-white flex items-center justify-center font-black text-[10px] sm:text-sm z-30 border-2 border-amber-500 shadow-lg"
											>
												{results[2].rank || 3}
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
													>{t('theater.sorter.genLabel', {
														gen: results[2].generation || ''
													}) || results[2].generation}</span
												>
											</div>
										</div>
									{/if}
								</div>
							</div>
						{/if}
					</div>

					{#if results.length > 3}
						<div class="grid grid-cols-1 md:grid-cols-2 gap-3 w-full">
							{#each results.slice(3) as member, i (member.id)}
								{@const idx = i + 3}
								<div
									in:fly={{ y: 20, delay: idx * 30, duration: 500, easing: quintOut }}
									class={`flex items-center gap-3 bg-white dark:bg-zinc-900 rounded-xl p-2.5 border transition-all hover:scale-[1.02] hover:shadow-xl group relative overflow-hidden shadow-sm cursor-pointer ${isPublic ? 'border-slate-100 dark:border-zinc-800 hover:border-red-600' : 'border-zinc-100 dark:border-zinc-800 hover:border-red-600'}`}
									onclick={() => toggleFlip(idx)}
									onkeydown={(e) => e.key === 'Enter' && toggleFlip(idx)}
									role="button"
									tabindex="0"
								>
									<div
										class={`rank-badge w-8 h-8 rounded-full flex items-center justify-center font-black text-xs shrink-0 z-30 bg-slate-100 dark:bg-zinc-800 border shadow-sm ${isPublic ? 'text-slate-900 dark:text-white border-slate-200 dark:border-zinc-700' : 'text-themed border-zinc-200 dark:border-zinc-700'}`}
									>
										{member.rank || i + 4}
									</div>

									<div
										class="relative w-11 aspect-[3/4] rounded-lg overflow-hidden shrink-0 border border-slate-100 dark:border-zinc-800 z-30 shadow-sm"
										style="container-type:inline-size"
									>
										{#if flippedCards[idx]}
											<div
												in:fade={{ duration: 200 }}
												out:fade={{ duration: 200 }}
												class="absolute inset-0"
											>
												<SorterCardBack rank={member.rank || i + 4} />
											</div>
										{:else}
											<div
												in:fade={{ duration: 200 }}
												out:fade={{ duration: 200 }}
												class="absolute inset-0 shiny-card"
											>
												<OptimizedImage
													src={getExternalMediaUrl(member.img || '') || ''}
													alt={member.name}
													class="w-full h-full object-cover"
												/>
												<img
													src={getMemberFrame(member.member_type || '') || ''}
													alt="member frame"
													class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10 opacity-80"
												/>
											</div>
										{/if}
									</div>

									<div class="flex flex-col gap-0.5 z-30 min-w-0">
										<h4
											class={`font-black text-xs sm:text-sm tracking-tight leading-tight line-clamp-2 ${isPublic ? 'text-slate-900 dark:text-white' : 'text-themed'}`}
										>
											{member.name}
										</h4>
										<span
											class={`text-[9px] font-bold uppercase tracking-widest truncate ${isPublic ? 'text-slate-400' : 'text-themed-secondary'}`}
											>{t('theater.sorter.genLabel', { gen: member.generation || '' }) ||
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
