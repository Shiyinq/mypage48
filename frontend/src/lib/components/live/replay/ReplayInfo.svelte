<script lang="ts">
	import { liveHistoryDetailStore } from '$lib/stores/liveHistoryDetail.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatGoldToIdr } from '$lib/utils/formatting';
	import { Gift, Crown, Info } from 'lucide-svelte';
	import { OptimizedImage, LottieAnimation, RiveAnimation } from '$lib/components/common';

	let { liveId }: { liveId: string } = $props();

	const { t } = useTranslation();
	import { page } from '$app/stores';

	let data = $derived(liveHistoryDetailStore.data[liveId]);
	let loading = $derived(liveHistoryDetailStore.loading[liveId] ?? false);
	let error = $derived(liveHistoryDetailStore.error[liveId] ?? null);
	let isShowroom = $derived(data?.platform === 'SHOWROOM');
	let liveHistoryUrl = $derived(
		$page.url.pathname.startsWith('/jkt48/')
			? `/jkt48/live/history/live/${liveId}`
			: `/live/history/live/${liveId}`
	);

	$effect(() => {
		if (liveId) {
			liveHistoryDetailStore.loadDetail(liveId);
		}
	});

	function isLottieUrl(url: string): boolean {
		return url.includes('/animation/') || !url.match(/\.(png|jpg|jpeg|webp|gif|svg)(\?|#|$)/i);
	}
</script>

<div class="flex-1 overflow-y-auto bg-white dark:bg-zinc-950 p-4 min-h-0">
	{#if loading}
		<div class="flex flex-col items-center justify-center py-16 text-slate-400 gap-3">
			<div
				class="w-8 h-8 border-2 border-slate-300 dark:border-zinc-700 border-t-sky-500 rounded-full animate-spin"
			></div>
			<p class="text-[10px] font-bold tracking-widest uppercase">
				{t('common.loading') || 'Loading...'}
			</p>
		</div>
	{:else if error}
		<div class="flex flex-col items-center justify-center py-16 text-slate-400 gap-3 text-center">
			<Info size={32} class="text-slate-300 dark:text-zinc-700" />
			<p class="text-xs font-bold">{error || 'Failed to load info'}</p>
		</div>
	{:else if data}
		<div class="flex flex-col gap-6 pb-8">
			<!-- Prominent Total Gift -->
			{#if data.total_gifts > 0}
				<div
					class="p-4 rounded-2xl bg-amber-50 dark:bg-amber-500/10 border border-amber-100 dark:border-amber-500/20 flex flex-col items-center justify-center text-center gap-1 shadow-sm"
				>
					<p
						class="text-[10px] font-black uppercase tracking-widest text-amber-600 dark:text-amber-500"
					>
						{t('liveHistory.detail.stats.totalGifts') || 'Total Gifts'}
					</p>
					{#if data.total_gold}
						<div class="flex items-center gap-2 mt-1">
							<p class="text-2xl font-black text-emerald-600 dark:text-emerald-500 leading-none">
								~ Rp {formatGoldToIdr(data.total_gold, isShowroom)}
							</p>
						</div>
						<div class="flex items-center gap-1.5 mt-2 text-xs">
							<span class="font-bold text-amber-600 dark:text-amber-400 flex items-center gap-1"
								><Gift size={12} /> {data.total_gifts.toLocaleString()}</span
							>
							<span class="text-amber-300 dark:text-amber-700 font-black">&bull;</span>
							<span class="font-bold text-amber-600 dark:text-amber-400"
								>{data.total_gold.toLocaleString()} {isShowroom ? 'point' : 'Gold'}</span
							>
						</div>
					{:else}
						<div class="flex items-center gap-2 mt-1">
							<Gift size={18} class="text-amber-500" />
							<p class="text-2xl font-black text-slate-800 dark:text-zinc-100 leading-none">
								{data.total_gifts.toLocaleString()}
							</p>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Top Fans -->
			{#if data.top_fans?.length > 0}
				<div>
					<h4
						class="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-3 flex items-center gap-2"
					>
						<Crown size={12} />
						{t('liveHistory.detail.topGifter') || 'Top Gifter'}
					</h4>
					<div class="flex flex-col gap-2">
						{#each data.top_fans.slice(0, 10) as fan, i}
							<div
								class="flex items-center justify-between p-2 rounded-xl {i === 0
									? 'bg-amber-50 dark:bg-amber-500/10 border border-amber-200/50 dark:border-amber-500/20'
									: 'bg-slate-50 dark:bg-zinc-900'}"
							>
								<div class="flex items-center gap-2 min-w-0">
									<div
										class="w-7 h-7 rounded-full bg-slate-200 dark:bg-zinc-800 flex items-center justify-center text-[10px] font-black shrink-0 overflow-hidden {i ===
										0
											? 'text-amber-500'
											: 'text-slate-400'}"
									>
										{#if fan.avatar}
											<OptimizedImage
												src={fan.avatar}
												alt={fan.user}
												class="w-full h-full object-cover"
											/>
										{:else}
											{i + 1}
										{/if}
									</div>
									<span class="text-xs font-bold text-slate-700 dark:text-zinc-300 truncate"
										>{fan.user}</span
									>
								</div>
								{#if fan.total_gold > 0}
									<div class="text-right shrink-0">
										<p class="text-[9px] font-black text-amber-600 dark:text-amber-500">
											{fan.total_gold.toLocaleString()}
											{isShowroom ? 'point' : 'G'}
										</p>
										<p class="text-[8px] font-bold text-emerald-500 mt-0.5">
											~ Rp {formatGoldToIdr(fan.total_gold, isShowroom)}
										</p>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Top Gifts -->
			{#if data.top_gifts?.length > 0}
				<div>
					<h4
						class="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-3 flex items-center gap-2"
					>
						<Gift size={12} />
						{t('liveHistory.detail.giftList') || 'Gift List'}
					</h4>
					<div class="flex flex-col gap-2">
						{#each data.top_gifts.slice(0, 10) as gift}
							<div
								class="flex items-center justify-between p-2 rounded-xl bg-slate-50 dark:bg-zinc-900 border border-slate-100 dark:border-zinc-800"
							>
								<div class="flex items-center gap-2 min-w-0">
									<div
										class="w-7 h-7 rounded-full bg-slate-200 dark:bg-zinc-800 flex items-center justify-center shrink-0 overflow-hidden"
									>
										{#if gift.image}
											{#if isLottieUrl(gift.image)}
												{#if gift.image.toLowerCase().endsWith('.riv')}
													<RiveAnimation src={gift.image} width="28px" height="28px" />
												{:else}
													<LottieAnimation src={gift.image} speed={1} width="28px" height="28px" />
												{/if}
											{:else}
												<img src={gift.image} alt={gift.name} class="w-full h-full object-cover" />
											{/if}
										{:else}
											<Gift size={12} class="text-slate-400" />
										{/if}
									</div>
									<div class="min-w-0">
										<p
											class="text-xs font-bold text-slate-700 dark:text-zinc-300 truncate leading-none"
										>
											{gift.name}
										</p>
										<p class="text-[9px] font-bold text-zinc-400 dark:text-zinc-500 mt-0.5">
											{gift.count}x
										</p>
									</div>
								</div>
								<div class="text-right shrink-0">
									<p class="text-[9px] font-black text-amber-600 dark:text-amber-500">
										{gift.total_gold.toLocaleString()}
										{isShowroom ? 'point' : 'G'}
									</p>
									{#if gift.free === true}
										<p class="text-[8px] font-bold text-green-500 mt-0.5 uppercase tracking-widest">
											Free
										</p>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Link to Full History -->
			<a
				href={liveHistoryUrl}
				target="_blank"
				rel="noopener noreferrer"
				class="w-full flex flex-col sm:flex-row items-center justify-center gap-2 bg-slate-50 hover:bg-slate-100 dark:bg-zinc-900/80 dark:hover:bg-zinc-800 text-slate-700 dark:text-zinc-300 transition-colors rounded-xl py-3 px-4 border border-slate-200 dark:border-zinc-800 shadow-sm"
			>
				<p class="text-xs font-black uppercase tracking-widest">
					{t('common.viewDetails') || 'Detail Info'}
				</p>
			</a>
		</div>
	{/if}
</div>

<style>
	.overflow-y-auto {
		scrollbar-width: thin;
		scrollbar-color: transparent transparent;
	}

	.overflow-y-auto:hover {
		scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
	}

	:global(.dark) .overflow-y-auto:hover {
		scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
	}
</style>
