<script lang="ts">
	import { goto } from '$app/navigation';
	import { showToast } from '$lib/stores';
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { EmptyState, ErrorState } from '$lib/components';
	import { Calendar } from 'lucide-svelte';
	import SetlistSection from '$lib/components/theater/SetlistSection.svelte';

	import { setlistsStore, maxAttendanceStore, isSetlistsLoading } from '$lib/stores/theater';

	const { t } = useTranslation();

	// State from store
	let setlists = $derived($setlistsStore.data || []);
	let error = $derived($setlistsStore.error);
	let maxAttendance = $derived($maxAttendanceStore);

	// Group setlists by type
	let setlistItems = $derived(setlists.filter((s) => s.type === 'setlist'));
	let eventItems = $derived(setlists.filter((s) => s.type === 'event'));

	// Sub-group by active status
	let activeSetlists = $derived(setlistItems.filter((s) => s.active));
	let inactiveSetlists = $derived(setlistItems.filter((s) => !s.active));
	let activeEvents = $derived(eventItems.filter((s) => s.active));
	let inactiveEvents = $derived(eventItems.filter((s) => !s.active));

	async function fetchSetlists() {
		try {
			await setlistsStore.load();
		} catch {
			// Error is handled by store
			showToast($t('theater.setlists.listErrorTitle') || 'Failed to load setlists', 'error');
		}
	}

	onMount(() => {
		fetchSetlists();
	});

	// Navigate to detail page
	function goToDetail(setlistId: string) {
		goto(`/theater/${setlistId}`);
	}
</script>

<SEO title={$t('theater.title')} path="/theater" description={$t('seo.shows')} />

{#if $isSetlistsLoading}
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
		<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
		{#each Array(6) as _}
			<div
				class="relative flex flex-row sm:block h-[8.5rem] sm:h-auto sm:aspect-[2/3] bg-white dark:bg-zinc-900 shadow-sm rounded-[20px] sm:rounded-2xl overflow-hidden border border-gray-100 dark:border-zinc-800 animate-pulse"
			>
				<!-- Image Skeleton -->
				<div class="w-[38%] sm:w-full sm:h-full bg-gray-100 dark:bg-zinc-800 shrink-0"></div>

				<!-- Content Area -->
				<div
					class="relative flex-1 p-3.5 sm:p-5 flex flex-col justify-between sm:justify-end sm:absolute sm:inset-0"
				>
					<div class="flex flex-col gap-3">
						<div class="h-6 w-3/4 bg-gray-200 dark:bg-zinc-700 rounded mb-1"></div>
					</div>
					<div class="flex flex-col gap-3 sm:gap-4">
						<div class="flex justify-between items-end">
							<div class="h-6 w-20 bg-gray-200 dark:bg-zinc-700 rounded-md"></div>
						</div>
						<div class="w-full bg-gray-200 dark:bg-zinc-700 rounded-full h-1 sm:h-1.5"></div>
					</div>
				</div>
			</div>
		{/each}
	</div>
{:else if error}
	<ErrorState
		title={$t('theater.setlists.listErrorTitle')}
		description={error || $t('theater.setlists.listErrorDesc')}
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
				<div class="h-8 w-1.5 bg-red-500 rounded-full"></div>
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
					onclick={goToDetail}
				/>
			{/if}

			<!-- Inactive Setlists -->
			{#if inactiveSetlists.length > 0}
				<SetlistSection
					title={$t('theater.setlists.inactive')}
					items={inactiveSetlists}
					{maxAttendance}
					onclick={goToDetail}
				/>
			{/if}
		</div>
	{/if}

	<!-- Events -->
	{#if eventItems.length > 0}
		<div>
			<div class="flex items-center gap-3 mb-6">
				<div class="h-8 w-1.5 bg-purple-500 rounded-full"></div>
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
					onclick={goToDetail}
				/>
			{/if}

			<!-- Inactive Events -->
			{#if inactiveEvents.length > 0}
				<SetlistSection
					title={$t('theater.setlists.inactiveEvents')}
					items={inactiveEvents}
					{maxAttendance}
					onclick={goToDetail}
				/>
			{/if}
		</div>
	{/if}
{/if}
