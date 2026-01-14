<script lang="ts">
	export let params: Record<string, string> | undefined = undefined;
	import { goto } from '$app/navigation';
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { EmptyState, ErrorState } from '$lib/components';
	import { Calendar } from 'lucide-svelte';
	import SetlistSection from '$lib/components/theater/SetlistSection.svelte';

	import { setlistsStore, maxAttendanceStore } from '$lib/stores/theater';

	const { t } = useTranslation();

	// State
	// Using reactive statements from store
	$: setlists = $setlistsStore || [];
	$: maxAttendance = $maxAttendanceStore;

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
		// If data is already in store, we might skip loading state or just background refresh
		// But for consistency let's just use the store load which checks cache key (though current setlistsStore is simple set)

		// Actually our new store logic simply checks if get() returns null
		if ($setlistsStore) {
			setlistsLoading = false;
			return;
		}

		try {
			setlistsLoading = true;
			error = false;
			await setlistsStore.load();
		} catch (e) {
			logger.error('Failed to fetch setlists', e, { context: 'TheaterPage' });
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

	// Navigate to detail page
	function goToDetail(setlistId: string) {
		goto(`/theater/${setlistId}`);
	}

	$: isLoading = !mounted || setlistsLoading;
</script>

<SEO title={$t('theater.title')} path="/theater" description={$t('seo.shows')} />

{#if isLoading}
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
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
				<SetlistSection
					title={$t('theater.setlists.active')}
					items={activeSetlists}
					{maxAttendance}
					isActive={true}
					on:click={(e) => goToDetail(e.detail)}
				/>
			{/if}

			<!-- Inactive Setlists -->
			{#if inactiveSetlists.length > 0}
				<SetlistSection
					title={$t('theater.setlists.inactive')}
					items={inactiveSetlists}
					{maxAttendance}
					on:click={(e) => goToDetail(e.detail)}
				/>
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
				<SetlistSection
					title={$t('theater.setlists.activeEvents')}
					items={activeEvents}
					{maxAttendance}
					isActive={true}
					on:click={(e) => goToDetail(e.detail)}
				/>
			{/if}

			<!-- Inactive Events -->
			{#if inactiveEvents.length > 0}
				<SetlistSection
					title={$t('theater.setlists.inactiveEvents')}
					items={inactiveEvents}
					{maxAttendance}
					on:click={(e) => goToDetail(e.detail)}
				/>
			{/if}
		</div>
	{/if}
{/if}
