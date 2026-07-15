<script lang="ts">
	import { page } from '$app/stores';
	import { liveHistoryDetailStore } from '$lib/stores/liveHistoryDetail.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		formatTimeAgo,
		parseUTCDate,
		formatDateOnly,
		formatTimeOnly as formatTimeHelper,
		formatDurationSeconds
	} from '$lib/utils/time';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { formatGoldToIdr } from '$lib/utils/formatting';
	import { spring } from 'svelte/motion';
	import type { ReplayDetailResponse } from '$lib/types/replay';
	import SEO from '$lib/components/SEO.svelte';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import {
		OptimizedImage,
		ImageLightbox,
		LottieAnimation,
		RiveAnimation
	} from '$lib/components/common';
	import {
		MessageCircle,
		Gift,
		Image,
		Clock,
		Crown,
		Eye,
		History,
		Calendar,
		Video,
		ChevronLeft,
		ChevronRight,
		Mail,
		Play,
		Info
	} from 'lucide-svelte';

	const { t, locale } = useTranslation();

	let liveId = $derived($page.params.live_id || '');
	let replayData = $derived(liveHistoryDetailStore.data[liveId]);
	let loading = $derived(liveHistoryDetailStore.loading[liveId] ?? false);
	let error = $derived(liveHistoryDetailStore.error[liveId] ?? null);

	let isShowroom = $derived(replayData?.platform === 'showroom');

	let replayBasePath = $derived(
		$page.url.pathname.startsWith('/jkt48/') ? '/jkt48/live/replay' : '/live/replay'
	);

	function isLottieUrl(url: string): boolean {
		return url.includes('/animation/') || !url.match(/\.(png|jpg|jpeg|webp|gif|svg)(\?|#|$)/i);
	}

	let scrollY = $state(0);
	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));
	let screenshotsContainer = $state<HTMLDivElement | null>(null);

	let showLightbox = $state(false);
	let lightboxIndex = $state(0);

	let allImages = $derived.by(() => {
		if (!replayData) return [];
		const imgs: string[] = [];
		if (replayData.image) imgs.push(replayData.image);
		if (replayData.files?.screenshots) imgs.push(...replayData.files.screenshots);
		return imgs;
	});

	function openLightbox(index: number) {
		lightboxIndex = index;
		showLightbox = true;
	}

	function scrollScreenshots(direction: 'left' | 'right') {
		if (screenshotsContainer) {
			const scrollAmount = direction === 'left' ? -300 : 300;
			screenshotsContainer.scrollBy({ left: scrollAmount, behavior: 'smooth' });
		}
	}

	$effect(() => {
		if (liveId) {
			liveHistoryDetailStore.loadDetail(liveId);
		}
	});

	function formatDate(dateStr?: string) {
		return formatDateOnly(dateStr, locale.value);
	}

	function formatDuration(seconds: number) {
		return formatDurationSeconds(seconds, true)
			.replace(/0(\d)h/, '$1h')
			.replace(/ 0(\d)m/, ' $1m')
			.replace(/ 0(\d)s/, ' $1s');
	}

	function formatTimeOnly(dateStr?: string | null) {
		return formatTimeHelper(dateStr, locale.value);
	}

	function getEndTime(data: ReplayDetailResponse) {
		if (data.end_at) return data.end_at;
		if (data.start_at && data.duration) {
			const start = parseUTCDate(data.start_at).getTime();
			return new Date(start + data.duration * 1000).toISOString();
		}
		if (data.start_at && data.duration_seconds) {
			const start = parseUTCDate(data.start_at).getTime();
			return new Date(start + data.duration_seconds * 1000).toISOString();
		}
		return null;
	}
</script>

<SEO
	title={replayData?.member_name || 'Live Detail'}
	path={$page.url.pathname}
	description={replayData
		? `${replayData.member_name} - ${replayData.title || 'Live streaming'} di ${replayData.platform}. ${replayData.view_num?.toLocaleString() || 0} views, ${replayData.total_chats?.toLocaleString() || 0} chats, ${replayData.total_gifts?.toLocaleString() || 0} gifts.`
		: undefined}
	image={replayData?.image || replayData?.member?.img || undefined}
	keywords={`JKT48, ${replayData?.member_name || ''}, ${replayData?.platform || 'Live'}, Live Streaming, Riwayat Live, ${replayData?.title || ''}`}
/>

<div
	role="region"
	class="h-full w-full flex flex-col overflow-hidden bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900"
	onmousemove={(e) => {
		const { clientX, clientY } = e;
		const { innerWidth, innerHeight } = window;
		mouse.set({ x: clientX / innerWidth - 0.5, y: clientY / innerHeight - 0.5 });
	}}
>
	<AppBackground hideDecorationsOnMobile={true} interactive={true} bind:mouse bind:scrollY />

	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-28 relative z-10">
			{#if loading}
				<div class="animate-pulse">
					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 mb-6"
					>
						<div class="flex flex-col lg:flex-row items-start justify-between gap-6 lg:gap-8">
							<div
								class="flex flex-row lg:flex-col items-start gap-4 sm:gap-5 w-full lg:w-36 xl:w-44"
							>
								<div
									class="w-24 sm:w-28 xl:w-32 aspect-[3/4] rounded-xl bg-zinc-200 dark:bg-zinc-700 shrink-0 border-[3px] sm:border-4 border-zinc-200 dark:border-zinc-700"
								></div>
								<div class="flex flex-col flex-1 lg:w-full gap-2 py-1">
									<div class="flex items-center gap-3 mb-2">
										<div class="w-16 h-5 rounded bg-zinc-200 dark:bg-zinc-700"></div>
										<div class="w-24 h-4 rounded bg-zinc-200 dark:bg-zinc-700"></div>
									</div>
									<div class="w-40 h-7 rounded bg-zinc-200 dark:bg-zinc-700"></div>
									<div class="w-28 h-4 rounded bg-zinc-200 dark:bg-zinc-700 mt-1"></div>
									<div class="w-full h-4 rounded bg-zinc-200 dark:bg-zinc-700 mt-2"></div>
									<div class="w-3/4 h-4 rounded bg-zinc-200 dark:bg-zinc-700 mt-1"></div>
									<div
										class="hidden lg:block w-32 h-9 rounded-full bg-zinc-200 dark:bg-zinc-700 mt-3"
									></div>
								</div>
							</div>
							<div class="lg:hidden w-full h-11 rounded-full bg-zinc-200 dark:bg-zinc-700"></div>
							<div class="flex-1 w-full flex flex-col sm:flex-row gap-5 sm:gap-6">
								<div class="w-full lg:w-[320px] space-y-6">
									<div>
										<div class="w-20 h-4 rounded bg-zinc-200 dark:bg-zinc-700 mb-4"></div>
										<div class="grid grid-cols-2 gap-4 sm:gap-6">
											<div>
												<div class="w-12 h-3 rounded bg-zinc-200 dark:bg-zinc-700 mb-2"></div>
												<div class="w-20 h-5 rounded bg-zinc-200 dark:bg-zinc-700"></div>
												<div class="w-28 h-3 rounded bg-zinc-200 dark:bg-zinc-700 mt-2"></div>
											</div>
											<div>
												<div class="w-12 h-3 rounded bg-zinc-200 dark:bg-zinc-700 mb-2"></div>
												<div class="w-20 h-5 rounded bg-zinc-200 dark:bg-zinc-700"></div>
												<div class="w-28 h-3 rounded bg-zinc-200 dark:bg-zinc-700 mt-2"></div>
											</div>
											<div>
												<div class="w-12 h-3 rounded bg-zinc-200 dark:bg-zinc-700 mb-2"></div>
												<div class="w-16 h-5 rounded bg-zinc-200 dark:bg-zinc-700"></div>
											</div>
										</div>
									</div>
									<div class="border-t border-zinc-100 dark:border-zinc-800 pt-6">
										<div class="w-20 h-4 rounded bg-zinc-200 dark:bg-zinc-700 mb-4"></div>
										<div class="grid grid-cols-2 gap-4 sm:gap-6">
											<div>
												<div class="w-12 h-3 rounded bg-zinc-200 dark:bg-zinc-700 mb-2"></div>
												<div class="w-16 h-5 rounded bg-zinc-200 dark:bg-zinc-700"></div>
											</div>
											<div>
												<div class="w-12 h-3 rounded bg-zinc-200 dark:bg-zinc-700 mb-2"></div>
												<div class="w-20 h-5 rounded bg-zinc-200 dark:bg-zinc-700"></div>
											</div>
											<div>
												<div class="w-12 h-3 rounded bg-zinc-200 dark:bg-zinc-700 mb-2"></div>
												<div class="w-16 h-5 rounded bg-zinc-200 dark:bg-zinc-700"></div>
											</div>
										</div>
									</div>
								</div>
								<div
									class="flex-1 min-w-0 border-t sm:border-t-0 sm:border-l border-zinc-100 dark:border-zinc-800 pt-4 sm:pt-0 sm:pl-6 mt-2 sm:mt-0"
								>
									<div class="flex items-center justify-between mb-2 px-1">
										<div class="w-28 h-4 rounded bg-zinc-200 dark:bg-zinc-700"></div>
										<div class="w-20 h-5 rounded bg-zinc-200 dark:bg-zinc-700"></div>
									</div>
									<div class="flex gap-3 sm:gap-4 overflow-hidden">
										<div
											class="shrink-0 h-40 w-[90px] sm:h-80 sm:w-[180px] rounded-xl bg-zinc-200 dark:bg-zinc-700"
										></div>
										<div
											class="shrink-0 h-40 w-[90px] sm:h-80 sm:w-[180px] rounded-xl bg-zinc-200 dark:bg-zinc-700"
										></div>
										<div
											class="shrink-0 h-40 w-[90px] sm:h-80 sm:w-[180px] rounded-xl bg-zinc-200 dark:bg-zinc-700"
										></div>
									</div>
								</div>
							</div>
						</div>
					</div>
					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 mb-6"
					>
						<div class="w-28 h-6 rounded bg-zinc-200 dark:bg-zinc-700 mb-4"></div>
						<div class="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-3">
							{#each [1, 2, 3, 4] as item (item)}
								<div
									class="flex items-center gap-3 p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700"
								>
									<div class="w-10 h-10 rounded-full bg-zinc-200 dark:bg-zinc-700 shrink-0"></div>
									<div class="flex-1 space-y-1">
										<div class="w-24 h-4 rounded bg-zinc-200 dark:bg-zinc-700"></div>
										<div class="w-16 h-3 rounded bg-zinc-200 dark:bg-zinc-700"></div>
										<div class="w-20 h-3 rounded bg-zinc-200 dark:bg-zinc-700"></div>
									</div>
								</div>
							{/each}
						</div>
					</div>
					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 mb-6"
					>
						<div class="w-24 h-6 rounded bg-zinc-200 dark:bg-zinc-700 mb-4"></div>
						<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
							{#each [1, 2, 3, 4] as item (item)}
								<div
									class="flex items-center justify-between p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700"
								>
									<div class="flex items-center gap-2 flex-1">
										<div class="w-11 h-11 rounded bg-zinc-200 dark:bg-zinc-700 shrink-0"></div>
										<div class="w-20 h-4 rounded bg-zinc-200 dark:bg-zinc-700"></div>
										<div class="w-8 h-3 rounded bg-zinc-200 dark:bg-zinc-700 shrink-0"></div>
									</div>
									<div class="w-16 h-4 rounded bg-zinc-200 dark:bg-zinc-700"></div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			{:else if error}
				<div
					class="flex flex-col items-center justify-center py-24 sm:py-32 px-4 text-center max-w-md mx-auto"
				>
					<div
						class="w-20 h-20 bg-zinc-100 dark:bg-zinc-900 rounded-full flex items-center justify-center mb-6 shadow-sm border border-zinc-200 dark:border-zinc-800"
					>
						<History size={36} class="text-zinc-400 dark:text-zinc-500" />
					</div>
					<h3 class="text-xl font-black text-slate-800 dark:text-white mb-3">
						{t('liveHistory.detail.errorTitle') || 'Detail Live Tidak Tersedia'}
					</h3>
					<p class="text-sm font-medium text-zinc-500 dark:text-zinc-400 leading-relaxed mb-8">
						{t('liveHistory.detail.errorDesc') ||
							'Mohon maaf, data statistik, chat, dan detail tangkapan layar untuk live ini belum didukung atau tidak ditemukan di sistem.'}
					</p>
					<button
						class="px-6 py-2.5 bg-red-500 hover:bg-red-600 text-white text-sm font-bold rounded-full transition-colors shadow-sm cursor-pointer"
						onclick={() => history.back()}
					>
						<div class="flex items-center gap-2">
							<ChevronLeft size={16} />
							{t('liveHistory.detail.back') || 'Kembali'}
						</div>
					</button>
				</div>
			{:else if replayData}
				{@const data = replayData}
				<!-- Header Profile -->
				<div
					class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 mb-6 relative overflow-hidden group flex flex-col"
				>
					<div
						class="absolute -right-4 -bottom-4 opacity-[0.03] dark:opacity-[0.02] pointer-events-none z-0"
					>
						<History size={150} />
					</div>

					<div
						class="flex flex-col lg:flex-row items-start justify-between gap-6 lg:gap-8 z-10 relative"
					>
						<div
							class="flex flex-row lg:flex-col items-start gap-4 sm:gap-5 shrink-0 w-full lg:w-36 xl:w-44"
						>
							{#if data.member?.img}
								<div
									class="relative w-24 sm:w-28 xl:w-32 aspect-[3/4] rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center shrink-0 overflow-hidden shadow-sm border-[3px] sm:border-4 border-red-500"
								>
									<OptimizedImage
										src={getExternalMediaUrl(data.member.img)}
										alt={data.member_name}
										class="absolute inset-0 w-full h-full object-cover"
										sizes="128px"
									/>
								</div>
							{:else if data.image}
								<div
									class="relative w-24 sm:w-28 xl:w-32 aspect-[3/4] rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center shrink-0 overflow-hidden shadow-sm border-[3px] sm:border-4 border-red-500"
								>
									<OptimizedImage
										src={data.image}
										srcMedium={data.image_medium}
										srcSmall={data.image_small}
										blurHash={data.blurHash}
										alt={data.member_name}
										class="absolute inset-0 w-full h-full object-cover"
										sizes="128px"
									/>
								</div>
							{/if}
							<div
								class="flex flex-col min-w-0 flex-1 lg:w-full justify-center lg:justify-start py-1 lg:py-0"
							>
								<div class="flex items-center gap-3 mb-2">
									<PlatformLogo platform={data.platform} size="sm" />
									{#if data.start_at}
										<div class="flex items-center gap-1.5 text-xs font-bold text-zinc-400">
											<History size={12} />
											<span>{formatTimeAgo(data.start_at, t)}</span>
										</div>
									{/if}
								</div>

								{#if data.member?.id && data.member_name?.toUpperCase() !== 'JKT48'}
									<a
										href={$page.url.pathname.startsWith('/jkt48')
											? `/jkt48/members?id=${data.member.id}`
											: `/theater/members/${data.member.id}`}
										class="group/member block w-fit"
									>
										<h1
											class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white leading-tight group-hover/member:text-red-500 transition-colors"
										>
											{data.member_name}
										</h1>
										{#if data.member_nickname}
											<p
												class="text-sm font-medium text-zinc-500 dark:text-zinc-400 mt-0.5 group-hover/member:text-red-400 transition-colors"
											>
												@{data.member_nickname}
											</p>
										{/if}
									</a>
								{:else}
									<h1
										class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white leading-tight"
									>
										{data.member_name}
									</h1>

									{#if data.member_nickname}
										<p class="text-sm font-medium text-zinc-500 dark:text-zinc-400 mt-0.5">
											@{data.member_nickname}
										</p>
									{/if}
								{/if}

								{#if data.title}
									<p
										class="text-xs sm:text-sm font-medium text-zinc-600 dark:text-zinc-300 mt-2 line-clamp-2"
									>
										{data.title}
									</p>
								{/if}
								{#if data.youtube_id}
									<a
										href="{replayBasePath}/{data.youtube_id}"
										data-sveltekit-preload-data
										class="hidden lg:inline-flex items-center gap-2 mt-3 px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-xs font-bold rounded-full transition-colors shadow-sm w-fit"
									>
										<Play size={14} />
										{t('liveHistory.detail.watchReplay') || 'Watch Replay'}
									</a>
								{/if}
							</div>
						</div>

						{#if data.youtube_id}
							<a
								href="{replayBasePath}/{data.youtube_id}"
								data-sveltekit-preload-data
								class="lg:hidden inline-flex items-center justify-center gap-2 mt-3 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white text-xs font-bold rounded-full transition-colors shadow-sm w-full"
							>
								<Play size={14} />
								{t('liveHistory.detail.watchReplay') || 'Watch Replay'}
							</a>
						{/if}

						<!-- Right Side: Waktu Siaran, Stats, Screenshots -->
						<div class="flex-1 w-full flex flex-col sm:flex-row gap-5 sm:gap-6 min-w-0">
							<div class="shrink-0 flex flex-col gap-6 w-full lg:w-[320px]">
								<div class="flex flex-col justify-start">
									<h2
										class="text-xs font-black text-zinc-400 uppercase tracking-wider flex items-center gap-1.5 mb-4"
									>
										<Clock size={14} class="text-zinc-400" />
										{t('liveHistory.detail.broadcast') || 'Siaran'}
									</h2>

									<div class="grid grid-cols-2 gap-4 sm:gap-6">
										<div>
											<p class="text-[10px] font-bold text-zinc-400 uppercase mb-1">
												{t('liveHistory.detail.stats.start') || 'Mulai'}
											</p>
											<div
												class="flex items-center gap-2 text-base font-black text-slate-700 dark:text-zinc-200 leading-none"
											>
												<Calendar size={16} class="text-purple-500" />
												{formatTimeOnly(data.start_at)}
											</div>
											<p class="text-[10px] font-medium text-zinc-500 mt-1">
												{formatDate(data.start_at)}
											</p>
										</div>

										<div>
											<p class="text-[10px] font-bold text-zinc-400 uppercase mb-1">
												{t('liveHistory.detail.stats.end') || 'Selesai'}
											</p>
											<div
												class="flex items-center gap-2 text-base font-black text-slate-700 dark:text-zinc-200 leading-none"
											>
												<Calendar size={16} class="text-purple-500" />
												{formatTimeOnly(getEndTime(data))}
											</div>
											<p class="text-[10px] font-medium text-zinc-500 mt-1">
												{formatDate(getEndTime(data) || undefined)}
											</p>
										</div>

										<div>
											<p class="text-[10px] font-bold text-zinc-400 uppercase mb-1">
												{t('liveHistory.detail.stats.duration') || 'Durasi'}
											</p>
											<div
												class="flex items-center gap-2 text-base font-black text-slate-700 dark:text-zinc-200 leading-none"
											>
												<Clock size={16} class="text-red-500" />
												{formatDuration(data.duration || data.duration_seconds)}
											</div>
										</div>

										{#if data.duration && data.duration_seconds && Math.abs(data.duration - data.duration_seconds) > 60}
											<div>
												<div class="flex items-center gap-1 mb-1">
													<p class="text-[10px] font-bold text-zinc-400 uppercase">
														{t('liveHistory.detail.stats.recording') || 'Rekaman'}
													</p>
													<button
														type="button"
														class="group/info relative cursor-help focus:outline-none inline-flex items-center justify-center"
													>
														<Info class="w-3 h-3 text-zinc-400 hover:text-zinc-500" />
														<div
															class="absolute bottom-full left-1/2 -translate-x-[85%] sm:-translate-x-1/2 mb-2 w-48 p-2 bg-gray-800 text-white text-[10px] rounded shadow-lg opacity-0 invisible group-hover/info:opacity-100 group-hover/info:visible group-focus/info:opacity-100 group-focus/info:visible transition-all z-50 text-center pointer-events-none font-normal normal-case tracking-normal leading-relaxed"
														>
															{t('liveHistory.detail.stats.recordingInfo') ||
																'Auto rekam live bisa saja mengalami keterlambatan dalam merekam live member'}
															<div
																class="absolute top-full left-[85%] sm:left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-800"
															></div>
														</div>
													</button>
												</div>
												<div
													class="flex items-center gap-2 text-base font-black text-slate-700 dark:text-zinc-200 leading-none"
												>
													<Video size={16} class="text-zinc-500" />
													{formatDuration(data.duration_seconds)}
												</div>
											</div>
										{/if}
									</div>
								</div>

								<div
									class="flex flex-col justify-start border-t border-zinc-100 dark:border-zinc-800 pt-6"
								>
									<h2
										class="text-xs font-black text-zinc-400 uppercase tracking-wider flex items-center gap-1.5 mb-4"
									>
										<Crown size={14} class="text-zinc-400" />
										{t('liveHistory.detail.stats.title') || 'Statistik'}
									</h2>

									<div class="grid grid-cols-2 gap-4 sm:gap-6">
										<div>
											<p class="text-[10px] font-bold text-zinc-400 uppercase mb-1">
												{t('liveHistory.detail.stats.views') || 'Views'}
											</p>
											<div
												class="flex items-center gap-2 text-base font-black text-slate-700 dark:text-zinc-200 leading-none"
											>
												<Eye size={16} class="text-emerald-500" />
												{data.view_num ? data.view_num.toLocaleString() : '0'}
											</div>
										</div>

										{#if data.total_gifts > 0}
											<div>
												<p class="text-[10px] font-bold text-zinc-400 uppercase mb-1">
													{t('liveHistory.detail.stats.gifts') || 'Gifts'}
												</p>
												<div
													class="flex flex-wrap items-center gap-1.5 text-base font-black text-slate-700 dark:text-zinc-200 leading-none"
												>
													<Gift size={16} class="text-amber-500" />
													<span>{data.total_gifts.toLocaleString()}</span>
													{#if data.total_gold}
														<span class="text-xs font-bold text-amber-500 ml-0.5">
															({data.total_gold.toLocaleString()} Gold)
														</span>
													{/if}
												</div>
												{#if data.total_gold}
													<div class="mt-0.5 flex">
														<span class="text-[10px] font-bold text-emerald-500 leading-none"
															>~ Rp {formatGoldToIdr(data.total_gold, isShowroom)}</span
														>
													</div>
												{/if}
											</div>
										{/if}

										<div>
											<p class="text-[10px] font-bold text-zinc-400 uppercase mb-1">
												{t('liveHistory.detail.stats.chats') || 'Chats'}
											</p>
											<div
												class="flex items-center gap-2 text-base font-black text-slate-700 dark:text-zinc-200 leading-none"
											>
												<MessageCircle size={16} class="text-blue-500" />
												{data.total_chats.toLocaleString()}
											</div>
										</div>

										{#if data.total_loveletters && data.total_loveletters > 0}
											<div>
												<p class="text-[10px] font-bold text-zinc-400 uppercase mb-1">
													Love Letters
												</p>
												<div
													class="flex items-center gap-2 text-base font-black text-slate-700 dark:text-zinc-200 leading-none"
												>
													<Mail size={16} class="text-rose-500" />
													{data.total_loveletters.toLocaleString()}
												</div>
											</div>
										{/if}

										{#if isShowroom && data.total_free_gifts && data.total_free_gifts > 0}
											<div>
												<p class="text-[10px] font-bold text-zinc-400 uppercase mb-1">Free Gifts</p>
												<div
													class="flex items-center gap-2 text-base font-black text-slate-700 dark:text-zinc-200 leading-none"
												>
													<Gift size={16} class="text-green-400" />
													{data.total_free_gifts.toLocaleString()}
												</div>
											</div>
										{/if}
									</div>
								</div>
							</div>

							<!-- Screenshots Carousel -->
							{#if (data.files.screenshots && data.files.screenshots.length > 0) || data.image}
								<div
									class="flex-1 min-w-0 border-t sm:border-t-0 sm:border-l border-zinc-100 dark:border-zinc-800 pt-4 sm:pt-0 sm:pl-6 mt-2 sm:mt-0"
								>
									<div class="flex items-center justify-between mb-2 px-1">
										<h2
											class="text-xs font-black text-zinc-400 uppercase tracking-wider flex items-center gap-1.5"
										>
											<Image size={14} class="text-zinc-400" />
											{t('liveHistory.detail.screenshots') || 'Screenshots'}
										</h2>
										<span
											class="text-[10px] font-bold text-zinc-400 uppercase bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded-md"
											>{(data.files.screenshots?.length || 0) + (data.image ? 1 : 0)}
											{t('liveHistory.detail.images') || 'Images'}</span
										>
									</div>
									<div class="relative w-full group/carousel">
										<div
											class="flex gap-3 sm:gap-4 overflow-x-auto pb-4 snap-x scrollbar-hide"
											style="mask-image: linear-gradient(to right, black 85%, transparent 100%); -webkit-mask-image: linear-gradient(to right, black 85%, transparent 100%);"
											bind:this={screenshotsContainer}
										>
											{#if data.image}
												<div
													class="shrink-0 h-40 w-[90px] sm:h-80 sm:w-[180px] rounded-xl overflow-hidden bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 snap-center shadow-sm hover:border-red-500/50 transition-colors cursor-pointer group/img relative"
													onclick={() => openLightbox(0)}
													onkeydown={(e) => e.key === 'Enter' && openLightbox(0)}
													role="button"
													tabindex="0"
												>
													<OptimizedImage
														src={data.image}
														srcMedium={data.image_medium}
														srcSmall={data.image_small}
														blurHash={data.blurHash}
														alt="Thumbnail"
														class="w-full h-full object-cover group-hover/img:scale-105 transition-transform duration-300"
														sizes="192px"
													/>
													<div
														class="absolute bottom-1.5 left-1.5 bg-black/60 text-white text-[10px] px-2 py-0.5 rounded font-bold uppercase backdrop-blur-sm z-10 border border-white/10"
													>
														{t('liveHistory.detail.cover') || 'Cover'}
													</div>
												</div>
											{/if}
											{#if data.files.screenshots}
												{#each data.files.screenshots as url, i (url)}
													{@const ssIndex = (data.image ? 1 : 0) + i}
													<div
														class="shrink-0 h-40 w-[90px] sm:h-80 sm:w-[180px] rounded-xl overflow-hidden bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 snap-center shadow-sm hover:border-red-500/50 transition-colors cursor-pointer group/img"
														onclick={() => openLightbox(ssIndex)}
														onkeydown={(e) => e.key === 'Enter' && openLightbox(ssIndex)}
														role="button"
														tabindex="0"
													>
														<img
															src={url}
															alt="Screenshot"
															class="w-full h-full object-cover group-hover/img:scale-105 transition-transform duration-300"
															loading="lazy"
														/>
													</div>
												{/each}
											{/if}
										</div>

										<button
											class="absolute left-2 top-1/2 -translate-y-[calc(50%+8px)] w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-black/50 text-white flex items-center justify-center opacity-0 group-hover/carousel:opacity-100 transition-opacity hover:bg-red-500 z-20 backdrop-blur-md border border-white/10 shadow-lg"
											onclick={() => scrollScreenshots('left')}
											aria-label="Scroll left"
										>
											<ChevronLeft size={24} />
										</button>
										<button
											class="absolute right-4 sm:right-8 top-1/2 -translate-y-[calc(50%+8px)] w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-black/50 text-white flex items-center justify-center opacity-0 group-hover/carousel:opacity-100 transition-opacity hover:bg-red-500 z-20 backdrop-blur-md border border-white/10 shadow-lg"
											onclick={() => scrollScreenshots('right')}
											aria-label="Scroll right"
										>
											<ChevronRight size={24} />
										</button>
									</div>
								</div>
							{/if}
						</div>
					</div>
				</div>

				<!-- Top Fans -->
				{#if data.top_fans.length > 0}
					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 mb-6"
					>
						<h2
							class="text-lg font-black text-slate-800 dark:text-white mb-4 flex items-center gap-2"
						>
							<Crown size={18} class="text-yellow-500" />
							{t('liveHistory.detail.topGifter') || 'Top Gifter'}
						</h2>
						<div class="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-3">
							{#each data.top_fans as fan, index (fan.user)}
								<div
									class="flex items-center gap-3 p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 hover:shadow-md transition-shadow"
								>
									<div class="relative shrink-0">
										{#if fan.avatar}
											<OptimizedImage
												src={fan.avatar}
												alt={fan.user}
												class="w-10 h-10 rounded-full object-cover shrink-0 border border-zinc-200 dark:border-zinc-600"
											/>
										{:else}
											<div
												class="w-10 h-10 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center text-sm font-bold text-zinc-500 dark:text-zinc-400 shrink-0"
											>
												{fan.user[0]?.toUpperCase() || '?'}
											</div>
										{/if}
										<div
											class="absolute -top-1.5 -left-1.5 min-w-[20px] h-5 px-1 rounded-full flex items-center justify-center text-[10px] font-black border-2 border-white dark:border-zinc-800 shadow-sm z-10 {index ===
											0
												? 'bg-amber-500 text-white'
												: index === 1
													? 'bg-slate-300 text-slate-800'
													: index === 2
														? 'bg-amber-700 text-white'
														: 'bg-zinc-200 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400'}"
										>
											{index + 1}
										</div>
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-xs font-bold text-slate-800 dark:text-white truncate">
											{fan.user}
										</p>
										{#if fan.total_gold > 0}
											<div class="flex items-center gap-2 mt-0.5">
												<span class="text-[10px] font-bold text-zinc-400 dark:text-zinc-500">
													{fan.count}x
												</span>
												<span class="text-[10px] font-bold text-amber-600 dark:text-amber-400">
													{fan.total_gold.toLocaleString()} gold
													<span class="text-emerald-500">
														(~ Rp {formatGoldToIdr(fan.total_gold, isShowroom)})
													</span>
												</span>
											</div>
										{/if}
										{#if isShowroom && fan.free_count}
											<div class="flex items-center gap-2 mt-0.5">
												<span class="text-[10px] font-bold text-zinc-400 dark:text-zinc-500">
													{fan.free_count}x
												</span>
												<span class="text-[10px] font-bold text-amber-600 dark:text-amber-400">
													{fan.free_gold!.toLocaleString()} point
													<span class="text-green-500">(free)</span>
												</span>
											</div>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Top Gifts -->
				{#if data.top_gifts.length > 0}
					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 mb-6"
					>
						<h2
							class="text-lg font-black text-slate-800 dark:text-white mb-4 flex items-center gap-2"
						>
							<Gift size={18} class="text-amber-500" />
							{t('liveHistory.detail.giftList') || 'Gift List'}
						</h2>
						<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
							{#each data.top_gifts as gift (gift.name)}
								<div
									class="flex items-center justify-between p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 hover:shadow-md transition-shadow"
								>
									<div class="flex items-center gap-2 min-w-0 flex-1 pr-2">
										{#if gift.image}
											{#if isLottieUrl(gift.image)}
												{#if gift.image.toLowerCase().endsWith('.riv')}
													<RiveAnimation
														src={gift.image}
														width="44px"
														height="44px"
														className="shrink-0"
													/>
												{:else}
													<LottieAnimation
														src={gift.image}
														speed={1}
														width="44px"
														height="44px"
														className="shrink-0"
													/>
												{/if}
											{:else}
												<img
													src={gift.image}
													alt={gift.name}
													class="w-11 h-11 object-contain shrink-0"
												/>
											{/if}
										{/if}
										<span
											class="font-bold text-sm text-slate-800 dark:text-white truncate"
											title={gift.name}
										>
											{gift.name}
										</span>
										<span class="text-[10px] font-bold text-zinc-400 dark:text-zinc-500 shrink-0">
											{gift.count}x
										</span>
									</div>
									<div class="flex flex-col items-end shrink-0">
										<span class="text-xs font-bold text-amber-600 dark:text-amber-400">
											{gift.total_gold.toLocaleString()}
											{isShowroom ? 'point' : 'gold'}
										</span>
										{#if gift.free === true}
											<span class="text-[10px] font-bold text-green-500 mt-0.5">Free</span>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>

<ImageLightbox
	images={allImages}
	currentIndex={lightboxIndex}
	onIndexChange={(i) => (lightboxIndex = i)}
	isOpen={showLightbox}
	onClose={() => (showLightbox = false)}
/>
