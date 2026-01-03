<script lang="ts">
	import { tickets, isAuthenticated, isInitialDataLoaded, showToast } from '$lib/stores';
	import { Heart, Camera } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';
	import { PageHeader, EmptyState, ErrorState } from '$lib/components';
	import { ticketsApi } from '$lib/apis/tickets';
	import { KamiOshiCard, Leaderboard } from '$lib/components/top2shot';
	import { Top2ShotSkeleton } from '$lib/components/skeletons';

	const { t } = useTranslation();

	/* Loading State */
	let mounted = false;
	let error = false;
	let loadingData = false;

	onMount(async () => {
		mounted = true;
		if ($tickets.length === 0 && !$isInitialDataLoaded) {
			await fetchTickets();
		}
	});

	async function fetchTickets() {
		try {
			loadingData = true;
			error = false;
			const res = await ticketsApi.getMyTickets(1, 100); // Fetch standard amount to populate stats
			tickets.set(res.data);
			isInitialDataLoaded.set(true);
		} catch (e) {
			console.error('Failed to load tickets for top 2shot:', e);
			error = true;
			showToast($t('top2shot.errorTitle') || 'Failed to load data', 'error');
		} finally {
			loadingData = false;
		}
	}

	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded) || loadingData;

	// --- DATA PROCESSING ---
	$: stats = (() => {
		const memberStats: Record<
			string,
			{ count: number; spend: number; lastDate: string; image?: string }
		> = {};
		let totalTwoShotSpend = 0;
		let totalTwoShotCount = 0;

		$tickets.forEach((t) => {
			// 2-Shot Stats
			if (t.two_shot?.member_name) {
				const name = t.two_shot.member_name.trim();
				const price = t.two_shot.price || 0;

				totalTwoShotSpend += price;
				totalTwoShotCount++;

				if (!memberStats[name]) {
					memberStats[name] = {
						count: 0,
						spend: 0,
						lastDate: t.event.date,
						image: t.two_shot.imageUrl
					};
				}

				memberStats[name].count += 1;
				memberStats[name].spend += price;

				// Update image to latest if available
				if (t.two_shot.imageUrl) {
					// Prefer latest image, or if current doesn't have one
					if (
						new Date(t.event.date) > new Date(memberStats[name].lastDate) ||
						!memberStats[name].image
					) {
						memberStats[name].image = t.two_shot.imageUrl;
						memberStats[name].lastDate = t.event.date;
					}
				}
			}
		});

		// Convert to array and sort
		const ranking = Object.entries(memberStats)
			.map(([name, data]) => ({ name, ...data }))
			.sort((a, b) => {
				if (b.count !== a.count) return b.count - a.count; // Sort by count
				return b.spend - a.spend; // Then by spend
			});

		return {
			ranking,
			totalTwoShotSpend,
			totalTwoShotCount
		};
	})();

	$: mostCollected = stats.ranking[0];
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
			onRetry={fetchTickets}
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
				<KamiOshiCard member={mostCollected} />
			</div>

			<!-- RIGHT COL: Leaderboard -->
			<div class="lg:col-span-2">
				<Leaderboard
					ranking={stats.ranking}
					totalCount={stats.totalTwoShotCount}
					topMemberCount={mostCollected.count}
				/>
			</div>
		</div>
	{/if}
</div>
