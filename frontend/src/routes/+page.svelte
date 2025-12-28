<script lang="ts">
	import { tickets, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { goto } from '$app/navigation';
	import StatCard from '$lib/components/StatCard.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import {
		Ticket as TicketIcon,
		Calendar,
		DollarSign,
		Armchair,
		MapPin,
		Filter,
		ChevronDown,
		LayoutDashboard,
		X,
		Star,
		Grid3X3,
		AlignJustify,
		Heart,
		Camera,
		ChevronRight,
		Crown,
		User,
		Wallet,
		Users,
		TrendingUp
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';

	const { t } = useTranslation();

	let mounted = false;

	onMount(() => {
		mounted = true;
	});

	// Loading state - show skeleton when:
	// 1. Not mounted yet (SSR or initial client render)
	// 2. Authenticated but data is not loaded yet
	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded);

	// Constants
	const SHOW_IMAGES = [
		{
			title: 'Pertaruhan Cinta',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1760105446/wwiaxahqs3ti0lhqdszz.jpg'
		},
		{
			title: 'Pajama Drive',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1717174034/xspjxcs9wwm9jxwhiy5q.jpg'
		},
		{
			title: 'Aturan Anti Cinta',
			image:
				'https://cdn.idntimes.com/content-images/post/20251115/50a27780-93e7-4e40-8474-60f6e0cca6da-251115200115.jpg'
		},
		{
			title: 'Sambil Menggandeng Erat Tanganku',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1743898507/nvw4gqjtdhje2ftxt9i1.jpg'
		},
		{
			title: 'Cara Meminum Ramune',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1702404446/nixg3rixpjpom3xa0ivf.jpg'
		},
		{
			title: 'Ingin Bertemu',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1697224788/uploads/w2zvghwk8tocey8e8xhv.jpg'
		},
		{
			title: 'KIRA KIRA GIRLS',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1763233779/tanfbrrf8oexxmmfoouh.jpg'
		}
	];

	const MONTHS = [
		'January',
		'February',
		'March',
		'April',
		'May',
		'June',
		'July',
		'August',
		'September',
		'October',
		'November',
		'December'
	];
	const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
	const THEATER_ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
	const ROW_SEAT_COUNTS: Record<string, number> = {
		A: 22,
		B: 23,
		C: 25,
		D: 26,
		E: 26,
		F: 28,
		G: 28,
		H: 27,
		I: 26,
		J: 26
	};

	// State
	const currentYear: number = new Date().getFullYear();
	let selectedYear: number = currentYear;
	let startMonth: number = 0;
	let endMonth: number = 11;
	let isFilterOpen: boolean = false;
	let mapView: 'ROWS' | 'SEATS' = 'SEATS';
	let isAllData: boolean = false;

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
			if (THEATER_ROWS.includes(r)) counts[r] = (counts[r] || 0) + 1;
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
			kamiOshi: ranking[0] || null
		};
	})() as {
		ranking: { name: string; count: number; image?: string }[];
		totalSpend: number;
		totalCount: number;
		uniqueCount: number;
		kamiOshi: { name: string; count: number; image?: string } | null;
	};

	// Most frequent row for card
	$: mostFrequentRow = (Object.entries(rowStats.counts).sort((a, b) => b[1] - a[1])[0]?.[0] ||
		'-') as string;

	// Helper for rendering detailed row
	const getSeatsForRow = (row: string, total: number) => {
		const seats = [];
		for (let i = 1; i <= total; i++) seats.push(i);
		return seats;
	};
</script>

<SEO title={$t('dashboard.title')} path="/" description={$t('seo.dashboard')} />

<div class="space-y-6 p-4 pb-32 max-w-7xl mx-auto">
	<!-- Header / Filter Toggle -->
	<div class="mb-6">
		{#if isFilterOpen}
			<div class="glass-panel p-4 rounded-3xl animate-fade-in">
				<div class="flex items-start justify-between mb-4 md:mb-0 md:items-center gap-4">
					<div class="flex items-center gap-3">
						<div
							class="bg-red-50 dark:bg-red-500/20 p-2.5 rounded-xl text-red-600 dark:text-red-400 shadow-sm ring-1 ring-red-100 dark:ring-red-500/30"
						>
							<Filter class="w-5 h-5" />
						</div>
						<div>
							<h2 class="font-bold text-gray-800 dark:text-gray-100 text-lg leading-none">
								{$t('dashboard.filterTitle')}
							</h2>
							<p class="text-xs text-gray-400 font-medium mt-1">
								{$t('dashboard.filterSubtitle')}
							</p>
						</div>
					</div>
					<button
						on:click={() => (isFilterOpen = false)}
						class="p-2 hover:bg-red-50 dark:hover:bg-white/5 text-gray-400 hover:text-red-500 dark:hover:text-red-400 rounded-full transition-colors cursor-pointer"
					>
						<X class="w-5 h-5" />
					</button>
				</div>

				<!-- All Data Toggle -->
				<div class="mt-4 flex items-center gap-3">
					<button
						on:click={() => (isAllData = !isAllData)}
						class={`relative flex items-center px-4 py-2.5 rounded-xl font-bold text-sm transition-all w-full justify-center gap-2 cursor-pointer ${isAllData ? 'bg-red-600 text-white shadow-lg shadow-red-200 dark:shadow-red-900/20' : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-white/10'}`}
					>
						<span
							class={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${isAllData ? 'border-white bg-white' : 'border-gray-400'}`}
						>
							{#if isAllData}
								<span class="w-2 h-2 rounded-full bg-red-600"></span>
							{/if}
						</span>
						{$t('common.allData')}
					</button>
				</div>

				<div
					class="mt-4 md:mt-4 grid grid-cols-1 md:grid-cols-2 gap-3 w-full {isAllData
						? 'opacity-50 pointer-events-none'
						: ''}"
				>
					<div class="relative group w-full">
						<select
							bind:value={selectedYear}
							disabled={isAllData}
							class="w-full appearance-none bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 pl-10 pr-10 py-2.5 rounded-xl text-sm font-bold text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500 shadow-sm cursor-pointer hover:border-red-200 dark:hover:border-red-500/50 transition-colors disabled:cursor-not-allowed disabled:bg-gray-100 dark:disabled:bg-gray-900"
						>
							{#each availableYears as y}
								<option value={y}>{y}</option>
							{/each}
						</select>
						<Calendar class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-red-400" />
						<ChevronDown
							class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none group-hover:text-red-400 transition-colors"
						/>
					</div>

					<div
						class="flex items-center bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl shadow-sm w-full overflow-hidden h-[42px]"
					>
						<div
							class="relative flex-1 h-full border-r border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
						>
							<select
								bind:value={startMonth}
								disabled={isAllData}
								class="w-full h-full appearance-none bg-transparent pl-9 pr-2 text-xs font-bold text-gray-700 dark:text-gray-200 focus:outline-none cursor-pointer disabled:cursor-not-allowed"
							>
								{#each MONTHS as m, i}
									<option value={i}>{m.substring(0, 3)}</option>
								{/each}
							</select>
							<span
								class="absolute left-3 top-1/2 -translate-y-1/2 text-[10px] font-extrabold text-gray-400 uppercase tracking-wider pointer-events-none"
								>Fr</span
							>
						</div>

						<div
							class="relative flex-1 h-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
						>
							<select
								bind:value={endMonth}
								disabled={isAllData}
								class="w-full h-full appearance-none bg-transparent pl-9 pr-2 text-xs font-bold text-gray-700 focus:outline-none cursor-pointer disabled:cursor-not-allowed"
							>
								{#each MONTHS as m, i}
									<option value={i}>{m.substring(0, 3)}</option>
								{/each}
							</select>
							<span
								class="absolute left-3 top-1/2 -translate-y-1/2 text-[10px] font-extrabold text-gray-400 uppercase tracking-wider pointer-events-none"
								>To</span
							>
						</div>
					</div>
				</div>
			</div>
		{:else}
			<div class="flex items-center justify-between animate-fade-in">
				<div class="flex items-center gap-3">
					<div
						class="p-3 rounded-2xl bg-red-50 dark:bg-red-500/20 text-red-600 dark:text-red-400 shadow-lg shadow-red-100 dark:shadow-red-900/30 border-2 border-white dark:border-gray-800 transform -rotate-6"
					>
						<LayoutDashboard class="w-6 h-6" />
					</div>
					<div>
						<h2 class="text-2xl font-bold text-themed leading-none relative w-fit">
							{$t('dashboard.title')}
							<span
								class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 dark:bg-red-500/30 -z-10 transform -skew-x-12 rounded-sm"
							></span>
						</h2>
						<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{$t('dashboard.subtitle')}</p>
					</div>
				</div>
				<div class="flex items-center gap-2">
					<span
						class="text-xs font-bold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-zinc-900 px-3 py-1.5 rounded-full border border-gray-200 dark:border-zinc-700"
					>
						{filterLabel}
					</span>
					<button
						on:click={() => (isFilterOpen = true)}
						class="flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-zinc-900 text-gray-600 dark:text-gray-300 font-bold text-xs shadow-sm border border-gray-200 dark:border-zinc-700 hover:border-red-200 dark:hover:border-red-500/50 hover:text-red-600 dark:hover:text-red-400 transition-all cursor-pointer"
					>
						<Filter class="w-4 h-4" />
						<span class="hidden sm:inline">{$t('common.filters')}</span>
					</button>
				</div>
			</div>
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
					sub={$t('dashboard.theater.inYear', { year: selectedYear })}
					icon={TicketIcon}
					colorClass="bg-red-600/10 text-red-600"
					loading={isLoading}
				/>
				<StatCard
					title={$t('dashboard.theater.spending')}
					value={new Intl.NumberFormat('id-ID', {
						style: 'currency',
						currency: 'IDR',
						maximumFractionDigits: 0
					}).format(totalSpent)}
					sub={$t('dashboard.theater.totalExpenses')}
					icon={DollarSign}
					colorClass="bg-emerald-500/10 text-emerald-500"
					loading={isLoading}
				/>
				<StatCard
					title={$t('dashboard.theater.topRow')}
					value={mostFrequentRow}
					sub={$t('dashboard.theater.mostFrequentSeat')}
					icon={Armchair}
					colorClass="bg-amber-500/10 text-amber-500"
					loading={isLoading}
				/>

				<div
					class="glass-card rounded-3xl relative overflow-hidden group hover:shadow-lg transition-all duration-300 flex flex-col h-full bg-purple-50/50 dark:bg-transparent border-purple-100 dark:border-purple-500/20"
				>
					<div class="p-5 pb-0 flex justify-between items-start">
						<div class="flex items-center gap-2 text-purple-500">
							<div class="p-1.5 bg-purple-100 dark:bg-purple-800/40 rounded-lg">
								<Star class="w-4 h-4 fill-current" />
							</div>
							<span class="font-bold text-xs tracking-wider text-purple-500 dark:text-purple-400"
								>{$t('dashboard.theater.topShow')}</span
							>
						</div>
						<Crown class="w-5 h-5 text-yellow-400 fill-current" />
					</div>
					<div class="p-5 flex items-center gap-4">
						{#if isLoading}
							<!-- Skeleton Loading -->
							<div
								class="w-14 h-14 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse flex-shrink-0"
							></div>
							<div class="min-w-0 flex-1">
								<div class="h-2 w-16 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse mb-2"></div>
								<div class="h-5 w-28 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse mb-1"></div>
								<div class="h-3 w-12 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
							</div>
						{:else}
							<div
								class="w-14 h-14 rounded-full p-0.5 bg-gradient-to-tr from-indigo-400 via-purple-500 to-fuchsia-500 flex-shrink-0"
							>
								<div
									class="w-full h-full rounded-full border-2 border-white dark:border-gray-800 overflow-hidden bg-white dark:bg-gray-800 flex items-center justify-center"
								>
									{#if topShowStats.image}
										<img
											src={topShowStats.image}
											alt={topShowStats.title}
											class="w-full h-full object-cover"
										/>
									{:else}
										<Star class="w-6 h-6 text-purple-500 fill-purple-100" />
									{/if}
								</div>
							</div>
							<div class="min-w-0">
								<p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
									{$t('dashboard.theater.mostWatched')}
								</p>
								<h3
									class={`font-black text-themed leading-none mb-0.5 truncate ${topShowStats.title.length > 15 ? 'text-sm' : 'text-lg'}`}
									title={topShowStats.title}
								>
									{topShowStats.title}
								</h3>
								<p class="text-sm font-bold text-purple-500">
									{topShowStats.count}
									{$t('shows.unit')}
								</p>
							</div>
						{/if}
					</div>
					{#if isLoading}
						<div
							class="mt-auto border-t border-purple-100 dark:border-purple-800/30 p-3 w-full flex justify-center"
						>
							<div class="h-4 w-24 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
						</div>
					{:else}
						<button
							on:click={() => goto('/shows')}
							class="mt-auto border-t border-purple-100 dark:border-purple-800/30 p-3 w-full text-center text-xs font-bold text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 transition-colors flex items-center justify-center gap-1 relative z-20 cursor-pointer"
						>
							{$t('common.viewDetails')}
							<ChevronRight class="w-3 h-3" />
						</button>
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
					title="2Shot"
					value={twoShotStats.totalCount}
					sub={$t('dashboard.twoShot.collected')}
					icon={Camera}
					colorClass="bg-pink-500/10 text-pink-500"
					loading={isLoading}
				/>
				<StatCard
					title={$t('dashboard.twoShot.spending')}
					value={new Intl.NumberFormat('id-ID', {
						style: 'currency',
						currency: 'IDR',
						maximumFractionDigits: 0
					}).format(twoShotStats.totalSpend)}
					sub={$t('dashboard.twoShot.totalExpenses')}
					icon={Wallet}
					colorClass="bg-emerald-500/10 text-emerald-500"
					loading={isLoading}
				/>
				<StatCard
					title={$t('dashboard.twoShot.members')}
					value={twoShotStats.uniqueCount}
					sub={$t('dashboard.twoShot.uniqueIdols')}
					icon={Users}
					colorClass="bg-purple-500/10 text-purple-500"
					loading={isLoading}
				/>

				<!-- Top 2-Shot Card -->
				<div
					class="glass-card rounded-3xl relative overflow-hidden group hover:shadow-lg transition-all duration-300 flex flex-col h-full bg-pink-50/50 dark:bg-transparent border-pink-100 dark:border-pink-500/20"
				>
					<div class="p-5 pb-0 flex justify-between items-start">
						<div class="flex items-center gap-2 text-pink-500">
							<div class="flex items-center gap-2 mb-3">
								<Heart class="w-4 h-4 text-pink-500 fill-pink-500" />
								<span class="text-[10px] font-black tracking-widest text-pink-500 uppercase"
									>{$t('dashboard.twoShot.topTwoShot')}</span
								>
							</div>
						</div>
						<Crown class="w-5 h-5 text-yellow-400 fill-current" />
					</div>
					<div class="p-5 flex items-center gap-4">
						{#if isLoading}
							<!-- Skeleton Loading -->
							<div
								class="w-14 h-14 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse flex-shrink-0"
							></div>
							<div class="min-w-0 flex-1">
								<div class="h-2 w-16 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse mb-2"></div>
								<div class="h-5 w-28 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse mb-1"></div>
								<div class="h-3 w-12 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
							</div>
						{:else}
							<div
								class="w-14 h-14 rounded-full p-0.5 bg-gradient-to-tr from-pink-400 via-rose-500 to-red-500 flex-shrink-0"
							>
								<div
									class="w-full h-full rounded-full border-2 border-white dark:border-gray-800 overflow-hidden bg-white dark:bg-gray-800 flex items-center justify-center"
								>
									{#if twoShotStats?.kamiOshi?.image}
										<img
											src={twoShotStats.kamiOshi.image}
											alt={twoShotStats.kamiOshi.name}
											class="w-full h-full object-cover"
										/>
									{:else}
										<User class="w-6 h-6 text-pink-500 fill-pink-100" />
									{/if}
								</div>
							</div>
							<div class="min-w-0">
								<p class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">
									{$t('dashboard.twoShot.kamiOshi')}
								</p>
								<h3
									class={`font-black text-themed leading-none mb-0.5 truncate ${(twoShotStats?.kamiOshi?.name?.length ?? 0) > 15 ? 'text-sm' : 'text-lg'}`}
									title={twoShotStats?.kamiOshi?.name || '-'}
								>
									{twoShotStats?.kamiOshi?.name || '-'}
								</h3>
								<p class="text-sm font-bold text-pink-500">
									{twoShotStats?.kamiOshi?.count || 0}
									{$t('dashboard.twoShot.photos')}
								</p>
							</div>
						{/if}
					</div>
					{#if isLoading}
						<div
							class="mt-auto border-t border-pink-100 dark:border-pink-800/30 p-3 w-full flex justify-center"
						>
							<div class="h-4 w-24 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
						</div>
					{:else}
						<button
							on:click={() => goto('/top-2shot')}
							class="mt-auto border-t border-pink-100 dark:border-pink-800/30 p-3 w-full text-center text-xs font-bold text-pink-600 dark:text-pink-400 hover:bg-pink-50 dark:hover:bg-pink-900/30 transition-colors flex items-center justify-center gap-1 cursor-pointer"
						>
							{$t('common.viewDetails')}
							<ChevronRight class="w-3 h-3" />
						</button>
					{/if}
				</div>
			</div>
		</div>
	</div>

	<!-- THEATER MAP -->
	<div class="glass-panel p-6 rounded-3xl">
		<div class="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
			<div>
				<h3 class="text-xl font-bold text-themed">
					{$t('dashboard.seatMap.title')}
				</h3>
				<p class="text-xs text-gray-400">{$t('dashboard.seatMap.subtitle')}</p>
			</div>
			<div class="flex items-center gap-2">
				<div
					class="bg-red-50 dark:bg-red-500/20 text-red-600 dark:text-red-400 px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-2"
				>
					<MapPin class="w-3.5 h-3.5" />
					<span
						>{rowStats.uniqueVisited}/{THEATER_ROWS.length}
						{$t('dashboard.seatMap.rowsCollected')}</span
					>
				</div>
				<div class="bg-gray-100 dark:bg-gray-800 p-1 rounded-lg flex gap-1">
					<button
						on:click={() => (mapView = 'ROWS')}
						class={`p-1.5 rounded-md transition-all cursor-pointer ${mapView === 'ROWS' ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
					>
						<AlignJustify class="w-4 h-4" />
					</button>
					<button
						on:click={() => (mapView = 'SEATS')}
						class={`p-1.5 rounded-md transition-all cursor-pointer ${mapView === 'SEATS' ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
					>
						<Grid3X3 class="w-4 h-4" />
					</button>
				</div>
			</div>
		</div>

		<div class="w-full overflow-x-auto sm:overflow-hidden">
			<div class="w-full mx-auto px-2">
				<div class="w-full min-w-[700px]">
					<div
						class="w-3/4 mx-auto h-4 bg-gradient-to-b from-gray-200 dark:from-gray-700 to-white dark:to-gray-800 rounded-t-2xl mb-8 relative shadow-sm border-t border-x border-gray-300 dark:border-gray-600"
					>
						<div class="absolute inset-0 bg-red-600 opacity-5 blur-xl"></div>
						<div
							class="absolute -top-6 left-1/2 -translate-x-1/2 bg-gray-100 dark:bg-gray-800 px-4 py-1 rounded-full border border-gray-200 dark:border-gray-700"
						>
							<span
								class="text-[10px] font-black tracking-[0.3em] text-gray-400 uppercase block text-center"
								>{$t('dashboard.seatMap.stage')}</span
							>
						</div>
					</div>

					<!-- MAP VIEW: ROWS -->
					{#if mapView === 'ROWS'}
						{#if isLoading}
							<!-- Skeleton Loading for Rows -->
							<div class="grid grid-cols-2 gap-x-4 md:gap-x-12 gap-y-3 max-w-5xl mx-auto">
								{#each THEATER_ROWS as row}
									<div class="flex items-center gap-3">
										<div
											class="w-9 h-9 md:w-10 md:h-10 flex-shrink-0 rounded-xl bg-gray-200 dark:bg-zinc-700 animate-pulse"
										></div>
										<div
											class="flex-1 h-9 md:h-10 rounded-xl bg-gray-200 dark:bg-zinc-700 animate-pulse"
										></div>
									</div>
								{/each}
							</div>
						{:else}
							<div class="grid grid-cols-2 gap-x-4 md:gap-x-12 gap-y-3 max-w-5xl mx-auto">
								{#each THEATER_ROWS as row}
									{@const count = rowStats.counts[row] || 0}
									{@const intensity = rowStats.maxCount > 0 ? count / rowStats.maxCount : 0}
									{@const hasData = count > 0}
									<div class="flex items-center gap-3 group">
										<div
											class={`w-9 h-9 md:w-10 md:h-10 flex-shrink-0 flex items-center justify-center rounded-xl text-sm font-bold transition-all duration-300 shadow-sm ${!hasData ? 'bg-gray-100 dark:bg-gray-800 text-gray-400' : ''}`}
											style={hasData
												? `background-color: rgba(220, 38, 38, ${0.2 + intensity * 0.8}); color: ${intensity > 0.4 ? 'white' : '#dc2626'}; box-shadow: 0 4px 12px -2px rgba(220, 38, 38, ${intensity * 0.5})`
												: ''}
										>
											{row}
										</div>
										<div
											class={`flex-1 h-9 md:h-10 rounded-xl flex items-center px-3 md:px-4 relative overflow-hidden transition-all duration-300 ${hasData ? 'bg-white dark:bg-gray-800 border border-red-100 dark:border-red-500/30 shadow-sm' : 'bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700 border-dashed'}`}
										>
											{#if hasData}
												<div
													class="absolute left-0 top-0 bottom-0 transition-all duration-1000"
													style={`width: ${intensity * 100}%; background-color: rgba(220, 38, 38, ${0.1 + intensity * 0.9});`}
												>
													<div
														class="absolute right-0 top-0 bottom-0 w-[1px] bg-red-400 opacity-20"
													></div>
												</div>
											{/if}
											<div class="relative z-10 w-full flex justify-between items-center px-1">
												<span
													class={`text-[10px] md:text-xs font-bold uppercase tracking-wide transition-colors duration-300 ${hasData && intensity <= 0.3 ? 'text-gray-600 dark:text-gray-300' : ''} ${!hasData ? 'text-gray-300 dark:text-gray-600' : ''}`}
													style={hasData && intensity > 0.3
														? 'color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.3)'
														: ''}>{$t('dashboard.seatMap.row')} {row}</span
												>
												<span
													class={`text-base md:text-lg font-black transition-colors duration-300 ${hasData && intensity <= 0.85 ? 'text-red-600 dark:text-red-400' : ''} ${!hasData ? 'text-gray-300 dark:text-gray-600' : ''}`}
													style={hasData && intensity > 0.85
														? 'color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.3)'
														: ''}>{count}</span
												>
											</div>
										</div>
									</div>
								{/each}
							</div>
						{/if}
					{/if}

					<!-- MAP VIEW: SEATS -->
					{#if mapView === 'SEATS'}
						{@const maxSeatCount = Math.max(...Object.values(seatStats), 1)}
						<!-- Seat structure per row (total 28 max seats + 3 aisles = 31 columns)
							 Layout: [Label] [G1: 6 seats] [Aisle] [G2: 6 seats] [Aisle] [G3: 6 seats] [Aisle] [G4: 10 seats]
						-->
						{@const SEAT_LAYOUT = {
							A: {
								start: 3,
								seats: 22,
								groups: [
									[3, 6],
									[7, 12],
									[13, 18],
									[19, 24]
								]
							},
							B: {
								start: 3,
								seats: 23,
								groups: [
									[3, 6],
									[7, 12],
									[13, 18],
									[19, 25]
								]
							},
							C: {
								start: 2,
								seats: 25,
								groups: [
									[2, 6],
									[7, 12],
									[13, 18],
									[19, 26]
								]
							},
							D: {
								start: 2,
								seats: 26,
								groups: [
									[2, 6],
									[7, 12],
									[13, 18],
									[19, 27]
								]
							},
							E: {
								start: 2,
								seats: 26,
								groups: [
									[2, 6],
									[7, 12],
									[13, 18],
									[19, 27]
								]
							},
							F: {
								start: 1,
								seats: 28,
								groups: [
									[1, 6],
									[7, 12],
									[13, 18],
									[19, 28]
								]
							},
							G: {
								start: 1,
								seats: 28,
								groups: [
									[1, 6],
									[7, 12],
									[13, 18],
									[19, 28]
								]
							},
							H: {
								start: 1,
								seats: 27,
								groups: [
									[1, 6],
									[7, 12],
									[13, 18],
									[19, 27]
								]
							},
							I: {
								start: 2,
								seats: 26,
								groups: [
									[2, 6],
									[7, 12],
									[13, 18],
									[19, 27]
								]
							},
							J: {
								start: 2,
								seats: 26,
								groups: [
									[2, 6],
									[7, 12],
									[13, 18],
									[19, 27]
								]
							}
						}}
						{#if isLoading}
							<!-- Skeleton Loading for Seats -->
							<div class="space-y-2 max-w-5xl mx-auto">
								{#each THEATER_ROWS as row}
									<div class="flex items-center gap-2">
										<div
											class="w-8 h-8 rounded-lg bg-gray-200 dark:bg-zinc-700 animate-pulse flex-shrink-0"
										></div>
										<div class="flex-1 flex gap-1">
											{#each Array(28) as _, i}
												<div
													class="w-5 h-5 rounded bg-gray-200 dark:bg-zinc-700 animate-pulse"
												></div>
											{/each}
										</div>
									</div>
								{/each}
							</div>
						{:else}
							<div class="seat-map-grid">
								{#each THEATER_ROWS as row}
									{@const layout = SEAT_LAYOUT[/** @type {keyof typeof SEAT_LAYOUT} */ (row)]}
									<div class="grid-row">
										<!-- Row Label -->
										<div class="row-label">{row}</div>

										<!-- Group 1 (columns 1-6) -->
										{#each [1, 2, 3, 4, 5, 6] as col}
											{@const seatNum = col - layout.start + 1}
											{@const isValidSeat =
												col >= layout.groups[0][0] && col <= layout.groups[0][1]}
											{@const seatKey = `${row}-${seatNum}`}
											{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
											{@const hasVisit = count > 0}
											{@const intensity = hasVisit ? Math.max(0.25, count / maxSeatCount) : 0}

											{#if isValidSeat}
												<div
													class="map-seat {hasVisit ? 'active' : ''}"
													style={hasVisit ? `--intensity: ${intensity}` : ''}
													data-title="{seatKey}: {count}x"
												>
													<span class="seat-id">{seatKey}</span>
													{#if hasVisit}<span class="seat-count">{count}x</span>{/if}
												</div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}

										<!-- Aisle 1 -->
										<div class="aisle-gap"></div>

										<!-- Group 2 (columns 7-12) -->
										{#each [7, 8, 9, 10, 11, 12] as col}
											{@const seatNum = col - layout.start + 1}
											{@const isValidSeat =
												col >= layout.groups[1][0] && col <= layout.groups[1][1]}
											{@const seatKey = `${row}-${seatNum}`}
											{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
											{@const hasVisit = count > 0}
											{@const intensity = hasVisit ? Math.max(0.25, count / maxSeatCount) : 0}

											{#if isValidSeat}
												<div
													class="map-seat {hasVisit ? 'active' : ''}"
													style={hasVisit ? `--intensity: ${intensity}` : ''}
													data-title="{seatKey}: {count}x"
												>
													<span class="seat-id">{seatKey}</span>
													{#if hasVisit}<span class="seat-count">{count}x</span>{/if}
												</div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}

										<!-- Aisle 2 -->
										<div class="aisle-gap"></div>

										<!-- Group 3 (columns 13-18) -->
										{#each [13, 14, 15, 16, 17, 18] as col}
											{@const seatNum = col - layout.start + 1}
											{@const isValidSeat =
												col >= layout.groups[2][0] && col <= layout.groups[2][1]}
											{@const seatKey = `${row}-${seatNum}`}
											{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
											{@const hasVisit = count > 0}
											{@const intensity = hasVisit ? Math.max(0.25, count / maxSeatCount) : 0}

											{#if isValidSeat}
												<div
													class="map-seat {hasVisit ? 'active' : ''}"
													style={hasVisit ? `--intensity: ${intensity}` : ''}
													data-title="{seatKey}: {count}x"
												>
													<span class="seat-id">{seatKey}</span>
													{#if hasVisit}<span class="seat-count">{count}x</span>{/if}
												</div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}

										<!-- Aisle 3 -->
										<div class="aisle-gap"></div>

										<!-- Group 4 (columns 19-28) -->
										{#each [19, 20, 21, 22, 23, 24, 25, 26, 27, 28] as col}
											{@const seatNum = col - layout.start + 1}
											{@const isValidSeat =
												col >= layout.groups[3][0] && col <= layout.groups[3][1]}
											{@const seatKey = `${row}-${seatNum}`}
											{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
											{@const hasVisit = count > 0}
											{@const intensity = hasVisit ? Math.max(0.25, count / maxSeatCount) : 0}

											{#if isValidSeat}
												<div
													class="map-seat {hasVisit ? 'active' : ''}"
													style={hasVisit ? `--intensity: ${intensity}` : ''}
													data-title="{seatKey}: {count}x"
												>
													<span class="seat-id">{seatKey}</span>
													{#if hasVisit}<span class="seat-count">{count}x</span>{/if}
												</div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}
									</div>
								{/each}
							</div>
						{/if}
					{/if}
				</div>
			</div>
		</div>
	</div>

	<div class="grid lg:grid-cols-3 gap-6">
		<!-- Monthly Heatmap -->
		<div class="glass-panel p-6 rounded-3xl lg:col-span-2 flex flex-col">
			<div class="mb-6">
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
			<div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3 flex-1">
				{#if isLoading}
					<!-- Skeleton Loading for Monthly -->
					{#each Array(12) as _, i}
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
							month.count > 0 ? 0.2 + (month.count / monthlyStats.maxCount) * 0.7 : 0.05}
						{@const hasData = month.count > 0}
						<div
							class={`flex flex-col items-center group ${!month.isActive ? 'opacity-30 grayscale pointer-events-none' : ''}`}
						>
							<div
								class="w-full aspect-square rounded-2xl mb-2 flex flex-col items-center justify-center relative overflow-hidden transition-all duration-300 group-hover:-translate-y-1 border border-transparent shadow-sm dark:border-gray-700"
								style={`background: ${hasData ? `rgba(227, 0, 15, ${intensity})` : 'var(--color-surface)'}; border-color: ${hasData ? 'transparent' : 'var(--color-border-light)'}`}
							>
								{#if hasData}
									<span class="text-xl md:text-2xl font-bold text-white drop-shadow-sm"
										>{month.count}</span
									>
									<span class="text-[8px] text-white/80 font-medium uppercase tracking-wider"
										>{$t('shows.unit')}</span
									>
								{:else}
									<span class="text-gray-300 dark:text-gray-600 text-xl font-bold opacity-30"
										>-</span
									>
								{/if}
							</div>
							<div class="text-center w-full">
								<span
									class="text-[10px] font-bold text-gray-500 dark:text-gray-400 block uppercase tracking-wide"
									>{$t('time.monthsShort.' + month.name.substring(0, 3).toLowerCase())}</span
								>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</div>

		<!-- Day Preference List (Replacing Pie Chart for now) -->
		<!-- Day Preference Grid -->
		<div class="glass-panel p-6 rounded-3xl flex flex-col">
			<div class="mb-6">
				<h3 class="text-xl font-bold text-themed">
					{$t('dashboard.dayPreference.title')}
				</h3>
				<p class="text-xs text-gray-400">{$t('dashboard.dayPreference.subtitle')}</p>
			</div>

			<div class="grid grid-cols-3 sm:grid-cols-4 gap-3 flex-1 content-start">
				{#if isLoading}
					<!-- Skeleton Loading for Days -->
					{#each Array(7) as _, i}
						<div class="flex flex-col items-center">
							<div
								class="w-full aspect-square rounded-2xl mb-2 bg-gray-200 dark:bg-zinc-700 animate-pulse"
							></div>
							<div class="h-3 w-8 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
						</div>
					{/each}
				{:else}
					{#each dayStats.stats as day}
						{@const intensity = day.count > 0 ? 0.2 + (day.count / dayStats.maxCount) * 0.7 : 0.05}
						{@const hasData = day.count > 0}
						<div class="flex flex-col items-center group">
							<div
								class="w-full aspect-square rounded-2xl mb-2 flex flex-col items-center justify-center relative overflow-hidden transition-all duration-300 group-hover:-translate-y-1 border border-transparent shadow-sm dark:border-gray-700"
								style={`background: ${hasData ? `rgba(227, 0, 15, ${intensity})` : 'var(--color-surface)'}; border-color: ${hasData ? 'transparent' : 'var(--color-border-light)'}`}
							>
								{#if hasData}
									<span class="text-xl md:text-2xl font-bold text-white drop-shadow-sm"
										>{day.count}</span
									>
									<span class="text-[8px] text-white/80 font-medium uppercase tracking-wider"
										>{$t('shows.unit')}</span
									>
								{:else}
									<span class="text-gray-300 dark:text-gray-600 text-xl font-bold opacity-30"
										>-</span
									>
								{/if}
							</div>
							<div class="text-center w-full">
								<span
									class="text-[10px] font-bold text-gray-500 dark:text-gray-400 block uppercase tracking-wide"
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
