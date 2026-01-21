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
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
			{#each $upcomingEvents as event (event.id)}
				<a
					href={`https://jkt48.com${event.url}`}
					target="_blank"
					class="group relative aspect-[2/3] rounded-2xl block {isToday(event.date)
						? 'today-event overflow-visible bg-gray-900 hover:-translate-y-1 transition-all duration-300'
						: 'bg-gray-100 dark:bg-zinc-800 overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1'}"
					in:scale={{ duration: 300, start: 0.95 }}
				>
					{#if isToday(event.date)}
						<!-- Blinking Border -->
						<div
							class="absolute inset-0 z-0 rounded-2xl border-[3px] border-blue-400 animate-border-blink"
						></div>
					{/if}

					<!-- Content Container -->
					<div
						class="overflow-hidden {isToday(event.date)
							? 'absolute inset-[3px] rounded-[13px] bg-gray-900 shadow-sm hover:shadow-md transition-all duration-300'
							: 'relative h-full w-full'}"
					>
						{#if event.imageUrl}
							<img
								src={event.imageUrl}
								alt={event.title}
								class="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
							/>
							<div
								class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent"
							></div>
						{:else}
							<div
								class="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center"
							>
								<Calendar class="w-12 h-12 text-white/50" />
							</div>
							<div
								class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"
							></div>
						{/if}

						<!-- Today Badge -->
						{#if isToday(event.date)}
							<div class="absolute top-3 right-3 z-20">
								<span
									class="today-badge inline-block px-3 py-1 rounded-full text-xs font-bold text-white bg-blue-400 shadow-lg"
								>
									{$t('theater.events.today')}
								</span>
							</div>
						{/if}

						<div class="absolute inset-x-0 bottom-0 p-5">
							<div class="flex items-start justify-between mb-1">
								{#if event.team?.img}
									<div class="w-16 h-16">
										<img
											src={`https://jkt48.com${event.team.img}`}
											alt="Team"
											class="w-full h-full object-contain object-left-bottom"
										/>
									</div>
								{:else if event.label}
									<div class="w-16 h-16">
										<img
											src={`https://jkt48.com${event.label}`}
											alt="Label"
											class="w-full h-full object-contain object-left-bottom"
										/>
									</div>
								{:else}
									<div
										class="w-16 h-16 rounded-full bg-white/10 backdrop-blur-sm p-3 border border-white/20 flex items-center justify-center"
									>
										<Calendar class="w-full h-full text-white/80" />
									</div>
								{/if}
							</div>

							<h3
								class="font-bold text-white text-lg mb-1 group-hover:text-blue-300 transition-colors"
							>
								{event.title}
							</h3>
							{#if (event.seitansaiMembers?.length ?? 0) > 0}
								<div class="flex items-center gap-2 text-sm text-pink-300 font-medium mb-1 pl-0.5">
									<Cake class="w-4 h-4 text-pink-400" />
									<span>{event.seitansaiMembers?.join(', ')}</span>
								</div>
							{/if}
							<div class="flex flex-col gap-1.5 pl-0.5">
								<div class="flex items-center gap-2 text-sm text-gray-200 font-medium">
									<Calendar class="w-4 h-4 text-gray-400" />
									<span>
										{new Date(event.date).toLocaleDateString($locale, {
											weekday: 'long',
											day: 'numeric',
											month: 'long',
											year: 'numeric'
										})}
									</span>
								</div>
								<div class="flex items-center gap-2 text-sm text-gray-200 font-medium">
									<Clock class="w-4 h-4 text-gray-400" />
									<span
										>{new Date(event.date).toLocaleTimeString([], {
											hour: '2-digit',
											minute: '2-digit'
										})}</span
									>
								</div>
								{#if event.totalMembers > 0}
									<div class="flex items-center gap-2 text-sm text-gray-200 font-medium">
										<Users class="w-4 h-4 text-gray-400" />
										<span>{event.totalMembers} {$t('theater.events.members')}</span>
									</div>
								{/if}
							</div>
						</div>
					</div>
				</a>
			{/each}
		</div>
	{/if}
</div>

<style>
	:global(.today-event) {
		box-shadow: 0 0 25px rgba(147, 197, 253, 0.6);
	}

	.animate-border-blink {
		animation: border-blink 1s ease-in-out infinite;
	}

	@keyframes border-blink {
		0%,
		100% {
			opacity: 0.5;
			box-shadow: 0 0 10px rgba(147, 197, 253, 0.4);
		}
		50% {
			opacity: 1;
			box-shadow: 0 0 20px rgba(147, 197, 253, 0.8);
		}
	}

	:global(.today-badge) {
		animation: pulse-badge 1.5s ease-in-out infinite;
	}

	@keyframes pulse-badge {
		0%,
		100% {
			transform: scale(1);
			box-shadow: 0 4px 15px rgba(147, 197, 253, 0.4);
		}
		50% {
			transform: scale(1.1);
			box-shadow: 0 4px 25px rgba(147, 197, 253, 0.8);
		}
	}
</style>
