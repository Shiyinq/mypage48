<script lang="ts">
	import { goto } from '$app/navigation';
	import { showToast, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { onMount } from 'svelte';
	import { setlistsApi, type Setlist } from '$lib/apis/setlists';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { ShowCard } from '$lib/components/shows';
	import { EmptyState, ErrorState } from '$lib/components';
	import { Calendar } from 'lucide-svelte';

	import { setlistsStore, maxAttendanceStore } from '$lib/stores/theater';
	import { get } from 'svelte/store';

	const { t } = useTranslation();

	// State
	let setlists: Setlist[] = [];
	let maxAttendance = 1;
	let setlistsLoading = true;
	let mounted = false;
	let error = false;

	// Group setlists by type
	$: setlistItems = setlists.filter((s) => s.type === 'setlist');
	$: eventItems = setlists.filter((s) => s.type === 'event');

	// Sub-group by active status
	$: activeSetlists = setlistItems.filter((s) => s.active);
	$: inactiveSetlists = setlistItems.filter((s) => !s.active);
	$: activeEvents = eventItems.filter((s) => s.active);
	$: inactiveEvents = eventItems.filter((s) => !s.active);

	async function fetchSetlists() {
		// Check cache first
		const cachedSetlists = get(setlistsStore);
		const cachedMaxAttendance = get(maxAttendanceStore);

		if (cachedSetlists) {
			setlists = cachedSetlists;
			maxAttendance = cachedMaxAttendance;
			setlistsLoading = false;
			return;
		}

		try {
			setlistsLoading = true;
			error = false;
			const response = await setlistsApi.getAll();
			setlists = response.setlists;
			maxAttendance = response.maxAttendance || 1;

			// Update cache
			setlistsStore.set(setlists);
			maxAttendanceStore.set(maxAttendance);
		} catch (e) {
			console.error('Failed to fetch setlists:', e);
			error = true;
			showToast($t('theater.setlists.listErrorTitle') || 'Failed to load setlists', 'error');
		} finally {
			setlistsLoading = false;
		}
	}

	onMount(() => {
		mounted = true;
		fetchSetlists();
	});

	$: isLoading = !mounted || setlistsLoading || ($isAuthenticated && !$isInitialDataLoaded);

	// Navigate to detail page
	function goToDetail(setlistId: string) {
		goto(`/theater/${setlistId}`);
	}

	// Helper to transform setlist to show data format
	function toShowData(s: Setlist) {
		return {
			title: s.title,
			image: s.imageUrl,
			count: s.watched.count,
			percentage: s.watched.percentage,
			isMostWatched: s.watched.isMostWatched
		};
	}
</script>

<SEO title={$t('theater.title')} path="/theater" description={$t('seo.shows')} />

{#if isLoading}
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
		<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
		{#each Array(6) as _}
			<div
				class="relative overflow-hidden rounded-3xl h-64 bg-white dark:bg-zinc-900 shadow-sm border border-gray-100 dark:border-zinc-800"
			>
				<div class="absolute inset-0 bg-gray-100 dark:bg-zinc-800 animate-pulse"></div>
				<div class="absolute bottom-0 left-0 right-0 p-6 flex flex-col gap-3">
					<div class="h-8 w-3/4 bg-gray-200 dark:bg-zinc-700 rounded mb-1 animate-pulse"></div>
					<div class="flex justify-between items-end">
						<div class="h-6 w-16 bg-gray-200 dark:bg-zinc-700 rounded-full animate-pulse"></div>
					</div>
					<div class="w-full bg-gray-200 dark:bg-zinc-700 rounded-full h-1.5 animate-pulse"></div>
				</div>
			</div>
		{/each}
	</div>
{:else if error}
	<ErrorState
		title={$t('theater.setlists.listErrorTitle')}
		description={$t('theater.setlists.listErrorDesc')}
		onRetry={fetchSetlists}
	/>
{:else if setlists.length === 0}
	<EmptyState
		icon={Calendar}
		title={$t('theater.setlists.emptyTitle')}
		description={$t('theater.setlists.emptyDesc')}
	/>
{:else}
	<!-- Setlists -->
	{#if setlistItems.length > 0}
		<div class="mb-12">
			<div class="flex items-center gap-3 mb-6">
				<div class="h-8 w-1.5 bg-gradient-to-b from-red-500 to-pink-600 rounded-full"></div>
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white">
					{$t('theater.setlists.section')}
				</h2>
			</div>

			<!-- Active Setlists -->
			{#if activeSetlists.length > 0}
				<div class="mb-8">
					<h3
						class="text-lg font-semibold text-gray-600 dark:text-gray-400 mb-4 flex items-center gap-2"
					>
						<div class="w-2 h-2 rounded-full bg-green-500"></div>
						{$t('theater.setlists.active')}
					</h3>
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
						{#each activeSetlists as setlist (setlist.setlistId)}
							{@const show = toShowData(setlist)}
							<ShowCard
								{show}
								count={show.count}
								{maxAttendance}
								onClick={() => goToDetail(setlist.setlistId)}
							/>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Inactive Setlists -->
			{#if inactiveSetlists.length > 0}
				<div>
					<h3 class="text-lg font-semibold text-gray-600 dark:text-gray-400 mb-4">
						{$t('theater.setlists.inactive')}
					</h3>
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
						{#each inactiveSetlists as setlist (setlist.setlistId)}
							{@const show = toShowData(setlist)}
							<ShowCard
								{show}
								count={show.count}
								{maxAttendance}
								onClick={() => goToDetail(setlist.setlistId)}
							/>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Events -->
	{#if eventItems.length > 0}
		<div>
			<div class="flex items-center gap-3 mb-6">
				<div class="h-8 w-1.5 bg-gradient-to-b from-purple-500 to-indigo-600 rounded-full"></div>
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white">
					{$t('theater.setlists.events')}
				</h2>
			</div>

			<!-- Active Events -->
			{#if activeEvents.length > 0}
				<div class="mb-8">
					<h3
						class="text-lg font-semibold text-gray-600 dark:text-gray-400 mb-4 flex items-center gap-2"
					>
						<div class="w-2 h-2 rounded-full bg-green-500"></div>
						{$t('theater.setlists.activeEvents')}
					</h3>
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
						{#each activeEvents as event (event.setlistId)}
							{@const show = toShowData(event)}
							<ShowCard
								{show}
								count={show.count}
								{maxAttendance}
								onClick={() => goToDetail(event.setlistId)}
							/>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Inactive Events -->
			{#if inactiveEvents.length > 0}
				<div>
					<h3 class="text-lg font-semibold text-gray-600 dark:text-gray-400 mb-4">
						{$t('theater.setlists.inactiveEvents')}
					</h3>
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
						{#each inactiveEvents as event (event.setlistId)}
							{@const show = toShowData(event)}
							<ShowCard
								{show}
								count={show.count}
								{maxAttendance}
								onClick={() => goToDetail(event.setlistId)}
							/>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{/if}
{/if}
