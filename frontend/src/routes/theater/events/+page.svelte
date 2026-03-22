<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { Calendar, Clock, Users, Cake } from 'lucide-svelte';
	import { EmptyState, ErrorState } from '$lib/components';
	import { scale } from 'svelte/transition';

	import { EventCardSkeleton } from '$lib/components/skeletons';
	import {
		eventsStore,
		upcomingEvents,
		isUpcomingEventsLoading,
		upcomingError
	} from '$lib/stores/events';
	import { membersStore, isBirthdaysLoading } from '$lib/stores/theater';
	import Birthdays from '$lib/components/theater/Birthdays.svelte';

	import { formatDate, formatTime } from '$lib/i18n';
	const { t, locale } = useTranslation();

	function isToday(dateStr: string): boolean {
		const eventDate = new Date(dateStr);
		const today = new Date();
		return (
			eventDate.getDate() === today.getDate() &&
			eventDate.getMonth() === today.getMonth() &&
			eventDate.getFullYear() === today.getFullYear()
		);
	}

	onMount(async () => {
		await eventsStore.loadUpcoming();
		await membersStore.loadBirthdays();
	});

	$: error = $upcomingError;
</script>

<SEO
	title={$t('theater.events.title')}
	path="/theater/events"
	description={$t('theater.events.subtitle')}
/>

<div class="space-y-6">
	<!-- Birthdays Section -->
	<Birthdays birthdays={$membersStore.birthdays || []} isLoading={$isBirthdaysLoading} />

	<div class="flex items-center gap-2 mb-4">
		<Calendar class="w-5 h-5 text-red-500" />
		<h2 class="text-xl font-bold text-gray-800 dark:text-gray-100">
			{$t('theater.upcomingEvents.title') || 'Upcoming Shows'}
		</h2>
	</div>

	{#if $isUpcomingEventsLoading}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
			{#each Array(6) as _}
				<EventCardSkeleton />
			{/each}
		</div>
	{:else if error}
		<ErrorState
			title={$t('theater.upcomingEvents.errorTitle') || 'Failed to load events'}
			description={$t('theater.upcomingEvents.errorDesc') || error || ''}
			onRetry={() => eventsStore.loadUpcoming(true)}
		/>
	{:else if $upcomingEvents.length === 0}
		<EmptyState
			icon={Calendar}
			title={$t('theater.upcomingEvents.emptyTitle')}
			description={$t('theater.upcomingEvents.empty')}
		/>
	{:else}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
			{#each $upcomingEvents as event (event.id)}
				<a
					href={`https://jkt48.com${event.url}`}
					target="_blank"
					class="group relative block transition-all duration-300 flex flex-row sm:block h-[8.5rem] sm:h-auto sm:aspect-[2/3] shadow-sm hover:shadow-xl rounded-[20px] sm:rounded-2xl {isToday(
						event.date
					)
						? 'overflow-visible'
						: 'overflow-hidden border border-gray-100 dark:border-white/5 sm:border-0'}"
					in:scale={{ duration: 300, start: 0.95 }}
				>
					{#if isToday(event.date)}
						<!-- Premium Pulse Glow Overlay -->
						<div
							class="absolute inset-0 z-0 rounded-[20px] sm:rounded-2xl ring-4 ring-red-500/40 animate-pulse pointer-events-none shadow-[0_0_20px_rgba(239,68,68,0.3)]"
						></div>
					{/if}

					<!-- Content Container -->
					<div
						class="relative z-10 flex flex-row sm:block w-full h-full overflow-hidden rounded-[20px] sm:rounded-2xl {isToday(
							event.date
						)
							? 'bg-white dark:bg-zinc-900'
							: 'bg-white dark:bg-zinc-900/50 sm:bg-gray-100 sm:dark:bg-zinc-800'}"
					>
						<!-- Image / Placeholder -->
						<div class="relative w-[38%] sm:w-full sm:h-full shrink-0 overflow-hidden">
							{#if event.imageUrl}
								<img
									src={event.imageUrl}
									alt={event.title}
									class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
								/>
								<!-- Mobile Gradient: Right to Left -->
								<div
									class="absolute inset-0 sm:hidden bg-gradient-to-r from-black/10 via-transparent to-black/5"
								></div>
								<!-- Desktop Gradient: Bottom to Top (Original) -->
								<div
									class="absolute inset-0 hidden sm:block bg-gradient-to-t from-black/90 via-black/50 to-transparent"
								></div>
							{:else}
								<div
									class="absolute inset-0 bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center"
								>
									<Calendar class="w-8 h-8 sm:w-12 sm:h-12 text-white/50" />
								</div>
								<div
									class="absolute inset-0 hidden sm:block bg-gradient-to-t from-black/80 via-transparent to-transparent"
								></div>
							{/if}

							<!-- Date Badge (Mobile) -->
							<div
								class="absolute top-2 left-2 sm:hidden flex flex-col items-center bg-white/95 dark:bg-zinc-900/90 backdrop-blur-md rounded-lg p-1.5 shadow-sm min-w-[3rem]"
							>
								<span class="text-[10px] uppercase font-bold text-red-500 leading-none mb-0.5">
									{$formatDate(event.date, { month: 'short' })}
								</span>
								<span class="text-lg font-black text-gray-900 dark:text-white leading-none">
									{new Date(event.date).getDate()}
								</span>
							</div>

							<!-- Today Badge -->
							{#if isToday(event.date)}
								<div class="absolute bottom-2 left-2 sm:top-3 sm:right-3 sm:left-auto z-20">
									<span
										class="inline-flex items-center px-2 py-0.5 sm:px-3 sm:py-1 rounded-full text-[10px] sm:text-xs font-bold text-white bg-red-500 sm:bg-red-400 shadow-lg shadow-red-500/30 backdrop-blur-sm today-badge"
									>
										{$t('theater.events.today')}
									</span>
								</div>
							{/if}
						</div>

						<!-- Details -->
						<div
							class="relative flex-1 p-3.5 sm:p-5 flex flex-col justify-start sm:justify-end sm:absolute sm:inset-x-0 sm:bottom-0 sm:top-auto sm:pointer-events-none z-10"
						>
							<!-- Top Metadata Row (Mobile: Team Info) / Desktop: Team Info at bottom -->
							<div
								class="absolute top-3.5 right-3.5 sm:static sm:flex sm:items-start sm:justify-between sm:mb-1 sm:pointer-events-auto z-20"
							>
								<div class="flex items-center gap-2">
									{#if event.label}
										<div
											class="px-2 py-0.5 sm:px-3 sm:py-1 text-[10px] sm:text-xs font-bold rounded-md uppercase tracking-wider border shadow-sm {event.label ===
											'JKT48'
												? 'bg-red-50 dark:bg-red-900/20 text-red-500 dark:text-red-400 border-red-100 dark:border-red-800/30'
												: 'bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-gray-400 border-gray-200/50 dark:border-white/5'}"
										>
											{event.label}
										</div>
									{/if}
									{#if event.type}
										<div
											class="px-2 py-0.5 sm:px-3 sm:py-1 text-[10px] sm:text-xs font-bold rounded-md uppercase tracking-wider shadow-sm border border-transparent {event.type ===
											'EVENT'
												? 'bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 border-pink-200/30 dark:border-pink-800/20'
												: event.type === 'SHOW'
												? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border-blue-200/30 dark:border-blue-800/20'
												: event.type === 'GENERAL'
												? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 border-red-200/30 dark:border-red-800/20'
												: event.type === 'BIRTHDAY'
												? 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400 border-yellow-200/30 dark:border-yellow-800/20'
												: 'bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-gray-400 border-gray-200/50 dark:border-white/5'}"
										>
											{event.type}
										</div>
									{/if}
								</div>
							</div>

							<!-- Text Content -->
							<div
								class="flex flex-col h-full sm:h-auto justify-start sm:justify-end sm:pointer-events-auto sm:pl-0.5 pr-10 sm:pr-0"
							>
								<h3
									class="font-bold text-[15px] sm:text-lg leading-tight mb-1.5 sm:mb-1 group-hover:text-red-600 dark:group-hover:text-red-400 sm:group-hover:text-red-300 transition-colors line-clamp-2 sm:line-clamp-none text-gray-900 dark:text-white sm:text-white"
								>
									{event.title}
								</h3>

								{#if (event.seitansaiMembers?.length ?? 0) > 0}
									<div
										class="flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-sm text-pink-500 sm:text-pink-300 font-medium mb-1.5 sm:mb-1 w-fit"
									>
										<Cake class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-pink-500 sm:text-pink-400" />
										<span class="line-clamp-1">{event.seitansaiMembers?.join(', ')}</span>
									</div>
								{/if}

								<!-- Metadata Grid: Stacked on both Mobile and Desktop -->
								<div class="flex flex-col gap-1 sm:gap-1.5">
									<!-- Date -->
									<div
										class="flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-sm font-medium text-gray-500 dark:text-gray-400 sm:text-gray-200"
									>
										<Calendar class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" />
										<span>
											{$formatDate(event.date, {
												weekday: 'long',
												day: 'numeric',
												month: 'long',
												year: 'numeric'
											})}
										</span>
									</div>

									<!-- Time -->
									{#if event.setlistId}
										<div
											class="flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-sm font-medium text-gray-500 dark:text-gray-400 sm:text-gray-200"
										>
											<Clock class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" />
											<span
												>{$formatTime(event.date, {
													hour: '2-digit',
													minute: '2-digit'
												})}</span
											>
										</div>
									{/if}

									<!-- Members -->
									{#if event.totalMembers > 1}
										<div
											class="flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-sm font-medium text-gray-500 dark:text-gray-400 sm:text-gray-200"
										>
											<Users class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" />
											<span>{event.totalMembers} {$t('theater.events.members')}</span>
										</div>
									{/if}
								</div>
							</div>
						</div>
					</div>
				</a>
			{/each}
		</div>
	{/if}
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
