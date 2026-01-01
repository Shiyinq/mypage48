<script lang="ts">
	import { tickets, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { goto } from '$app/navigation';
	import StatCard from '$lib/components/StatCard.svelte';
	import TheaterSeatMap from '$lib/components/TheaterSeatMap.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import {
		Ticket as TicketIcon,
		Calendar,
		DollarSign,
		Armchair,
		Filter,
		ChevronDown,
		LayoutDashboard,
		X,
		Star,
		Heart,
		Camera,
		ChevronRight,
		Crown,
		User,
		Users,
		Maximize2
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';

	// Import shared constants
	import { SHOW_IMAGES, getShowImage, MONTHS, DAYS, THEATER_ROWS } from '$lib/constants';

	// Import dashboard components
	import {
		DashboardFilters,
		DashboardHeader,
		TopShowCard,
		Top2ShotCard
	} from '$lib/components/dashboard';

	const { t } = useTranslation();

	let mounted = false;

	onMount(() => {
		mounted = true;
	});

	// Loading state - show skeleton when:
	// 1. Not mounted yet (SSR or initial client render)
	// 2. Authenticated but data is not loaded yet
	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded);

	// State
	const currentYear: number = new Date().getFullYear();
	let selectedYear: number = currentYear;
	let startMonth: number = 0;
	let endMonth: number = 11;
	let isFilterOpen: boolean = false;

	let isAllData: boolean = false;
	let showTheaterPopup: boolean = false;
	let showTwoShotPopup: boolean = false;

	// Helper function for filter label
	$: filterLabel = (() => {
		if (isAllData) return 'All Data';
		const startMonthShort = MONTHS[startMonth].substring(0, 3);
		const endMonthShort = MONTHS[endMonth].substring(0, 3);
		if (startMonth === 0 && endMonth === 11) {
			return `${selectedYear} Jan-Dec`;
		}
		return `${selectedYear} ${startMonthShort}-${endMonthShort}`;
	})();

	// Derived State
	$: availableYears = Array.from(
		new Set([
			currentYear,
			...$tickets.map((t) => new Date(t.event.date).getFullYear()).filter((y) => !isNaN(y))
		])
	).sort((a, b) => b - a) as number[];

	$: filteredTickets = $tickets.filter((t) => {
		if (isAllData) return true;
		const d = new Date(t.event.date);
		const y = d.getFullYear();
		const m = d.getMonth();
		return y === selectedYear && m >= startMonth && m <= endMonth;
	});

	$: totalSpent = filteredTickets.reduce((acc, t) => acc + t.price, 0) as number;
	$: totalVisits = filteredTickets.length as number;

	// Day Stats (Sync with Monthly Style)
	$: dayStats = (() => {
		const stats = DAYS.map((name) => ({ name, count: 0 }));
		filteredTickets.forEach((t) => {
			let day = t.event.day || new Date(t.event.date).toLocaleString('en-US', { weekday: 'long' });
			if (day) {
				const d = stats.find((s) => s.name.toLowerCase() === day.trim().toLowerCase());
				if (d) d.count++;
			}
		});
		const maxCount = Math.max(...stats.map((s) => s.count), 1);
		return { stats, maxCount };
	})() as { stats: { name: string; count: number }[]; maxCount: number };

	// Row Stats
	$: rowStats = (() => {
		const counts: Record<string, number> = {};
		filteredTickets.forEach((t) => {
			const r = t.seat.section.trim().toUpperCase().charAt(0);
			if ((THEATER_ROWS as readonly string[]).includes(r)) counts[r] = (counts[r] || 0) + 1;
		});
		const maxCount = Math.max(...Object.values(counts), 1);
		return { counts, maxCount, uniqueVisited: Object.keys(counts).length };
	})() as { counts: Record<string, number>; maxCount: number; uniqueVisited: number };

	// Seat Stats
	$: seatStats = (() => {
		const stats: Record<string, number> = {};
		filteredTickets.forEach((t) => {
			const k = `${t.seat.section.trim().toUpperCase().charAt(0)}-${t.seat.number}`;
			stats[k] = (stats[k] || 0) + 1;
		});
		return stats;
	})() as Record<string, number>;

	// Monthly Stats
	$: monthlyStats = (() => {
		const stats = Array(12)
			.fill(null)
			.map((_, i) => ({
				name: new Date(2000, i, 1).toLocaleString('default', { month: 'short' }),
				count: 0,
				spent: 0,
				isActive: isAllData ? true : i >= startMonth && i <= endMonth
			}));
		filteredTickets.forEach((t) => {
			const d = new Date(t.event.date);
			const m = d.getMonth();
			stats[m].count++;
			stats[m].spent += t.price;
		});
		const maxCount = Math.max(...stats.map((s) => s.count), 1);
		return { stats, maxCount };
	})() as {
		stats: { name: string; count: number; spent: number; isActive: boolean }[];
		maxCount: number;
	};

	// Top Show
	$: topShowStats = (() => {
		if (filteredTickets.length === 0) return { title: '-', count: 0, image: null as string | null };
		const counts: Record<string, number> = {};
		filteredTickets.forEach((t) => {
			const title = t.event.title.trim();
			counts[title] = (counts[title] || 0) + 1;
		});

		let title = '-';
		if (Object.keys(counts).length > 0) {
			title = Object.keys(counts).reduce((a, b) => (counts[a] > counts[b] ? a : b));
		}

		const matchedShow = SHOW_IMAGES.find((s) =>
			title.toLowerCase().includes(s.title.toLowerCase())
		);
		return { title, count: counts[title] || 0, image: matchedShow?.image || null };
	})() as { title: string; count: number; image: string | null };

	// Two Shot
	$: twoShotStats = (() => {
		const memberStats: Record<string, { count: number; image?: string }> = {};
		let totalSpend = 0;
		let totalCount = 0;
		const uniqueMembers = new Set<string>();
		filteredTickets.forEach((t) => {
			if (t.two_shot?.member_name) {
				const name = t.two_shot.member_name.trim();
				const price = t.two_shot.price || 0;
				totalSpend += price;
				totalCount++;
				uniqueMembers.add(name);
				if (!memberStats[name]) memberStats[name] = { count: 0, image: t.two_shot.imageUrl };
				memberStats[name].count++;
				if (t.two_shot.imageUrl) memberStats[name].image = t.two_shot.imageUrl;
			}
		});
		const ranking = Object.entries(memberStats)
			.map(([name, d]) => ({ name, ...d }))
			.sort((a, b) => b.count - a.count);
		return {
			ranking,
			totalSpend,
			totalCount,
			uniqueCount: uniqueMembers.size,
			mostCollected: ranking[0] || null
		};
	})() as {
		ranking: { name: string; count: number; image?: string }[];
		totalSpend: number;
		totalCount: number;
		uniqueCount: number;
		mostCollected: { name: string; count: number; image?: string } | null;
	};

	// Most frequent row for card
	$: mostFrequentRow = (Object.entries(rowStats.counts).sort((a, b) => b[1] - a[1])[0]?.[0] ||
		'-') as string;

	// First & Last Show
	$: showExtremes = (() => {
		if (filteredTickets.length === 0) return { first: null, last: null };
		const sorted = [...filteredTickets].sort((a, b) => {
			const dateA = new Date(a.event.date).getTime();
			const dateB = new Date(b.event.date).getTime();
			if (dateA !== dateB) return dateA - dateB;
			return a.event.time.localeCompare(b.event.time);
		});
		return { first: sorted[0], last: sorted[sorted.length - 1] };
	})() as { first: (typeof $tickets)[0] | null; last: (typeof $tickets)[0] | null };

	// First & Last 2-Shot
	$: twoShotExtremes = (() => {
		const with2Shot = filteredTickets.filter((t) => t.two_shot?.member_name);
		if (with2Shot.length === 0) return { first: null, last: null };
		const sorted = [...with2Shot].sort((a, b) => {
			const dateA = new Date(a.event.date).getTime();
			const dateB = new Date(b.event.date).getTime();
			if (dateA !== dateB) return dateA - dateB;
			return a.event.time.localeCompare(b.event.time);
		});
		return { first: sorted[0], last: sorted[sorted.length - 1] };
	})() as { first: (typeof $tickets)[0] | null; last: (typeof $tickets)[0] | null };

	const formatDate = (dateStr: string) => {
		const d = new Date(dateStr);
		const options: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' };
		if (isAllData) options.year = 'numeric';
		return d.toLocaleDateString('id-ID', options);
	};
</script>

<SEO title={$t('dashboard.title')} path="/" description={$t('seo.dashboard')} />

<div class="space-y-6 p-4 pb-32 max-w-7xl mx-auto">
	<!-- Header / Filter Toggle -->
	<div class="mb-6">
		{#if isFilterOpen}
			<DashboardFilters
				bind:isOpen={isFilterOpen}
				bind:isAllData
				bind:selectedYear
				bind:startMonth
				bind:endMonth
				{availableYears}
			/>
		{:else}
			<DashboardHeader {filterLabel} onOpenFilter={() => (isFilterOpen = true)} />
		{/if}
	</div>

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
					loading={isLoading}
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
					loading={isLoading}
					hideable={true}
				/>
				<StatCard
					title={$t('dashboard.theater.topRow')}
					value={mostFrequentRow}
					sub={$t('dashboard.theater.mostFrequentSeat')}
					detail={`${rowStats.counts[mostFrequentRow] || 0} ${$t('dashboard.theater.times')}`}
					icon={Armchair}
					theme="amber"
					showCrown={true}
					loading={isLoading}
				/>

				<TopShowCard
					title={topShowStats.title}
					count={topShowStats.count}
					image={topShowStats.image}
					loading={isLoading}
				/>

				<!-- First & Last Show Card -->
				<div
					class="glass-card rounded-3xl p-5 relative overflow-hidden group hover:shadow-lg transition-all duration-300 bg-purple-50/20 dark:bg-transparent border-purple-100 dark:border-purple-500/20 sm:col-span-2"
				>
					<div class="flex justify-between items-start mb-4">
						<div class="flex items-center gap-2 text-purple-500">
							<div class="p-1.5 bg-purple-100 dark:bg-purple-800/40 rounded-lg">
								<Calendar class="w-4 h-4" />
							</div>
							<span class="font-bold text-xs tracking-wider text-gray-800 dark:text-gray-100">
								{$t('dashboard.theater.firstLast')}
								{!isAllData ? selectedYear : ''}
							</span>
						</div>
						<button
							on:click={() => (showTheaterPopup = true)}
							class="p-2 -mr-2 -mt-2 text-purple-400 hover:text-purple-600 dark:hover:text-purple-300 hover:bg-purple-100 dark:hover:bg-purple-800/30 rounded-full transition-colors cursor-pointer"
							title="View Fullscreen"
						>
							<Maximize2 class="w-4 h-4" />
						</button>
					</div>

					{#if isLoading}
						<div class="grid grid-cols-2 gap-4">
							<div class="space-y-2">
								<div class="h-3 w-12 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
								<div class="h-5 w-24 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
								<div class="h-3 w-20 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
							</div>
							<div class="space-y-2">
								<div class="h-3 w-12 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
								<div class="h-5 w-24 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
								<div class="h-3 w-20 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
							</div>
						</div>
					{:else}
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">
							<!-- Divider -->
							<div
								class="hidden sm:block absolute left-1/2 top-0 bottom-0 w-px bg-purple-200 dark:bg-purple-800/30"
							></div>

							<!-- First Show -->
							<div class="flex items-start gap-3">
								{#if showExtremes.first}
									{@const showImg = getShowImage(showExtremes.first.event.title)}
									<div
										class="w-12 h-16 rounded-lg bg-gray-200 dark:bg-gray-800 overflow-hidden flex-shrink-0 shadow-sm border border-purple-100 dark:border-purple-500/20"
									>
										{#if showImg}
											<img
												src={showImg}
												alt={showExtremes.first.event.title}
												class="w-full h-full object-cover"
											/>
										{:else}
											<div class="w-full h-full flex items-center justify-center text-purple-300">
												<Star class="w-4 h-4" />
											</div>
										{/if}
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
											{$t('dashboard.theater.first')}
										</p>
										<p class="font-bold text-themed text-sm leading-tight truncate">
											{showExtremes.first.event.title}
										</p>
										<p class="text-xs font-bold text-purple-600 dark:text-purple-400">
											{formatDate(showExtremes.first.event.date)}
										</p>
										<p class="text-[10px] text-gray-500 mt-0.5">
											{$t('dashboard.seatMap.row')}
											{showExtremes.first.seat.section.trim().charAt(0)} - {showExtremes.first.seat
												.number}
										</p>
									</div>
								{:else}
									<div
										class="w-12 h-16 rounded-lg bg-gray-50 dark:bg-gray-800/50 overflow-hidden flex-shrink-0 shadow-sm border border-purple-100 dark:border-purple-500/20"
									>
										<div
											class="w-full h-full flex items-center justify-center text-purple-200 dark:text-purple-800/30"
										>
											<Star class="w-4 h-4" />
										</div>
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
											{$t('dashboard.theater.first')}
										</p>
										<p class="font-bold text-themed text-sm leading-tight truncate">-</p>
										<p class="text-xs font-bold text-purple-600 dark:text-purple-400">-</p>
										<p class="text-[10px] text-gray-500 mt-0.5">-</p>
									</div>
								{/if}
							</div>

							<!-- Last Show -->
							<div class="flex items-start gap-3 relative sm:pl-2">
								{#if showExtremes.last}
									{@const showImg = getShowImage(showExtremes.last.event.title)}
									<div
										class="w-12 h-16 rounded-lg bg-gray-200 dark:bg-gray-800 overflow-hidden flex-shrink-0 shadow-sm border border-purple-100 dark:border-purple-500/20"
									>
										{#if showImg}
											<img
												src={showImg}
												alt={showExtremes.last.event.title}
												class="w-full h-full object-cover"
											/>
										{:else}
											<div class="w-full h-full flex items-center justify-center text-purple-300">
												<Star class="w-4 h-4" />
											</div>
										{/if}
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
											{$t('dashboard.theater.last')}
										</p>
										<p class="font-bold text-themed text-sm leading-tight truncate">
											{showExtremes.last.event.title}
										</p>
										<p class="text-xs font-bold text-purple-600 dark:text-purple-400">
											{formatDate(showExtremes.last.event.date)}
										</p>
										<p class="text-[10px] text-gray-500 mt-0.5">
											{$t('dashboard.seatMap.row')}
											{showExtremes.last.seat.section.trim().charAt(0)} - {showExtremes.last.seat
												.number}
										</p>
									</div>
								{:else}
									<div
										class="w-12 h-16 rounded-lg bg-gray-50 dark:bg-gray-800/50 overflow-hidden flex-shrink-0 shadow-sm border border-purple-100 dark:border-purple-500/20"
									>
										<div
											class="w-full h-full flex items-center justify-center text-purple-200 dark:text-purple-800/30"
										>
											<Star class="w-4 h-4" />
										</div>
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
											{$t('dashboard.theater.last')}
										</p>
										<p class="font-bold text-themed text-sm leading-tight truncate">-</p>
										<p class="text-xs font-bold text-purple-600 dark:text-purple-400">-</p>
										<p class="text-[10px] text-gray-500 mt-0.5">-</p>
									</div>
								{/if}
							</div>
						</div>
					{/if}
				</div>
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
					loading={isLoading}
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
					loading={isLoading}
					hideable={true}
				/>
				<StatCard
					title={$t('dashboard.twoShot.members')}
					value={twoShotStats.uniqueCount}
					sub={$t('dashboard.twoShot.uniqueIdols')}
					icon={Users}
					theme="blue"
					loading={isLoading}
				/>

				<!-- Top 2-Shot Card -->
				<Top2ShotCard
					name={twoShotStats.mostCollected?.name || null}
					count={twoShotStats.mostCollected?.count || 0}
					image={twoShotStats.mostCollected?.image || undefined}
					loading={isLoading}
				/>

				<!-- First & Last 2-Shot Card -->
				<div
					class="glass-card rounded-3xl p-5 relative overflow-hidden group hover:shadow-lg transition-all duration-300 bg-pink-50/20 dark:bg-transparent border-pink-100 dark:border-pink-500/20 sm:col-span-2"
				>
					<div class="flex justify-between items-start mb-4">
						<div class="flex items-center gap-2 text-pink-400">
							<div class="p-1.5 bg-pink-50 dark:bg-pink-800/40 rounded-lg">
								<Calendar class="w-4 h-4" />
							</div>
							<span class="font-bold text-xs tracking-wider text-gray-800 dark:text-gray-100">
								{$t('dashboard.twoShot.firstLast')}
								{!isAllData ? selectedYear : ''}
							</span>
						</div>
						<button
							on:click={() => (showTwoShotPopup = true)}
							class="p-2 -mr-2 -mt-2 text-pink-300 hover:text-pink-500 dark:hover:text-pink-300 hover:bg-pink-50 dark:hover:bg-pink-800/30 rounded-full transition-colors cursor-pointer"
							title="View Fullscreen"
						>
							<Maximize2 class="w-4 h-4" />
						</button>
					</div>

					{#if isLoading}
						<div class="grid grid-cols-2 gap-4">
							<div class="space-y-2">
								<div class="h-3 w-12 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
								<div class="h-5 w-24 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
							</div>
							<div class="space-y-2">
								<div class="h-3 w-12 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
								<div class="h-5 w-24 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
							</div>
						</div>
					{:else}
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">
							<!-- Divider -->
							<div
								class="hidden sm:block absolute left-1/2 top-0 bottom-0 w-px bg-pink-200 dark:bg-pink-800/30"
							></div>

							<!-- First 2-Shot -->
							<div class="flex items-start gap-3">
								{#if twoShotExtremes.first}
									<div
										class="w-12 h-16 rounded-lg bg-gray-200 dark:bg-gray-800 overflow-hidden flex-shrink-0 shadow-sm border border-pink-100 dark:border-pink-500/20"
									>
										{#if twoShotExtremes.first.two_shot?.imageUrl}
											<img
												src={twoShotExtremes.first.two_shot.imageUrl}
												alt="2-Shot"
												class="w-full h-full object-cover"
											/>
										{:else}
											<div class="w-full h-full flex items-center justify-center text-pink-300">
												<Camera class="w-4 h-4" />
											</div>
										{/if}
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
											{$t('dashboard.twoShot.first')}
										</p>
										<p class="font-bold text-themed text-sm leading-tight truncate">
											{twoShotExtremes.first.two_shot?.member_name || '-'}
										</p>
										<p class="text-xs font-bold text-pink-400">
											{formatDate(twoShotExtremes.first.event.date)}
										</p>
									</div>
								{:else}
									<div
										class="w-12 h-16 rounded-lg bg-gray-50 dark:bg-gray-800/50 overflow-hidden flex-shrink-0 shadow-sm border border-pink-100 dark:border-pink-500/20"
									>
										<div
											class="w-full h-full flex items-center justify-center text-pink-200 dark:text-pink-800/30"
										>
											<Camera class="w-4 h-4" />
										</div>
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
											{$t('dashboard.twoShot.first')}
										</p>
										<p class="font-bold text-themed text-sm leading-tight truncate">-</p>
										<p class="text-xs font-bold text-pink-400">-</p>
									</div>
								{/if}
							</div>

							<!-- Last 2-Shot -->
							<div class="flex items-start gap-3 relative sm:pl-2">
								{#if twoShotExtremes.last}
									<div
										class="w-12 h-16 rounded-lg bg-gray-200 dark:bg-gray-800 overflow-hidden flex-shrink-0 shadow-sm border border-pink-100 dark:border-pink-500/20"
									>
										{#if twoShotExtremes.last.two_shot?.imageUrl}
											<img
												src={twoShotExtremes.last.two_shot.imageUrl}
												alt="2-Shot"
												class="w-full h-full object-cover"
											/>
										{:else}
											<div class="w-full h-full flex items-center justify-center text-pink-300">
												<Camera class="w-4 h-4" />
											</div>
										{/if}
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
											{$t('dashboard.twoShot.last')}
										</p>
										<p class="font-bold text-themed text-sm leading-tight truncate">
											{twoShotExtremes.last.two_shot?.member_name || '-'}
										</p>
										<p class="text-xs font-bold text-pink-400">
											{formatDate(twoShotExtremes.last.event.date)}
										</p>
									</div>
								{:else}
									<div
										class="w-12 h-16 rounded-lg bg-gray-50 dark:bg-gray-800/50 overflow-hidden flex-shrink-0 shadow-sm border border-pink-100 dark:border-pink-500/20"
									>
										<div
											class="w-full h-full flex items-center justify-center text-pink-200 dark:text-pink-800/30"
										>
											<Camera class="w-4 h-4" />
										</div>
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
											{$t('dashboard.twoShot.last')}
										</p>
										<p class="font-bold text-themed text-sm leading-tight truncate">-</p>
										<p class="text-xs font-bold text-pink-400">-</p>
									</div>
								{/if}
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>

	<!-- THEATER MAP -->
	<TheaterSeatMap {rowStats} {seatStats} {isLoading} />

	<div class="grid lg:grid-cols-3 gap-6">
		<!-- Monthly Heatmap -->
		<div class="glass-panel p-6 rounded-3xl lg:col-span-2 flex flex-col">
			<div class="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
				<div>
					<h3 class="text-xl font-bold text-themed">
						{$t('dashboard.monthlyAttendance.title')}
					</h3>
					<p class="text-xs text-gray-400">
						{$t('dashboard.monthlyAttendance.subtitle')}
						{isAllData
							? availableYears.length > 1
								? `${Math.min(...availableYears)} - ${Math.max(...availableYears)}`
								: availableYears[0]
							: selectedYear}
					</p>
				</div>
			</div>

			<div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3 flex-1">
				{#if isLoading}
					<!-- Skeleton Loading for Monthly -->
					<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
					{#each [1, 2, 3] as _unused, i}
						<div class="flex flex-col items-center">
							<div
								class="w-full aspect-square rounded-2xl mb-2 bg-gray-200 dark:bg-zinc-700 animate-pulse"
							></div>
							<div class="h-3 w-8 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
						</div>
					{/each}
				{:else}
					{#each monthlyStats.stats as month}
						{@const intensity =
							month.count > 0 ? 0.2 + (month.count / monthlyStats.maxCount) * 0.8 : 0.05}
						{@const hasData = month.count > 0}
						{@const isHighIntensity = intensity > 0.5}
						<div
							class={`flex flex-col items-center group relative ${!month.isActive ? 'opacity-30 grayscale pointer-events-none' : ''}`}
							title={hasData
								? `${new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(month.spent)}`
								: ''}
						>
							<div
								class="w-full aspect-square rounded-2xl mb-2 flex flex-col items-center justify-center relative overflow-hidden transition-all duration-300 group-hover:-translate-y-1 group-hover:shadow-lg group-hover:scale-105 border"
								style={`
									background: ${hasData ? `rgba(227, 0, 15, ${intensity})` : 'var(--color-surface)'}; 
									border-color: ${hasData ? 'transparent' : 'var(--color-border-light)'};
									box-shadow: ${hasData ? `0 4px 12px -2px rgba(220, 38, 38, ${intensity * 0.6})` : 'none'}
								`}
							>
								{#if hasData}
									<span
										class={`text-xl md:text-2xl font-black drop-shadow-sm transition-colors duration-300 ${isHighIntensity ? 'text-white' : 'text-red-600 dark:text-red-400'}`}
									>
										{month.count}
									</span>
									<span
										class={`text-[8px] font-bold uppercase tracking-wider transition-colors duration-300 ${isHighIntensity ? 'text-white/80' : 'text-red-600/70 dark:text-red-400/70'}`}
									>
										{$t('shows.unit')}
									</span>

									<!-- Spending Pill on Hover -->
									<div
										class="absolute inset-x-0 bottom-0 p-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-black/40 backdrop-blur-sm flex justify-center"
									>
										<p class="text-[9px] text-white font-bold truncate">
											{new Intl.NumberFormat('id-ID', {
												notation: 'compact',
												compactDisplay: 'short'
											}).format(month.spent)}
										</p>
									</div>
								{:else}
									<span class="text-gray-300 dark:text-gray-600 text-xl font-bold opacity-30"
										>-</span
									>
								{/if}
							</div>
							<div class="text-center w-full">
								<span
									class="text-[10px] font-bold text-gray-500 dark:text-gray-400 block uppercase tracking-wide group-hover:text-red-500 transition-colors"
									>{$t('time.monthsShort.' + month.name.substring(0, 3).toLowerCase())}</span
								>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</div>

		<!-- Day Preference List -->
		<div class="glass-panel p-6 rounded-3xl flex flex-col">
			<div class="mb-6">
				<h3 class="text-xl font-bold text-themed">
					{$t('dashboard.dayPreference.title')}
				</h3>
				<p class="text-xs text-gray-400">{$t('dashboard.dayPreference.subtitle')}</p>
			</div>

			<div class="flex flex-wrap justify-center gap-3 flex-1 content-start w-full">
				{#if isLoading}
					<!-- Skeleton Loading for Days -->
					<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
					{#each Array(7) as _unused, i}
						<div
							class="flex flex-col items-center w-[calc(33.33%-0.5rem)] sm:w-[calc(25%-0.56rem)] lg:w-[calc(33.33%-0.5rem)] xl:w-[calc(25%-0.56rem)]"
						>
							<div
								class="w-full aspect-square rounded-2xl mb-2 bg-gray-200 dark:bg-zinc-700 animate-pulse"
							></div>
							<div class="h-3 w-8 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
						</div>
					{/each}
				{:else}
					{#each dayStats.stats as day}
						{@const intensity = day.count > 0 ? 0.2 + (day.count / dayStats.maxCount) * 0.8 : 0.05}
						{@const hasData = day.count > 0}
						{@const isHighIntensity = intensity > 0.5}
						<div
							class="flex flex-col items-center group w-[calc(33.33%-0.5rem)] sm:w-[calc(25%-0.56rem)] lg:w-[calc(33.33%-0.5rem)] xl:w-[calc(25%-0.56rem)]"
						>
							<div
								class="w-full aspect-square rounded-2xl mb-2 flex flex-col items-center justify-center relative overflow-hidden transition-all duration-300 group-hover:-translate-y-1 group-hover:shadow-lg group-hover:scale-105 border"
								style={`
									background: ${hasData ? `rgba(227, 0, 15, ${intensity})` : 'var(--color-surface)'}; 
									border-color: ${hasData ? 'transparent' : 'var(--color-border-light)'};
									box-shadow: ${hasData ? `0 4px 12px -2px rgba(220, 38, 38, ${intensity * 0.6})` : 'none'}
								`}
							>
								{#if hasData}
									<span
										class={`text-xl md:text-2xl font-black drop-shadow-sm transition-colors duration-300 ${isHighIntensity ? 'text-white' : 'text-red-600 dark:text-red-400'}`}
									>
										{day.count}
									</span>
									<span
										class={`text-[8px] font-bold uppercase tracking-wider transition-colors duration-300 ${isHighIntensity ? 'text-white/80' : 'text-red-600/70 dark:text-red-400/70'}`}
									>
										{$t('shows.unit')}
									</span>
								{:else}
									<span class="text-gray-300 dark:text-gray-600 text-xl font-bold opacity-30"
										>-</span
									>
								{/if}
							</div>
							<div class="text-center w-full">
								<span
									class="text-[10px] font-bold text-gray-500 dark:text-gray-400 block uppercase tracking-wide group-hover:text-red-500 transition-colors"
									>{$t('time.daysShort.' + day.name.substring(0, 3).toLowerCase())}</span
								>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</div>
	</div>
</div>

<!-- THEATER POPUP -->
{#if showTheaterPopup}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
		on:click|self={() => (showTheaterPopup = false)}
		role="dialog"
		aria-modal="true"
	>
		<div
			class="bg-purple-50 dark:bg-zinc-900 w-full max-w-4xl rounded-3xl shadow-2xl overflow-hidden animate-scale-in border border-purple-100 dark:border-purple-500/20"
		>
			<!-- Header -->
			<div
				class="p-6 border-b border-purple-100 dark:border-purple-500/20 flex items-center justify-between bg-purple-50/30 dark:bg-transparent"
			>
				<div class="flex items-center gap-3 text-purple-500">
					<div class="p-2 bg-purple-100 dark:bg-purple-800/40 rounded-xl">
						<Calendar class="w-6 h-6" />
					</div>
					<h3 class="font-bold text-xl text-gray-800 dark:text-gray-100">
						{$t('dashboard.theater.firstLast')}
						{!isAllData ? selectedYear : ''}
					</h3>
				</div>
				<button
					on:click={() => (showTheaterPopup = false)}
					class="p-2 bg-purple-100 dark:bg-purple-800/40 hover:bg-purple-200 dark:hover:bg-purple-700/50 rounded-full transition-colors cursor-pointer"
				>
					<X class="w-6 h-6 text-purple-500 dark:text-purple-400" />
				</button>
			</div>

			<!-- Content -->
			<div class="p-6 md:p-10 grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 relative">
				<div
					class="hidden md:block absolute left-1/2 top-10 bottom-10 w-px bg-purple-200 dark:bg-purple-800/30"
				></div>

				<!-- First -->
				<div class="flex flex-col items-center text-center">
					<span
						class="text-xs font-black tracking-[0.2em] text-purple-500 uppercase mb-6 bg-purple-100 dark:bg-purple-800/40 px-3 py-1 rounded-full"
						>{$t('dashboard.theater.first')}</span
					>
					{#if showExtremes.first}
						{@const showImg = getShowImage(showExtremes.first.event.title)}
						<div
							class="w-48 h-64 md:w-64 md:h-80 rounded-2xl bg-gray-200 dark:bg-gray-800 shadow-xl mb-6 overflow-hidden relative group border border-purple-100 dark:border-purple-500/20"
						>
							{#if showImg}
								<img
									src={showImg}
									alt={showExtremes.first.event.title}
									class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
								/>
								<div
									class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60"
								></div>
							{:else}
								<div class="w-full h-full flex items-center justify-center text-purple-300">
									<Star class="w-16 h-16" />
								</div>
							{/if}
						</div>
						<h4 class="text-2xl font-black text-themed mb-2 leading-tight">
							{showExtremes.first.event.title}
						</h4>
						<p class="text-lg font-bold text-purple-600 dark:text-purple-400 mb-1">
							{formatDate(showExtremes.first.event.date)}
						</p>
						<p class="text-sm font-bold text-gray-400">
							{$t('dashboard.seatMap.row')}
							{showExtremes.first.seat.section.trim().charAt(0)} - {showExtremes.first.seat.number}
						</p>
					{:else}
						<p class="text-gray-400 italic">No data</p>
					{/if}
				</div>

				<!-- Last -->
				<div class="flex flex-col items-center text-center">
					<span
						class="text-xs font-black tracking-[0.2em] text-purple-500 uppercase mb-6 bg-purple-50 dark:bg-purple-900/20 px-3 py-1 rounded-full"
						>{$t('dashboard.theater.last')}</span
					>
					{#if showExtremes.last}
						{@const showImg = getShowImage(showExtremes.last.event.title)}
						<div
							class="w-48 h-64 md:w-64 md:h-80 rounded-2xl bg-gray-200 dark:bg-zinc-800 shadow-xl mb-6 overflow-hidden relative group border border-purple-100 dark:border-purple-500/20"
						>
							{#if showImg}
								<img
									src={showImg}
									alt={showExtremes.last.event.title}
									class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
								/>
								<div
									class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60"
								></div>
							{:else}
								<div class="w-full h-full flex items-center justify-center text-purple-200">
									<Star class="w-16 h-16" />
								</div>
							{/if}
						</div>
						<h4 class="text-2xl font-black text-themed mb-2 leading-tight">
							{showExtremes.last.event.title}
						</h4>
						<p class="text-lg font-bold text-purple-600 dark:text-purple-400 mb-1">
							{formatDate(showExtremes.last.event.date)}
						</p>
						<p class="text-sm font-bold text-gray-400">
							{$t('dashboard.seatMap.row')}
							{showExtremes.last.seat.section.trim().charAt(0)} - {showExtremes.last.seat.number}
						</p>
					{:else}
						<p class="text-gray-400 italic">No data</p>
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- 2-SHOT POPUP -->
{#if showTwoShotPopup}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
		on:click|self={() => (showTwoShotPopup = false)}
		role="dialog"
		aria-modal="true"
	>
		<div
			class="bg-pink-50 dark:bg-zinc-900 w-full max-w-4xl rounded-3xl shadow-2xl overflow-hidden animate-scale-in border border-pink-100 dark:border-pink-500/20"
		>
			<!-- Header -->
			<div
				class="p-6 border-b border-pink-100 dark:border-pink-500/20 flex items-center justify-between bg-pink-50/20 dark:bg-transparent"
			>
				<div class="flex items-center gap-3 text-pink-400">
					<div class="p-2 bg-pink-50 dark:bg-pink-800/40 rounded-xl">
						<Calendar class="w-6 h-6" />
					</div>
					<h3 class="font-bold text-xl text-gray-800 dark:text-gray-100">
						{$t('dashboard.twoShot.firstLast')}
						{!isAllData ? selectedYear : ''}
					</h3>
				</div>
				<button
					on:click={() => (showTwoShotPopup = false)}
					class="p-2 bg-pink-50 dark:bg-pink-800/40 hover:bg-pink-100 dark:hover:bg-pink-700/50 rounded-full transition-colors cursor-pointer"
				>
					<X class="w-6 h-6 text-pink-400 dark:text-pink-400" />
				</button>
			</div>

			<!-- Content -->
			<div class="p-6 md:p-10 grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 relative">
				<div
					class="hidden md:block absolute left-1/2 top-10 bottom-10 w-px bg-pink-200 dark:bg-pink-800/30"
				></div>

				<!-- First -->
				<div class="flex flex-col items-center text-center">
					<span
						class="text-xs font-black tracking-[0.2em] text-pink-400 uppercase mb-6 bg-pink-50 dark:bg-pink-800/40 px-3 py-1 rounded-full"
						>{$t('dashboard.twoShot.first')}</span
					>
					{#if twoShotExtremes.first}
						<div
							class="w-48 h-64 md:w-64 md:h-80 rounded-2xl bg-gray-200 dark:bg-gray-800 shadow-xl mb-6 overflow-hidden relative group border border-pink-100 dark:border-pink-500/20"
						>
							{#if twoShotExtremes.first.two_shot?.imageUrl}
								<img
									src={twoShotExtremes.first.two_shot.imageUrl}
									alt="2-Shot"
									class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
								/>
								<div
									class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60"
								></div>
							{:else}
								<div class="w-full h-full flex items-center justify-center text-pink-300">
									<Camera class="w-16 h-16" />
								</div>
							{/if}
						</div>
						<h4 class="text-2xl font-black text-themed mb-2 leading-tight">
							{twoShotExtremes.first.two_shot?.member_name || '-'}
						</h4>
						<p class="text-lg font-bold text-pink-400 dark:text-pink-400">
							{formatDate(twoShotExtremes.first.event.date)}
						</p>
					{:else}
						<p class="text-gray-400 italic">No data</p>
					{/if}
				</div>

				<!-- Last -->
				<div class="flex flex-col items-center text-center">
					<span
						class="text-xs font-black tracking-[0.2em] text-pink-400 uppercase mb-6 bg-pink-50 dark:bg-pink-800/40 px-3 py-1 rounded-full"
						>{$t('dashboard.twoShot.last')}</span
					>
					{#if twoShotExtremes.last}
						<div
							class="w-48 h-64 md:w-64 md:h-80 rounded-2xl bg-gray-200 dark:bg-gray-800 shadow-xl mb-6 overflow-hidden relative group border border-pink-100 dark:border-pink-500/20"
						>
							{#if twoShotExtremes.last.two_shot?.imageUrl}
								<img
									src={twoShotExtremes.last.two_shot.imageUrl}
									alt="2-Shot"
									class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
								/>
								<div
									class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60"
								></div>
							{:else}
								<div class="w-full h-full flex items-center justify-center text-pink-300">
									<Camera class="w-16 h-16" />
								</div>
							{/if}
						</div>
						<h4 class="text-2xl font-black text-themed mb-2 leading-tight">
							{twoShotExtremes.last.two_shot?.member_name || '-'}
						</h4>
						<p class="text-lg font-bold text-pink-400 dark:text-pink-400">
							{formatDate(twoShotExtremes.last.event.date)}
						</p>
					{:else}
						<p class="text-gray-400 italic">No data</p>
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if}
