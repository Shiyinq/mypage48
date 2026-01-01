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
		Top2ShotCard,
		FirstLastCard,
		MonthlyAttendance,
		DayPreference,
		FirstLastPopup
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
				<!-- First & Last Show Card -->
				<FirstLastCard
					title={`${$t('dashboard.theater.firstLast')} ${!isAllData ? selectedYear : ''}`}
					type="theater"
					loading={isLoading}
					onExpand={() => (showTheaterPopup = true)}
					first={showExtremes.first
						? {
								image: getShowImage(showExtremes.first.event.title),
								title: showExtremes.first.event.title,
								date: formatDate(showExtremes.first.event.date),
								detail: `Row ${showExtremes.first.seat.section.trim().charAt(0)} - ${showExtremes.first.seat.number}`
							}
						: null}
					last={showExtremes.last
						? {
								image: getShowImage(showExtremes.last.event.title),
								title: showExtremes.last.event.title,
								date: formatDate(showExtremes.last.event.date),
								detail: `Row ${showExtremes.last.seat.section.trim().charAt(0)} - ${showExtremes.last.seat.number}`
							}
						: null}
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
				<FirstLastCard
					title={`${$t('dashboard.twoShot.firstLast')} ${!isAllData ? selectedYear : ''}`}
					type="twoShot"
					loading={isLoading}
					onExpand={() => (showTwoShotPopup = true)}
					first={twoShotExtremes.first
						? {
								image: twoShotExtremes.first.two_shot?.imageUrl,
								title: twoShotExtremes.first.two_shot?.member_name || '-',
								date: formatDate(twoShotExtremes.first.event.date)
							}
						: null}
					last={twoShotExtremes.last
						? {
								image: twoShotExtremes.last.two_shot?.imageUrl,
								title: twoShotExtremes.last.two_shot?.member_name || '-',
								date: formatDate(twoShotExtremes.last.event.date)
							}
						: null}
				/>
			</div>
		</div>
	</div>

	<!-- THEATER MAP -->
	<TheaterSeatMap {rowStats} {seatStats} {isLoading} />

	<div class="grid lg:grid-cols-3 gap-6">
		<MonthlyAttendance
			stats={monthlyStats.stats}
			maxCount={monthlyStats.maxCount}
			loading={isLoading}
			subtitle={isAllData
				? availableYears.length > 1
					? `${Math.min(...availableYears)} - ${Math.max(...availableYears)}`
					: `${availableYears[0]}`
				: `${selectedYear}`}
		/>

		<DayPreference stats={dayStats.stats} maxCount={dayStats.maxCount} loading={isLoading} />
	</div>
</div>

<!-- THEATER POPUP -->
<FirstLastPopup
	show={showTheaterPopup}
	onClose={() => (showTheaterPopup = false)}
	title={`${$t('dashboard.theater.firstLast')} ${!isAllData ? selectedYear : ''}`}
	type="theater"
	first={showExtremes.first
		? {
				image: getShowImage(showExtremes.first.event.title),
				title: showExtremes.first.event.title,
				date: formatDate(showExtremes.first.event.date),
				detail: `${$t('dashboard.seatMap.row')} ${showExtremes.first.seat.section.trim().charAt(0)} - ${showExtremes.first.seat.number}`
			}
		: null}
	last={showExtremes.last
		? {
				image: getShowImage(showExtremes.last.event.title),
				title: showExtremes.last.event.title,
				date: formatDate(showExtremes.last.event.date),
				detail: `${$t('dashboard.seatMap.row')} ${showExtremes.last.seat.section.trim().charAt(0)} - ${showExtremes.last.seat.number}`
			}
		: null}
/>

<!-- 2-SHOT POPUP -->
<FirstLastPopup
	show={showTwoShotPopup}
	onClose={() => (showTwoShotPopup = false)}
	title={`${$t('dashboard.twoShot.firstLast')} ${!isAllData ? selectedYear : ''}`}
	type="twoShot"
	first={twoShotExtremes.first
		? {
				image: twoShotExtremes.first.two_shot?.imageUrl,
				title: twoShotExtremes.first.two_shot?.member_name || '-',
				date: formatDate(twoShotExtremes.first.event.date)
			}
		: null}
	last={twoShotExtremes.last
		? {
				image: twoShotExtremes.last.two_shot?.imageUrl,
				title: twoShotExtremes.last.two_shot?.member_name || '-',
				date: formatDate(twoShotExtremes.last.event.date)
			}
		: null}
/>
