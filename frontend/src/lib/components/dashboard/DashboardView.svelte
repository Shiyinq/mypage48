<script lang="ts">
	import { isAuthenticated } from '$lib/stores';
	import StatCard from '$lib/components/StatCard.svelte';
	import TheaterSeatMap from '$lib/components/TheaterSeatMap.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { Ticket as TicketIcon, DollarSign, Armchair, Camera, Users } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { slide } from 'svelte/transition';

	// Import dashboard components
	import {
		DashboardFilters,
		DashboardHeader,
		TopShowCard,
		Top2ShotCard,
		FirstLastCard,
		MonthlyAttendance,
		DayPreference,
		FirstLastPopup
	} from '$lib/components/dashboard';

	// Import dashboard store
	import { dashboardFilter, dashboardStatsData, isDashboardLoading } from '$lib/stores/dashboard';

	const { t } = useTranslation();

	function clickOutside(node: HTMLElement) {
		const handleClick = (event: MouseEvent) => {
			const target = event.target as Element;
			if (node && !node.contains(target) && !target.closest('[data-filter-toggle="true"]')) {
				isFilterOpen = false;
			}
		};

		document.addEventListener('click', handleClick, true);

		return {
			destroy() {
				document.removeEventListener('click', handleClick, true);
			}
		};
	}

	// Dashboard data sourced from store
	let dashboardDataState = $derived($dashboardStatsData);
	let dashboardStats = $derived(dashboardDataState.data);
	let error = $derived(dashboardDataState.error);

	const currentYear: number = new Date().getFullYear();
	let isFilterOpen = $state(false);

	let showTheaterPopup = $state(false);
	let showTwoShotPopup = $state(false);

	// Fetch dashboard data from API
	async function fetchDashboardStats() {
		if (!$isAuthenticated) {
			return;
		}

		await dashboardStatsData.load($dashboardFilter);
	}

	// Refetch when filter params change
	$effect(() => {
		if ($isAuthenticated && $dashboardFilter) {
			fetchDashboardStats();
		}
	});

	// Available years from API
	let availableYears = $derived(dashboardStats?.available_years ?? [currentYear]);

	// Derived stats from API response
	let totalSpent = $derived(dashboardStats?.theater.total_spent ?? 0);
	let totalVisits = $derived(dashboardStats?.theater.total_visits ?? 0);

	// Day Stats
	let dayStats = $derived({
		stats: dashboardStats?.period.day_stats.stats ?? [],
		maxCount: dashboardStats?.period.day_stats.max_count ?? 1
	});

	// Row Stats
	let rowStats = $derived({
		counts: dashboardStats?.seat_map.row_stats.counts ?? {},
		maxCount: dashboardStats?.seat_map.row_stats.max_count ?? 1,
		uniqueVisited: dashboardStats?.seat_map.row_stats.unique_visited ?? 0
	});

	// Seat Stats
	let seatStats = $derived(dashboardStats?.seat_map.seat_stats ?? {});

	// Monthly Stats - convert to frontend format
	let monthlyStats = $derived({
		stats:
			dashboardStats?.period.monthly_stats.stats.map((s) => ({
				name: s.name,
				count: s.count,
				spent: s.spent,
				isActive: s.is_active
			})) ?? [],
		maxCount: dashboardStats?.period.monthly_stats.max_count ?? 1
	});

	// Top Show
	let topShowStats = $derived({
		title: dashboardStats?.theater.top_show.title ?? '-',
		count: dashboardStats?.theater.top_show.count ?? 0,
		image: dashboardStats?.theater.top_show.image ?? null
	});

	// Two Shot Stats
	let twoShotStats = $derived({
		totalSpend: dashboardStats?.two_shot.total_spend ?? 0,
		totalCount: dashboardStats?.two_shot.total_count ?? 0,
		uniqueCount: dashboardStats?.two_shot.unique_count ?? 0,
		mostCollected: dashboardStats?.two_shot.top_2_shot
			? {
					name: dashboardStats.two_shot.top_2_shot.name,
					count: dashboardStats.two_shot.top_2_shot.count,
					image: dashboardStats.two_shot.top_2_shot.image ?? undefined
				}
			: null
	});

	// Most frequent row
	let mostFrequentRow = $derived(dashboardStats?.theater.most_frequent_row ?? '-');
	let mostFrequentRowCount = $derived(dashboardStats?.theater.most_frequent_row_count ?? 0);

	// Show Extremes
	let showExtremes = $derived({
		first: dashboardStats?.theater.extremes.first
			? {
					image: dashboardStats.theater.extremes.first.image,
					title: dashboardStats.theater.extremes.first.title,
					date: dashboardStats.theater.extremes.first.date,
					detail: dashboardStats.theater.extremes.first.detail ?? undefined
				}
			: null,
		last: dashboardStats?.theater.extremes.last
			? {
					image: dashboardStats.theater.extremes.last.image,
					title: dashboardStats.theater.extremes.last.title,
					date: dashboardStats.theater.extremes.last.date,
					detail: dashboardStats.theater.extremes.last.detail ?? undefined
				}
			: null
	});

	// Two Shot Extremes
	let twoShotExtremes = $derived({
		first: dashboardStats?.two_shot.extremes.first
			? {
					image: dashboardStats.two_shot.extremes.first.image,
					title: dashboardStats.two_shot.extremes.first.title,
					date: dashboardStats.two_shot.extremes.first.date
				}
			: null,
		last: dashboardStats?.two_shot.extremes.last
			? {
					image: dashboardStats.two_shot.extremes.last.image,
					title: dashboardStats.two_shot.extremes.last.title,
					date: dashboardStats.two_shot.extremes.last.date
				}
			: null
	});
</script>

<SEO title={$t('dashboard.title')} path="/" description={$t('seo.dashboard')} />

<div class="space-y-6 pt-4 sm:pt-6 px-4 pb-32 max-w-7xl mx-auto">
	<!-- Header / Filter Toggle -->
	<div class="mb-6 relative z-30">
		<DashboardHeader
			filter={$dashboardFilter}
			onOpenFilter={() => (isFilterOpen = !isFilterOpen)}
			isOpen={isFilterOpen}
		/>
		{#if isFilterOpen}
			<div
				use:clickOutside
				transition:slide={{ duration: 200 }}
				class="fixed md:absolute top-[72px] md:top-full left-0 right-0 md:left-auto md:right-0 mt-0 md:mt-2 px-4 md:px-0 z-[7000]"
			>
				<DashboardFilters
					bind:isAllData={$dashboardFilter.isAllData}
					bind:selectedYear={$dashboardFilter.selectedYear}
					bind:startMonth={$dashboardFilter.startMonth}
					bind:endMonth={$dashboardFilter.endMonth}
					{availableYears}
				/>
			</div>
		{/if}
	</div>

	<!-- Error Display -->
	{#if error}
		<div class="glass-panel p-4 rounded-xl text-center text-red-400">
			{error}
			<button
				class="ml-2 text-sm underline hover:text-red-300 cursor-pointer"
				onclick={() => fetchDashboardStats()}
			>
				{$t('errors.tryAgain')}
			</button>
		</div>
	{/if}

	<!-- THEATER & 2-SHOT STATS (2 COLUMNS) -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<!-- THEATER STATS -->
		<div class="glass-panel p-6 rounded-3xl">
			<div class="mb-6">
				<h3 class="text-xl font-bold text-themed">
					{$t('dashboard.theater.title')}
				</h3>
				<p class="text-xs text-gray-400">{$t('dashboard.theater.subtitle')}</p>
			</div>

			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
				<StatCard
					title={$t('dashboard.theater.shows')}
					value={totalVisits}
					sub={$t('dashboard.theater.timesWatched')}
					icon={TicketIcon}
					theme="red"
					loading={$isDashboardLoading}
				/>
				<StatCard
					title={$t('dashboard.theater.spending')}
					value={new Intl.NumberFormat('id-ID', {
						style: 'currency',
						currency: 'IDR',
						maximumFractionDigits: 0
					}).format(totalSpent)}
					icon={DollarSign}
					theme="emerald"
					loading={$isDashboardLoading}
					hideable={true}
				/>
				<StatCard
					title={$t('dashboard.theater.topRow')}
					value={mostFrequentRow}
					sub={$t('dashboard.theater.mostFrequentSeat')}
					detail={`${mostFrequentRowCount} ${$t('dashboard.theater.times')}`}
					icon={Armchair}
					theme="amber"
					showCrown={true}
					loading={$isDashboardLoading}
				/>

				<TopShowCard
					title={topShowStats.title}
					count={topShowStats.count}
					image={topShowStats.image}
					loading={$isDashboardLoading}
				/>

				<!-- First & Last Show Card -->
				<FirstLastCard
					title={`${$t('dashboard.theater.firstLast')} ${!$dashboardFilter.isAllData ? $dashboardFilter.selectedYear : ''}`}
					type="theater"
					loading={$isDashboardLoading}
					onExpand={() => (showTheaterPopup = true)}
					first={showExtremes.first}
					last={showExtremes.last}
				/>
			</div>
		</div>

		<!-- 2-SHOT STATS SECTION -->
		<div class="glass-panel p-6 rounded-3xl">
			<div class="mb-6">
				<h3 class="text-xl font-bold text-themed">
					{$t('dashboard.twoShot.title')}
				</h3>
				<p class="text-xs text-gray-400">{$t('dashboard.twoShot.subtitle')}</p>
			</div>

			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
				<StatCard
					title={$t('dashboard.twoShot.twoShotTitle')}
					value={twoShotStats.totalCount}
					sub={$t('dashboard.twoShot.collected')}
					icon={Camera}
					theme="pink"
					loading={$isDashboardLoading}
				/>
				<StatCard
					title={$t('dashboard.twoShot.spending')}
					value={new Intl.NumberFormat('id-ID', {
						style: 'currency',
						currency: 'IDR',
						maximumFractionDigits: 0
					}).format(twoShotStats.totalSpend)}
					icon={DollarSign}
					theme="emerald"
					loading={$isDashboardLoading}
					hideable={true}
				/>
				<StatCard
					title={$t('dashboard.twoShot.members')}
					value={twoShotStats.uniqueCount}
					sub={$t('dashboard.twoShot.uniqueIdols')}
					icon={Users}
					theme="blue"
					loading={$isDashboardLoading}
				/>

				<!-- Top 2-Shot Card -->
				<Top2ShotCard
					name={twoShotStats.mostCollected?.name || null}
					count={twoShotStats.mostCollected?.count || 0}
					image={twoShotStats.mostCollected?.image || undefined}
					loading={$isDashboardLoading}
				/>

				<!-- First & Last 2-Shot Card -->
				<FirstLastCard
					title={`${$t('dashboard.twoShot.firstLast')} ${!$dashboardFilter.isAllData ? $dashboardFilter.selectedYear : ''}`}
					type="twoShot"
					loading={$isDashboardLoading}
					onExpand={() => (showTwoShotPopup = true)}
					first={twoShotExtremes.first}
					last={twoShotExtremes.last}
				/>
			</div>
		</div>
	</div>

	<!-- THEATER MAP -->
	<TheaterSeatMap {rowStats} {seatStats} isLoading={$isDashboardLoading} />

	<div class="grid lg:grid-cols-3 gap-6">
		<MonthlyAttendance
			stats={monthlyStats.stats}
			maxCount={monthlyStats.maxCount}
			loading={$isDashboardLoading}
			subtitle={$dashboardFilter.isAllData
				? availableYears.length > 1
					? `${Math.min(...availableYears)} - ${Math.max(...availableYears)}`
					: `${availableYears[0]}`
				: `${$dashboardFilter.selectedYear}`}
		/>

		<DayPreference
			stats={dayStats.stats}
			maxCount={dayStats.maxCount}
			loading={$isDashboardLoading}
		/>
	</div>
</div>

<!-- THEATER POPUP -->
<FirstLastPopup
	show={showTheaterPopup}
	onClose={() => (showTheaterPopup = false)}
	title={`${$t('dashboard.theater.firstLast')} ${!$dashboardFilter.isAllData ? $dashboardFilter.selectedYear : ''}`}
	type="theater"
	first={showExtremes.first
		? {
				...showExtremes.first,
				detail: showExtremes.first.detail
					? `${$t('dashboard.seatMap.row')} ${showExtremes.first.detail.replace('Row ', '')}`
					: undefined
			}
		: null}
	last={showExtremes.last
		? {
				...showExtremes.last,
				detail: showExtremes.last.detail
					? `${$t('dashboard.seatMap.row')} ${showExtremes.last.detail.replace('Row ', '')}`
					: undefined
			}
		: null}
/>

<!-- 2-SHOT POPUP -->
<FirstLastPopup
	show={showTwoShotPopup}
	onClose={() => (showTwoShotPopup = false)}
	title={`${$t('dashboard.twoShot.firstLast')} ${!$dashboardFilter.isAllData ? $dashboardFilter.selectedYear : ''}`}
	type="twoShot"
	first={twoShotExtremes.first}
	last={twoShotExtremes.last}
/>
