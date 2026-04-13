<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { fly } from 'svelte/transition';
	import { liveStore, liveList, liveLoading } from '$lib/stores/live';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Users } from 'lucide-svelte';
	import LiveGrid from '$lib/components/live/LiveGrid.svelte';
	import SEO from '$lib/components/SEO.svelte';

	const { t } = useTranslation();

	let interval: ReturnType<typeof setInterval> | null = null;

	let initialLoading = $state($liveList.length === 0);
	async function fetchLives() {
		await liveStore.loadLiveList();
		initialLoading = false;
	}

	onMount(() => {
		fetchLives();
		interval = setInterval(() => liveStore.loadLiveList(true), 30000);
	});

	onDestroy(() => {
		if (interval) clearInterval(interval);
	});
</script>

<SEO title={$t('theater.live.title')} description={$t('seo.live')} path="/jkt48/live" />

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
						{$t('theater.live.onLive')}
					</div>
					<h1
						class="text-4xl sm:text-6xl font-black tracking-tighter text-slate-900 dark:text-white leading-[0.9]"
					>
						JKT48 <span class="text-red-600 italic">LIVE</span>
					</h1>
					<p class="text-slate-500 dark:text-slate-400 mt-4 font-medium max-w-lg">
						{$t('theater.live.subtitle')}
					</p>
				</div>

				{#if $liveList.length > 0}
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
									>{$t('theater.live.multiview.title')}</span
								>
								<span class="text-sm font-black tracking-tight text-slate-900 dark:text-white"
									>{$t('theater.live.switchMultiview')}</span
								>
							</div>

							<div
								class="ml-2 w-5 h-5 rounded-lg bg-slate-100 dark:bg-zinc-800 flex items-center justify-center text-[10px] font-black text-slate-500"
							>
								{$liveList.length}
							</div>
						</a>
					</div>
				{/if}
			</div>
		</div>
	</header>

	<div class="max-w-7xl mx-auto px-0 md:px-0">
		<LiveGrid liveList={$liveList} loading={$liveLoading} {initialLoading} />
	</div>
</div>

<style>
</style>
