<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { Calendar } from 'lucide-svelte';
	import { EmptyState } from '$lib/components';
	import { scale } from 'svelte/transition';

	import { EventCardSkeleton } from '$lib/components/skeletons';
	import { eventsStore, upcomingEvents, upcomingLoading } from '$lib/stores/events';

	const { t } = useTranslation();

	onMount(async () => {
		await eventsStore.loadUpcoming();
	});
</script>

<SEO
	title={$t('theater.upcomingEvents.title')}
	path="/theater/events"
	description={$t('theater.upcomingEvents.subtitle')}
/>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1
				class="text-3xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent"
			>
				{$t('theater.upcomingEvents.title')}
			</h1>
			<p class="text-themed-secondary mt-1">
				{$t('theater.upcomingEvents.subtitle')}
			</p>
		</div>
	</div>

	{#if $upcomingLoading}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each Array(6) as _}
				<EventCardSkeleton />
			{/each}
		</div>
	{:else if $upcomingEvents.length === 0}
		<EmptyState
			icon={Calendar}
			title={$t('theater.upcomingEvents.emptyTitle')}
			description={$t('theater.upcomingEvents.empty')}
		/>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each $upcomingEvents as event (event.id)}
				<a
					href={`https://jkt48.com${event.url}`}
					target="_blank"
					class="group relative aspect-video bg-gray-100 dark:bg-zinc-800 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 block"
					in:scale={{ duration: 300, start: 0.95 }}
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
						<div class="text-xs text-gray-300 flex items-center gap-2">
							<span>{new Date(event.date).toLocaleDateString()}</span>
							<span>•</span>
							<span
								>{new Date(event.date).toLocaleTimeString([], {
									hour: '2-digit',
									minute: '2-digit'
								})}</span
							>
							{#if event.totalMembers > 0}
								<span>•</span>
								<span>{event.totalMembers} Members</span>
							{/if}
						</div>
					</div>
				</a>
			{/each}
		</div>
	{/if}
</div>
