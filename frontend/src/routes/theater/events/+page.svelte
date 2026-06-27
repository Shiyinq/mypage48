<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { Calendar, Clock, Users, Cake, GraduationCap } from 'lucide-svelte';
	import { EmptyState, ErrorState } from '$lib/components';
	import { scale } from 'svelte/transition';

	import { HorizontalEventCardSkeleton } from '$lib/components/skeletons';
	import {
		eventsStore,
		upcomingEvents,
		isUpcomingEventsLoading,
		upcomingError
	} from '$lib/stores/events.svelte';
	import { membersStore, isBirthdaysLoading } from '$lib/stores/theater.svelte';
	import Birthdays from '$lib/components/theater/Birthdays.svelte';
	import { OptimizedImage } from '$lib/components/common';

	import { formatDate, formatTime } from '$lib/i18n';
	const { t } = useTranslation();

	function isToday(dateStr: string): boolean {
		const eventDate = new Date(dateStr);
		const today = new Date();
		return (
			eventDate.getDate() === today.getDate() &&
			eventDate.getMonth() === today.getMonth() &&
			eventDate.getFullYear() === today.getFullYear()
		);
	}

	let mounted = $state(false);

	onMount(async () => {
		await eventsStore.loadUpcoming();
		await membersStore.loadBirthdays();
		mounted = true;
	});

	let eventsList = $derived(upcomingEvents.value);
	let error = $derived(upcomingError.value);
</script>

<SEO
	title={t('theater.events.title')}
	path="/theater/events"
	description={t('theater.events.subtitle')}
/>

<div class="space-y-6">
	<div class="flex items-center gap-3 mb-4">
		<div class="h-8 w-1.5 bg-red-500 rounded-full"></div>
		<h2 class="text-xl font-bold text-gray-800 dark:text-gray-100">
			{t('theater.upcomingEvents.title') || 'Upcoming Shows'}
		</h2>
	</div>

	{#if !mounted || $isUpcomingEventsLoading}
		<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 lg:gap-5">
			{#each Array(6)}
				<HorizontalEventCardSkeleton />
			{/each}
		</div>
	{:else if error}
		<ErrorState
			title={t('theater.upcomingEvents.errorTitle') || 'Failed to load events'}
			description={t('theater.upcomingEvents.errorDesc') || error || ''}
			onRetry={() => eventsStore.loadUpcoming(true)}
		/>
	{:else if eventsList.length === 0}
		<EmptyState
			icon={Calendar}
			title={t('theater.upcomingEvents.emptyTitle')}
			description={t('theater.upcomingEvents.empty')}
		/>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 lg:gap-5">
			{#each eventsList as event (event.id)}
				<a
					href={`/theater/events/${event.id}`}
					class="group relative flex flex-row h-32 sm:h-36 lg:h-40 bg-white dark:bg-zinc-900 shadow-sm hover:shadow-xl rounded-[20px] sm:rounded-2xl transition-all duration-300 overflow-hidden border border-gray-100 dark:border-white/5 {isToday(
						event.date
					)
						? 'ring-2 ring-red-500/50'
						: ''}"
					in:scale={{ duration: 300, start: 0.95 }}
				>
					{#if isToday(event.date)}
						<!-- Premium Pulse Glow Overlay -->
						<div
							class="absolute inset-0 z-0 rounded-[20px] sm:rounded-2xl ring-4 ring-red-500/40 animate-pulse pointer-events-none shadow-[0_0_20px_rgba(239,68,68,0.3)]"
						></div>
					{/if}

					<!-- Image / Placeholder (Left side) -->
					<div
						class="relative w-1/3 sm:w-2/5 shrink-0 overflow-hidden bg-gray-50 dark:bg-zinc-800 z-10"
					>
						{#if event.imageUrl}
							<OptimizedImage
								src={event.imageUrl}
								srcMedium={event.imageUrl_medium}
								srcSmall={event.imageUrl_small}
								blurHash={event.blurHash}
								alt={event.title}
								sizes="(max-width: 640px) 40vw, (max-width: 1024px) 30vw, 20vw"
								class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
							/>
							<div
								class="absolute inset-0 bg-gradient-to-r from-black/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity"
							></div>
						{:else}
							<div
								class="absolute inset-0 bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center"
							>
								<Calendar class="w-8 h-8 text-white/50" />
							</div>
						{/if}

						<!-- Today Badge -->
						{#if isToday(event.date)}
							<div class="absolute bottom-2 left-2 z-20">
								<span
									class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-bold text-white bg-red-500 shadow-lg shadow-red-500/30 backdrop-blur-sm today-badge"
								>
									{t('theater.events.today')}
								</span>
							</div>
						{/if}
					</div>

					<!-- Details (Right side) -->
					<div class="relative flex-1 p-3 sm:p-4 flex flex-col z-10 min-w-0">
						<!-- Top Metadata Row -->
						<div class="flex flex-wrap items-center gap-2 mb-1.5 sm:mb-2">
							{#if event.label}
								<div
									class="px-2 py-0.5 text-[10px] font-bold rounded-md uppercase tracking-wider border shadow-sm {event.label ===
										'JKT48' ||
									event.label === 'GENERAL' ||
									event.label === 'EXCLUSIVE'
										? 'bg-red-50 dark:bg-red-900/20 text-red-500 dark:text-red-400 border-red-100 dark:border-red-800/30'
										: event.label === 'LOVE'
											? 'bg-pink-50 dark:bg-pink-900/20 text-pink-500 dark:text-pink-400 border-pink-100 dark:border-pink-800/30'
											: event.label === 'DREAM'
												? 'bg-cyan-50 dark:bg-cyan-900/20 text-cyan-500 dark:text-cyan-400 border-cyan-100 dark:border-cyan-800/30'
												: event.label === 'PASSION'
													? 'bg-orange-50 dark:bg-orange-900/20 text-orange-500 dark:text-orange-400 border-orange-100 dark:border-orange-800/30'
													: 'bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-gray-400 border-gray-200/50 dark:border-white/5'}"
								>
									{event.label}
								</div>
							{/if}
							{#if event.type && event.type !== event.label}
								<div
									class="px-2 py-0.5 text-[10px] font-bold rounded-md uppercase tracking-wider shadow-sm border border-transparent {event.type ===
									'EVENT'
										? 'bg-rose-100 dark:bg-rose-900/30 text-rose-600 dark:text-rose-400 border-rose-200/30 dark:border-rose-800/20'
										: event.type === 'SHOW'
											? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border-blue-200/30 dark:border-blue-800/20'
											: event.type === 'GENERAL' || event.type === 'EXCLUSIVE'
												? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 border-red-200/30 dark:border-red-800/20'
												: event.type === 'BIRTHDAY'
													? 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400 border-yellow-200/30 dark:border-yellow-800/20'
													: 'bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-gray-400 border-gray-200/50 dark:border-white/5'}"
								>
									{event.type}
								</div>
							{/if}
						</div>

						<!-- Text Content -->
						<h3
							class="font-bold text-sm sm:text-base leading-snug mb-1 group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors line-clamp-2 text-gray-900 dark:text-gray-100"
							title={event.title}
						>
							{event.title}
						</h3>

						{#if (event.seitansaiMembers?.length ?? 0) > 0}
							<div
								class="flex items-center gap-1.5 text-[11px] sm:text-xs text-pink-500 font-medium mb-1 w-fit"
							>
								<Cake class="w-3.5 h-3.5 text-pink-500" />
								<span class="line-clamp-1">{event.seitansaiMembers?.join(', ')}</span>
							</div>
						{/if}

						{#if (event.graduationMembers?.length ?? 0) > 0}
							<div
								class="flex items-center gap-1.5 text-[11px] sm:text-xs text-indigo-500 font-medium mb-1 w-fit"
							>
								<GraduationCap class="w-3.5 h-3.5 text-indigo-500" />
								<span class="line-clamp-1">{event.graduationMembers?.join(', ')}</span>
							</div>
						{/if}

						<!-- Metadata Grid -->
						<div class="flex flex-col gap-0.5 sm:gap-1 mt-auto">
							<!-- Date & Time -->
							<div
								class="flex items-center flex-wrap gap-x-2 gap-y-0.5 text-[10px] sm:text-[11px] font-medium text-gray-500 dark:text-gray-400"
							>
								<div class="flex items-center gap-1">
									<Calendar class="w-3 h-3 text-gray-400" />
									<span>
										{formatDate(event.date, {
											weekday: 'short',
											day: 'numeric',
											month: 'short',
											year: 'numeric'
										})}
									</span>
								</div>

								{#if event.setlistId}
									<div
										class="flex items-center gap-1 border-l border-gray-200 dark:border-zinc-700 pl-2"
									>
										<Clock class="w-3 h-3 text-gray-400" />
										<span>{formatTime(event.date, { hour: '2-digit', minute: '2-digit' })}</span>
									</div>
								{/if}
							</div>

							<!-- Members -->
							{#if event.totalMembers > 1}
								<div
									class="flex items-center gap-1 text-[10px] sm:text-[11px] font-medium text-gray-500 dark:text-gray-400"
								>
									<Users class="w-3 h-3 text-gray-400" />
									<span>{event.totalMembers} {t('theater.events.members')}</span>
								</div>
							{/if}
						</div>
					</div>
				</a>
			{/each}
		</div>
	{/if}

	<!-- Birthdays Section -->
	<Birthdays
		birthdays={$membersStore.birthdays || []}
		isLoading={!mounted || $isBirthdaysLoading}
	/>
</div>

<style>
	.today-badge {
		animation: pulse-badge 1.5s ease-in-out infinite;
	}

	@keyframes pulse-badge {
		0%,
		100% {
			transform: scale(1);
			box-shadow: 0 4px 15px rgba(252, 165, 165, 0.4);
		}
		50% {
			transform: scale(1.1);
			box-shadow: 0 4px 25px rgba(252, 165, 165, 0.8);
		}
	}
</style>
