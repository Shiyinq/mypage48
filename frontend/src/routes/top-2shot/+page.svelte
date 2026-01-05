<script lang="ts">
	import { isAuthenticated, showToast } from '$lib/stores';
	import { Heart, Camera } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';
	import { PageHeader, EmptyState, ErrorState } from '$lib/components';
	import { KamiOshiCard, Leaderboard } from '$lib/components/top2shot';
	import { Top2ShotSkeleton } from '$lib/components/skeletons';
	import type { TopTwoShotResponse } from '$lib/types';
	import { topTwoShotStore } from '$lib/stores/memories';

	const { t } = useTranslation();

	/* Loading State */
	let mounted = false;
	let error = false;
	let loadingData = false;

	// Default stats if store is null
	let defaultStats: TopTwoShotResponse = {
		ranking: [],
		totalTwoShotSpend: 0,
		totalTwoShotCount: 0
	};

	$: stats = $topTwoShotStore || defaultStats;

	onMount(async () => {
		mounted = true;
		if ($isAuthenticated) {
			await fetchTopTwoShot();
		}
	});

	async function fetchTopTwoShot() {
		// If data exists, no need to show loading
		if ($topTwoShotStore) return;

		try {
			loadingData = true;
			error = false;
			// Use store load
			await topTwoShotStore.load();
		} catch (e) {
			console.error('Failed to load top 2shot:', e);
			error = true;
			showToast($t('top2shot.errorTitle') || 'Failed to load data', 'error');
		} finally {
			loadingData = false;
		}
	}

	$: isLoading = !mounted || loadingData;
	$: mostCollected = stats.ranking.length > 0 ? stats.ranking[0] : undefined;
</script>

<SEO title={$t('top2shot.title')} path="/top-2shot" description={$t('seo.top2shot')} />

<div class="max-w-6xl mx-auto p-4 pb-24 animate-fade-in">
	<!-- Header -->
	<div class="mb-8">
		<PageHeader
			icon={Heart}
			title={$t('top2shot.title')}
			subtitle={$t('top2shot.subtitle')}
			theme="pink"
		/>
	</div>

	{#if isLoading}
		<Top2ShotSkeleton />
	{:else if error && stats.ranking.length === 0}
		<ErrorState
			title={$t('top2shot.errorTitle') || 'Failed to load data'}
			description={$t('top2shot.errorDesc') ||
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
