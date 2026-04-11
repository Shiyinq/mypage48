<script lang="ts">
	export let params: Record<string, string> | undefined = undefined;
	import { isAuthenticated, showToast } from '$lib/stores';
	import { isCacheExpired } from '$lib/utils/cache';
	import { logger } from '$lib/utils/logger';
	import { Heart, Camera } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';
	import { PageHeader, EmptyState, ErrorState } from '$lib/components';
	import { KamiOshiCard, Leaderboard } from '$lib/components/top2shot';
	import { Top2ShotSkeleton } from '$lib/components/skeletons';
	import type { TopTwoShotResponse } from '$lib/types';
	import { topTwoShotStore, isTopTwoShotLoading } from '$lib/stores/memories';

	const { t } = useTranslation();

	/* Loading State */
	let mounted = false;

	// Default stats if store is null
	let defaultStats: TopTwoShotResponse = {
		ranking: [],
		totalTwoShotSpend: 0,
		totalTwoShotCount: 0
	};

	$: stats = $topTwoShotStore.data || defaultStats;
	$: error = $topTwoShotStore.error;

	onMount(async () => {
		mounted = true;
		if ($isAuthenticated) {
			await fetchTopTwoShot();
		}
	});

	async function fetchTopTwoShot() {
		// If data exists and is not expired, no need to show loading
		// Store load check handles cache expiration check too, but we can double check here or just call load()
		if ($topTwoShotStore.data && !isCacheExpired($topTwoShotStore.lastUpdated)) return;

		try {
			await topTwoShotStore.load();
		} catch (e) {
			// Error state is handled by store, we just show toast
			showToast($t('top2shot.errorTitle') || 'Failed to load data', 'error');
		}
	}

	$: mostCollected = stats.ranking.length > 0 ? stats.ranking[0] : undefined;
</script>

<SEO title={$t('top2shot.title')} path="/top-2shot" description={$t('seo.top2shot')} />

<div class="max-w-6xl mx-auto pt-4 sm:pt-6 px-4 pb-24 animate-fade-in">
	<!-- Header -->
	<div class="mb-8">
		<PageHeader
			icon={Heart}
			title={$t('top2shot.title')}
			subtitle={$t('top2shot.subtitle')}
			theme="pink"
		/>
	</div>

	{#if $isTopTwoShotLoading || !mounted}
		<Top2ShotSkeleton />
	{:else if error && stats.ranking.length === 0}
		<ErrorState
			title={$t('top2shot.errorTitle') || 'Failed to load data'}
			description={$t('top2shot.errorDesc') ||
				error ||
				'Something went wrong while fetching the leaderboard.'}
			onRetry={fetchTopTwoShot}
		/>
	{:else if stats.ranking.length === 0}
		<EmptyState
			icon={Camera}
			title={$t('top2shot.noData')}
			description={$t('top2shot.noDataDesc')}
		/>
	{:else}
		<div class="grid lg:grid-cols-3 gap-6">
			<!-- LEFT COL: Kami Oshi Card -->
			<div class="space-y-6 lg:col-span-1">
				{#if mostCollected}
					<KamiOshiCard member={mostCollected} />
				{/if}
			</div>

			<!-- RIGHT COL: Leaderboard -->
			<div class="lg:col-span-2">
				<Leaderboard
					ranking={stats.ranking}
					totalCount={stats.totalTwoShotCount}
					topMemberCount={mostCollected ? mostCollected.count : 0}
				/>
			</div>
		</div>
	{/if}
</div>
