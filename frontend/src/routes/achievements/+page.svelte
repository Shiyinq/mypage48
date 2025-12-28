<script lang="ts">
	import { tickets, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { onMount } from 'svelte';
	import SEO from '$lib/components/SEO.svelte';
	import {
		Trophy,
		Star,
		Calendar,
		Crown,
		Zap,
		Heart,
		MapPin,
		Wallet,
		Lock,
		Check,
		Armchair,
		Award,
		Medal,
		Binoculars,
		Sparkles,
		History,
		Flame,
		Ticket as TicketIcon
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Milestone {
		id: string;
		title: string;
		description: string;
		icon: any;
		isUnlocked: boolean;
		progress?: string;
		color: string;
	}

	$: milestones = (() => {
		const totalShows = $tickets.length;

		// Date Calculations
		const sortedDates = [...$tickets]
			.map((t) => new Date(t.event.date).getTime())
			.sort((a, b) => a - b);

		const firstDate = sortedDates[0];
		const lastDate = sortedDates[sortedDates.length - 1];
		const timeSpanDays = firstDate && lastDate ? (lastDate - firstDate) / (1000 * 60 * 60 * 24) : 0;

		// Show Counts
		const showCounts: Record<string, number> = {};
		$tickets.forEach((t) => {
			const title = t.event.title.trim();
			showCounts[title] = (showCounts[title] || 0) + 1;
		});
		const maxSameShow = Math.max(...Object.values(showCounts), 0);

		// Row Calculations
		const hasRowA = $tickets.some((t) => t.seat.section.toUpperCase() === 'A');
		const hasRowJ = $tickets.some((t) => t.seat.section.toUpperCase() === 'J');

		// Full Row Collection (A-J)
		const collectedRows = new Set(
			$tickets.map((t) => t.seat.section.trim().toUpperCase().charAt(0))
		);
		const targetRows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
		const uniqueRowsCount = targetRows.filter((r) => collectedRows.has(r)).length;

		// Spending
		const totalSpent = $tickets.reduce((acc, t) => acc + t.price, 0);

		return [
			{
				id: 'first_show',
				title: 'First Step',
				description: 'Attended your first theater show',
				icon: Heart,
				isUnlocked: totalShows >= 1,
				color: 'red'
			},
			{
				id: 'regular_visitor',
				title: 'Regular Visitor',
				description: 'Attended 10 shows',
				icon: TicketIcon,
				isUnlocked: totalShows >= 10,
				progress: `${Math.min(totalShows, 10)}/10`,
				color: 'orange'
			},
			{
				id: 'dedicated_fan_50',
				title: 'Dedicated Fan',
				description: 'Attended 50 shows',
				icon: Award,
				isUnlocked: totalShows >= 50,
				progress: `${Math.min(totalShows, 50)}/50`,
				color: 'cyan'
			},
			{
				id: 'century_club_100',
				title: 'Century Club',
				description: 'Attended 100 shows',
				icon: Medal,
				isUnlocked: totalShows >= 100,
				progress: `${Math.min(totalShows, 100)}/100`,
				color: 'violet'
			},
			{
				id: 'theater_icon_150',
				title: 'Theater Icon',
				description: 'Attended 150 shows',
				icon: Zap,
				isUnlocked: totalShows >= 150,
				progress: `${Math.min(totalShows, 150)}/150`,
				color: 'fuchsia'
			},
			{
				id: 'legendary_wota_200',
				title: 'Legendary Wota',
				description: 'Attended 200 shows',
				icon: Crown,
				isUnlocked: totalShows >= 200,
				progress: `${Math.min(totalShows, 200)}/200`,
				color: 'rose'
			},
			{
				id: 'theater_kami_300',
				title: 'Theater Kami',
				description: 'Attended 300 shows',
				icon: Sparkles,
				isUnlocked: totalShows >= 300,
				progress: `${Math.min(totalShows, 300)}/300`,
				color: 'purple'
			},
			{
				id: 'absolute_legend_500',
				title: 'Absolute Legend',
				description: 'Attended 500 shows',
				icon: Trophy,
				isUnlocked: totalShows >= 500,
				progress: `${Math.min(totalShows, 500)}/500`,
				color: 'amber'
			},
			// Same Show Milestones
			{
				id: 'super_fan',
				title: 'Super Fan',
				description: 'Watched the same event 10 times',
				icon: Star,
				isUnlocked: maxSameShow >= 10,
				progress: `${Math.min(maxSameShow, 10)}/10`,
				color: 'yellow'
			},
			{
				id: 'mega_fan',
				title: 'Mega Fan',
				description: 'Watched the same event 20 times',
				icon: Sparkles,
				isUnlocked: maxSameShow >= 20,
				progress: `${Math.min(maxSameShow, 20)}/20`,
				color: 'orange'
			},
			{
				id: 'ultra_fan',
				title: 'Ultra Fan',
				description: 'Watched the same event 30 times',
				icon: Flame,
				isUnlocked: maxSameShow >= 30,
				progress: `${Math.min(maxSameShow, 30)}/30`,
				color: 'red'
			},
			// Anniversary Milestones
			{
				id: 'theater_enthusiast',
				title: 'Theater Enthusiast',
				description: '1 year anniversary since first show',
				icon: Calendar,
				isUnlocked: timeSpanDays >= 365,
				progress: `${Math.floor(timeSpanDays)}/365 days`,
				color: 'blue'
			},
			{
				id: 'theater_veteran',
				title: 'Theater Veteran',
				description: '2 year anniversary since first show',
				icon: History,
				isUnlocked: timeSpanDays >= 730,
				progress: `${Math.floor(timeSpanDays)}/730 days`,
				color: 'indigo'
			},
			{
				id: 'theater_legend',
				title: 'Theater Legend',
				description: '3 year anniversary since first show',
				icon: Crown,
				isUnlocked: timeSpanDays >= 1095,
				progress: `${Math.floor(timeSpanDays)}/1095 days`,
				color: 'violet'
			},
			// Row Milestones
			{
				id: 'elite_row',
				title: 'Elite Seat',
				description: 'Sat in the legendary Row A',
				icon: Crown,
				isUnlocked: hasRowA,
				color: 'purple'
			},
			{
				id: 'back_row_warrior',
				title: 'Back Row Warrior',
				description: 'Watched from the furthest row (Row J)',
				icon: Binoculars,
				isUnlocked: hasRowJ,
				color: 'indigo'
			},
			{
				id: 'seat_explorer',
				title: 'Seat Explorer',
				description: 'Collected a ticket for every row (A-J)',
				icon: Armchair,
				isUnlocked: uniqueRowsCount >= 10,
				progress: `${uniqueRowsCount}/10`,
				color: 'pink'
			},
			// Spending Milestone
			{
				id: 'supporter',
				title: 'Top Supporter',
				description: 'Spent over 5 Million IDR on tickets',
				icon: Wallet,
				isUnlocked: totalSpent >= 5000000,
				progress: `${(Math.min(totalSpent, 5000000) / 1000000).toFixed(1)}/5M`,
				color: 'emerald'
			}
		] as Milestone[];
	})();

	$: unlocked = milestones.filter((m) => m.isUnlocked);
	$: locked = milestones.filter((m) => !m.isUnlocked);

	/* Loading State */
	let mounted = false;

	onMount(() => {
		mounted = true;
	});

	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded);
</script>

<SEO title={$t('achievements.title')} path="/achievements" description={$t('seo.achievements')} />

<div class="max-w-6xl mx-auto p-4 pb-24 animate-fade-in">
	<div class="flex items-center gap-3 mb-8">
		<div
			class="p-3 rounded-2xl bg-yellow-50 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400 shadow-lg shadow-yellow-100 dark:shadow-yellow-900/20 border-2 border-white dark:border-zinc-700 transform -rotate-6"
		>
			<Trophy class="w-6 h-6" />
		</div>
		<div>
			<h2 class="text-2xl font-bold text-themed relative w-fit">
				{$t('achievements.title')}
				<span
					class="absolute -bottom-1 left-0 w-full h-2 bg-yellow-200/60 dark:bg-yellow-500/30 -z-10 transform -skew-x-12 rounded-sm"
				></span>
			</h2>
			<p class="text-sm text-themed-secondary">{$t('achievements.subtitle')}</p>
		</div>
	</div>

	<!-- Grid Layout -->
	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-5">
		{#if isLoading}
			{#each Array(8) as _}
				<div
					class="relative border-2 border-transparent rounded-3xl p-5 flex items-center gap-5 bg-white dark:bg-zinc-900 shadow-sm"
				>
					<!-- Icon Box Skeleton -->
					<div
						class="w-14 h-14 rounded-2xl flex-shrink-0 bg-gray-200 dark:bg-zinc-700 animate-pulse"
					></div>

					<!-- Text Skeleton -->
					<div class="flex-1">
						<div class="h-5 w-32 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse mb-2"></div>
						<div class="h-3 w-48 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
					</div>
				</div>
			{/each}
		{:else}
			{#each [...unlocked, ...locked] as m (m.id)}
				<div
					class={`relative border-2 rounded-3xl p-5 flex items-center gap-5 transition-all duration-300 h-full ${
						m.isUnlocked
							? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-400 dark:border-yellow-500/50 shadow-sm hover:shadow-md hover:scale-[1.01]'
							: 'bg-gray-50 dark:bg-zinc-900 border-gray-200 dark:border-zinc-700 opacity-70 grayscale'
					}`}
				>
					<!-- Icon Box -->
					<div
						class={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 ${
							m.isUnlocked
								? 'bg-white dark:bg-zinc-800 shadow-sm text-yellow-600'
								: 'bg-gray-200 dark:bg-zinc-700 text-gray-400'
						}`}
					>
						{#if m.isUnlocked}
							<svelte:component this={m.icon} class="w-8 h-8 fill-current" />
						{:else}
							<Lock class="w-6 h-6" />
						{/if}
					</div>

					<div class="flex-1">
						<h3 class={`text-lg font-bold ${m.isUnlocked ? 'text-themed' : 'text-themed-muted'}`}>
							{m.title}
						</h3>
						<p class="text-xs text-themed-secondary font-medium">{m.description}</p>

						<!-- Progress Bar for Locked Items -->
						{#if !m.isUnlocked && m.progress}
							<div class="mt-2">
								<div class="text-[10px] font-bold text-gray-400 mb-1 text-right">{m.progress}</div>
								<div class="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
									<div
										class="h-full bg-gray-400 rounded-full"
										style={`width: ${
											m.progress.includes('/')
												? (parseInt(m.progress.split('/')[0]) /
														parseInt(m.progress.split('/')[1])) *
													100
												: 0
										}%`}
									></div>
								</div>
							</div>
						{/if}
					</div>

					<!-- Status Badge -->
					{#if m.isUnlocked}
						<div
							class="absolute top-4 right-4 bg-yellow-400 text-yellow-900 text-[10px] font-bold px-3 py-1 rounded-full flex items-center gap-1 shadow-sm"
						>
							{$t('achievements.unlocked')}
							<Check class="w-3 h-3" />
						</div>
					{/if}
				</div>
			{/each}
		{/if}
	</div>
</div>
