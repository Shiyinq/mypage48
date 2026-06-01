<script lang="ts">
	import { untrack } from 'svelte';
	import { fly } from 'svelte/transition';
	import { liveStore, liveList, liveLoading } from '$lib/stores/live.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Users, Share2 } from 'lucide-svelte';
	import LiveGrid from '$lib/components/live/LiveGrid.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { showToast } from '$lib/stores';
	import { PromoBanner } from '$lib/components/common';

	const { t } = useTranslation();

	let initialLoading = $state(liveList.value.length === 0);

	async function copyLink() {
		try {
			const textToCopy = `${t('theater.live.share.shareText')} ${window.location.href}`;
			await navigator.clipboard.writeText(textToCopy);
			showToast(t('theater.live.share.toastSuccess'), 'success');
		} catch (err) {
			console.error('Failed to copy link:', err);
			showToast(t('theater.live.share.toastError'), 'error');
		}
	}

	function shareToX() {
		const shareText = encodeURIComponent(t('theater.live.share.shareText'));
		const shareUrl = encodeURIComponent(window.location.href);
		const twitterUrl = `https://twitter.com/intent/tweet?text=${shareText}&url=${shareUrl}`;
		window.open(twitterUrl, '_blank', 'noopener,noreferrer');
	}

	async function fetchLives() {
		try {
			await liveStore.loadLiveList();
		} finally {
			initialLoading = false;
		}
	}

	$effect(() => {
		untrack(() => {
			fetchLives();
		});
		const intervalId = setInterval(() => {
			liveStore.loadLiveList(true);
		}, 30000);

		return () => {
			clearInterval(intervalId);
		};
	});
</script>

<SEO
	title={t('theater.live.seoTitle')}
	description={t('theater.live.seoDescription')}
	path="/jkt48/live"
	keywords="JKT48 Live, JKT48 Showroom, JKT48 IDN Live, JKT48 Live Streaming, Multi-view JKT48"
/>

<div class="py-12 min-h-screen">
	<!-- Header Section -->
	<header class="mb-12" in:fly={{ y: -20, duration: 600 }}>
		<div class="max-w-7xl mx-auto px-0 sm:px-6 flex flex-col items-center">
			<div class="flex flex-col md:flex-row items-center justify-between w-full gap-6">
				<div class="flex-1 text-center md:text-left">
					<div
						class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-100 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-[10px] font-black uppercase tracking-widest mb-4"
					>
						<span class="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse"></span>
						{t('theater.live.onLive')}
					</div>
					<h1
						class="text-4xl sm:text-6xl font-black tracking-tighter text-slate-900 dark:text-white leading-[0.9]"
					>
						JKT48 <span class="text-red-600 italic">LIVE</span>
					</h1>
					<p class="text-slate-500 dark:text-slate-400 mt-4 font-medium max-w-lg">
						{t('theater.live.subtitle')}
					</p>
				</div>

				{#if liveList.value.length > 0}
					<div class="shrink-0 flex items-center">
						<a
							href="/jkt48/live/multiview"
							class="group relative flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 shadow-xl shadow-slate-200/50 dark:shadow-none hover:shadow-2xl hover:-translate-y-0.5 transition-all duration-300 overflow-hidden"
						>
							<div
								class="absolute inset-0 bg-gradient-to-r from-red-500/0 via-red-500/5 to-red-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"
							></div>

							<div
								class="w-8 h-8 rounded-xl bg-red-50 dark:bg-red-500/10 flex items-center justify-center text-red-600 group-hover:bg-red-600 group-hover:text-white transition-all duration-300"
							>
								<Users size={18} />
							</div>

							<div class="flex flex-col items-start leading-none gap-0.5">
								<span
									class="text-[10px] font-black uppercase tracking-widest text-slate-400 group-hover:text-red-600 transition-colors"
									>{t('theater.live.multiview.title')}</span
								>
								<span class="text-sm font-black tracking-tight text-slate-900 dark:text-white"
									>{t('theater.live.switchMultiview')}</span
								>
							</div>

							<div
								class="ml-2 w-5 h-5 rounded-lg bg-slate-100 dark:bg-zinc-800 flex items-center justify-center text-[10px] font-black text-slate-500"
							>
								{liveList.value.length}
							</div>
						</a>
					</div>
				{/if}
			</div>
		</div>
	</header>

	<PromoBanner
		title={t('theater.live.share.title')}
		desc={t('theater.live.share.description')}
		icon={Share2}
		storageKey="mypage48_share_banner_dismissed"
		class="max-w-7xl mx-auto px-4 sm:px-6 mb-10"
	>
		{#snippet actions()}
			<div
				class="grid grid-cols-2 gap-3.5 w-full sm:flex sm:items-center sm:gap-2.5 sm:w-auto z-10 shrink-0 mt-1 sm:mt-0"
			>
				<button
					class="w-full sm:w-auto py-2 px-5 bg-slate-900 dark:bg-white text-white dark:text-zinc-950 hover:bg-slate-800 dark:hover:bg-slate-100 active:scale-95 font-black uppercase tracking-widest text-[9px] rounded-2xl transition-all shadow-md cursor-pointer text-center"
					onclick={shareToX}
				>
					{t('theater.live.share.shareToX')}
				</button>
				<button
					class="w-full sm:w-auto py-2 px-5 bg-red-600 hover:bg-red-700 active:scale-95 text-white font-black uppercase tracking-widest text-[9px] rounded-2xl transition-all shadow-md shadow-red-500/20 cursor-pointer text-center"
					onclick={copyLink}
				>
					{t('theater.live.share.copyLink')}
				</button>
			</div>
		{/snippet}
	</PromoBanner>

	<div class="max-w-7xl mx-auto px-0 md:px-0">
		<LiveGrid liveList={liveList.value} loading={liveLoading.value} {initialLoading} />
	</div>
</div>
