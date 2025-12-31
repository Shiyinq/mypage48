<script lang="ts">
	import type { PageData } from './$types';
	import SEO from '$lib/components/SEO.svelte';
	import TheaterSeatMap from '$lib/components/TheaterSeatMap.svelte';
	import { User, Calendar, Ticket, Camera, DollarSign, Heart, Armchair } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let data: PageData;

	const { t } = useTranslation();
	// @ts-ignore
	const { profile } = data;

	const joinDate = new Date(profile.createdAt).toLocaleDateString(undefined, {
		month: 'long',
		year: 'numeric'
	});

	const formatCurrency = (amount: number) => {
		return new Intl.NumberFormat('id-ID', {
			style: 'currency',
			currency: 'IDR',
			maximumFractionDigits: 0
		}).format(amount);
	};

	// Prepare data for Seat Map
	let rowStats = { counts: {}, maxCount: 0, uniqueVisited: 0 };
	let seatStats = {};

	$: if (profile.stats) {
		const counts = profile.stats.rowCounts || {};
		const maxCount = Math.max(...Object.values(counts).map(Number), 0);
		const uniqueVisited = Object.keys(counts).length;

		rowStats = {
			counts,
			maxCount,
			uniqueVisited
		};
		seatStats = profile.stats.seatCounts || {};
	}
</script>

<SEO
	title={`${profile.name} (@${profile.username})`}
	description={`Check out ${profile.name}'s JKT48 theater journey!`}
/>

<div class="max-w-4xl mx-auto p-4 pb-24 animate-fade-in">
	<!-- Header -->
	<div
		class="glass-panel p-8 rounded-[2rem] mb-6 flex flex-col md:flex-row items-center gap-8 text-center md:text-left relative overflow-hidden"
	>
		<!-- Background decoration -->
		<div
			class="absolute top-0 right-0 w-64 h-64 bg-red-500/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"
		></div>

		<!-- Avatar -->
		<div class="relative">
			<div
				class="w-32 h-32 rounded-full border-4 border-white dark:border-zinc-800 shadow-xl overflow-hidden bg-gray-100 dark:bg-zinc-800"
			>
				{#if profile.profilePicture}
					<img src={profile.profilePicture} alt={profile.name} class="w-full h-full object-cover" />
				{:else}
					<div class="w-full h-full flex items-center justify-center text-gray-400">
						<User class="w-12 h-12" />
					</div>
				{/if}
			</div>
			{#if profile.oshi}
				<div
					class="absolute -bottom-2 -right-2 bg-white dark:bg-zinc-800 rounded-full p-1.5 shadow-md border border-gray-100 dark:border-zinc-700 tooltip-container"
				>
					<div class="w-10 h-10 rounded-full overflow-hidden border-2 border-pink-400">
						<img
							src={profile.oshi.profilePicture}
							alt={profile.oshi.name}
							class="w-full h-full object-cover"
						/>
					</div>
				</div>
			{/if}
		</div>

		<!-- Info -->
		<div class="relative z-10">
			<h1 class="text-3xl font-black text-gray-900 dark:text-white leading-tight mb-2">
				{profile.name}
			</h1>
			<p class="text-purple-600 dark:text-purple-400 font-bold mb-4">@{profile.username}</p>

			<div class="flex flex-wrap justify-center md:justify-start gap-3">
				{#if profile.oshi}
					<div
						class="flex items-center gap-2 px-3 py-1.5 bg-pink-50 dark:bg-pink-900/20 rounded-full text-xs font-bold text-pink-600 dark:text-pink-400"
					>
						<Heart class="w-3.5 h-3.5 fill-current" />
						Oshi: {profile.oshi.name}
					</div>
				{/if}
				{#if profile.publicYear}
					<div
						class="flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-full text-xs font-bold text-blue-700 dark:text-blue-300"
					>
						<Ticket class="w-3.5 h-3.5" />
						{$t('profile.publicActivity.yearBadge', { year: profile.publicYear })}
					</div>
				{/if}
			</div>
		</div>
	</div>

	<!-- Stats -->
	{#if profile.stats}
		<!-- Main Content Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
			<!-- Left Column: Stats Grid -->
			<div class="lg:col-span-2 grid grid-cols-2 gap-4">
				<!-- Show Count -->
				<div
					class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
				>
					<div
						class="w-10 h-10 rounded-2xl bg-red-50 dark:bg-red-900/20 text-red-500 flex items-center justify-center mb-1"
					>
						<Ticket class="w-5 h-5" />
					</div>
					<span class="text-5xl font-black text-gray-900 dark:text-white"
						>{profile.stats.totalShows}</span
					>
					<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
						>{$t('profile.stats.totalShows')}</span
					>
				</div>

				<!-- 2-Shot Count -->
				<div
					class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
				>
					<div
						class="w-10 h-10 rounded-2xl bg-pink-50 dark:bg-pink-900/20 text-pink-500 flex items-center justify-center mb-1"
					>
						<Camera class="w-5 h-5" />
					</div>
					<span class="text-5xl font-black text-gray-900 dark:text-white"
						>{profile.stats.totalTwoShots}</span
					>
					<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
						>{$t('dashboard.twoShot.twoShotTitle')}</span
					>
				</div>

				<!-- Top Row -->
				<div
					class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
				>
					<div
						class="w-10 h-10 rounded-2xl bg-purple-50 dark:bg-purple-900/20 text-purple-500 flex items-center justify-center mb-1"
					>
						<Armchair class="w-5 h-5" />
					</div>
					<span class="text-5xl font-black text-gray-900 dark:text-white"
						>{profile.stats.topRow || '-'}</span
					>
					{#if profile.stats.topRowCount}
						<span class="text-lg font-extrabold text-gray-500 dark:text-gray-400 mt-1">
							{profile.stats.topRowCount}
							{$t('dashboard.theater.times')}
						</span>
					{/if}
					<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
						>{$t('dashboard.theater.topRow')}</span
					>
				</div>

				<!-- Top Show (Replaced Spent) -->
				<div
					class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
				>
					<div
						class="w-10 h-10 rounded-2xl bg-yellow-50 dark:bg-yellow-900/20 text-yellow-500 flex items-center justify-center mb-1"
					>
						<Heart class="w-5 h-5" />
					</div>
					<span
						class="font-black text-gray-900 dark:text-white line-clamp-2 leading-tight px-2 {(
							profile.stats.topShow || ''
						).length > 25
							? 'text-sm'
							: (profile.stats.topShow || '').length > 15
								? 'text-lg'
								: 'text-2xl sm:text-3xl'}">{profile.stats.topShow || '-'}</span
					>
					{#if profile.stats.topShowCount}
						<span class="text-lg font-extrabold text-gray-500 dark:text-gray-400 mt-2">
							{profile.stats.topShowCount}
							{$t('dashboard.theater.times')}
						</span>
					{/if}
					<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
						>{$t('dashboard.theater.topShow')}</span
					>
				</div>
			</div>

			<!-- Right Column: Recent Activity -->
			<div class="glass-panel p-6 rounded-3xl flex flex-col h-full">
				<h3 class="font-black text-xl tracking-tight text-gray-900 dark:text-white mb-6">
					{$t('profile.recentActivity.title')}
				</h3>

				<div class="flex-1 overflow-y-auto pr-2 custom-scrollbar">
					{#if profile.stats.recentActivity && profile.stats.recentActivity.length > 0}
						<div class="flex flex-col">
							{#each profile.stats.recentActivity as activity}
								<div class="flex items-stretch gap-4 group">
									<!-- Timeline Column -->
									<div class="flex-shrink-0 relative w-4 flex flex-col items-center">
										<!-- Line -->
										<div
											class="absolute top-2 bottom-0 w-0.5 bg-gray-300 dark:bg-zinc-700 -z-10 group-last:hidden"
										></div>

										<!-- Dot -->
										<div class="mt-1.5 relative z-10 bg-white dark:bg-gray-900 rounded-full">
											{#if activity.type === '2-Shot'}
												<div
													class="w-2.5 h-2.5 rounded-full bg-pink-500 ring-4 ring-pink-50 dark:ring-pink-900/20"
												></div>
											{:else}
												<div
													class="w-2.5 h-2.5 rounded-full bg-red-600 ring-4 ring-red-50 dark:ring-red-900/20"
												></div>
											{/if}
										</div>
									</div>

									<!-- Content Column -->
									<div
										class="flex-1 min-w-0 pb-6 border-b border-gray-100 dark:border-zinc-800/50 group-last:border-0 group-last:pb-0"
									>
										<p class="text-sm font-bold text-gray-900 dark:text-white line-clamp-1">
											{activity.title}
										</p>
										<p class="text-xs text-gray-400 font-medium mt-0.5">
											{new Date(activity.date).toLocaleDateString(undefined, {
												day: 'numeric',
												month: 'short',
												year: 'numeric'
											})}
										</p>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div
							class="h-full flex flex-col items-center justify-center text-center text-gray-400 py-8"
						>
							<Calendar class="w-8 h-8 mb-2 opacity-50" />
							<p class="text-xs">{$t('profile.recentActivity.noActivity')}</p>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Theater Map -->
		<TheaterSeatMap {rowStats} {seatStats} showSubtitle={false} />
	{/if}

	<!-- Call to Action (if not logged in) or other info -->
	<div class="text-center mt-12 mb-8 opacity-70">
		<p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
			Powered by MyPage48
		</p>
		<a href="/" class="text-xs font-bold text-purple-600 hover:text-purple-500 underline"
			>Get your own theater tracker</a
		>
	</div>
</div>
