<script lang="ts">
	import { ticketsStore, showToast, isInitialDataLoaded, isTicketsLoading } from '$lib/stores';
	import { invalidateDashboard } from '$lib/stores/dashboard.svelte';
	import { invalidateTheater } from '$lib/stores/theater.svelte';
	import { invalidateMemories } from '$lib/stores/memories.svelte';
	import { setlistsStore } from '$lib/stores/theater.svelte';
	import { onMount } from 'svelte';

	import type { Ticket as TicketType, TicketFilters } from '$lib/types';
	import EditTicketModal from '$lib/components/EditTicketModal.svelte';
	import { History, Ticket, Filter as FilterIcon } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';

	import { useTranslation } from '$lib/i18n/useTranslation';

	// Shared components and utils
	import { PageHeader, EmptyState, ErrorState, NoMoreData } from '$lib/components';
	import { TableSkeleton, TicketCardSkeleton } from '$lib/components/skeletons';
	import {
		DeleteConfirmationModal,
		TicketCard,
		TicketTable,
		HistoryFilter
	} from '$lib/components/history';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { isCacheExpired } from '$lib/utils/cache';

	const { t } = useTranslation();

	// Store data via reactive properties
	let filteredTickets = $derived(ticketsStore.list);
	let pagination = $derived(ticketsStore.pagination);
	let filters = $derived(ticketsStore.filters);
	let error = $derived(ticketsStore.error);
	let hasMore = $derived(pagination.current_page < pagination.last_page);

	// Main Component Logic
	let viewMode: 'GRID' | 'TABLE' = $state('GRID');
	let deleteId: string | null = $state(null);
	let isDeleting = $state(false);

	/* Loading State */
	let mounted = $state(false);
	let isFilterOpen = $state(false);
	let filterCount = $state(0);

	onMount(() => {
		mounted = true;
		setlistsStore.loadOptions();

		// Initial load check
		if (filteredTickets.length === 0 || isCacheExpired(ticketsStore.lastUpdated)) {
			loadTickets(1);
		}
	});

	async function loadTickets(pageIdx: number, currentFilters: TicketFilters = {}) {
		// Store handles locking if needed, or we rely on UI not triggering double loads
		try {
			// Use store action
			await ticketsStore.load(pageIdx, currentFilters);
			isInitialDataLoaded.set(true);
		} catch {
			// Error logged and handled by store
			showToast(t('history.errorTitle') || 'Failed to load tickets', 'error');
		}
	}

	function handleIntersect() {
		if (!mounted || isTicketsLoading.value || !hasMore) return;
		loadTickets(pagination.current_page + 1, filters);
	}

	let searchTimeout: ReturnType<typeof setTimeout>;

	function handleFilterChange(newFilters: TicketFilters) {
		if (!mounted) return;
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			loadTickets(1, newFilters);
		}, 500);
	}

	// Actions
	// Logic for note update
	const handleToggleFavorite = async (ticketId: string) => {
		try {
			await ticketsStore.toggleFavorite(ticketId);
		} catch {
			showToast(t('common.error'), 'error');
		}
	};

	const handleNoteUpdate = async (ticketId: string, note: string) => {
		try {
			// Use store action (handles API + optimistic update)
			await ticketsStore.updateNote(ticketId, note);
			showToast(t('history.notesSaved'), 'success');
		} catch {
			// Error logged by store
			showToast(t('common.error'), 'error');
		}
	};

	const openDeleteModal = (id: string) => {
		deleteId = id;
	};

	const confirmDelete = async () => {
		if (!deleteId) return;
		isDeleting = true;
		try {
			// Use store action (handles API call internally)
			await ticketsStore.deleteTicket(deleteId);

			// Invalidate dashboard/theater cache
			invalidateDashboard();
			invalidateTheater();
			invalidateMemories();

			deleteId = null;
			showToast(t('history.ticketDeleted'), 'success');
		} catch {
			// Error logged by store
			showToast(t('common.error'), 'error');
		} finally {
			isDeleting = false;
		}
	};

	let editingTicket: TicketType | null = $state(null);

	const handleTicketUpdate = () => {
		// API call, store sync, and cache invalidation are already handled inside EditTicketModal
		editingTicket = null;
	};
</script>

<SEO title={t('history.title')} path="/history" description={t('history.description')} />

<DeleteConfirmationModal
	show={!!deleteId}
	{isDeleting}
	onCancel={() => (deleteId = null)}
	onConfirm={confirmDelete}
/>

<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 pb-32">
	<div class="mb-0 sm:mb-8 relative z-30">
		<PageHeader
			title={t('history.title')}
			subtitle={t('history.subtitle')}
			icon={History}
			theme="red"
			actionItems={[
				{
					icon: FilterIcon,
					label: t('common.filters') || 'Filter',
					onClick: () => (isFilterOpen = !isFilterOpen),
					theme: isFilterOpen || filterCount > 0 ? 'red' : 'gray',
					badge: filterCount > 0 ? filterCount : undefined
				}
			]}
		>
			{#snippet actions()}
				<div class="flex items-center gap-3 w-full md:w-auto">
					<HistoryFilter
						{filters}
						onfilterChange={(newFilters) => handleFilterChange(newFilters)}
						bind:viewMode
						bind:showFilters={isFilterOpen}
						bind:activeFilterCount={filterCount}
						hideViewToggleOnMobile={true}
					/>
				</div>
			{/snippet}
		</PageHeader>

		<!-- Mobile filter card (since actions snippet is hidden on mobile) -->
		{#if isFilterOpen}
			<div class="block sm:hidden">
				<HistoryFilter
					{filters}
					onfilterChange={(newFilters) => handleFilterChange(newFilters)}
					bind:viewMode
					bind:showFilters={isFilterOpen}
					bind:activeFilterCount={filterCount}
					cardOnly={true}
				/>
			</div>
		{/if}
	</div>

	<!-- Content Area -->
	{#if error && filteredTickets.length === 0}
		<ErrorState
			title={t('history.errorTitle') || 'Failed to load tickets'}
			description={t('history.errorDesc') || error || ''}
			onRetry={() => loadTickets(1, filters)}
		/>
	{:else if isTicketsLoading.value && filteredTickets.length === 0}
		{#if viewMode === 'GRID'}
			<TicketCardSkeleton count={6} />
		{:else}
			<TableSkeleton
				rows={5}
				columns={[
					t('history.date'),
					t('history.eventDetails'),
					t('history.seat'),
					t('history.notes'),
					t('history.actions')
				]}
			/>
		{/if}
	{:else if filteredTickets.length === 0}
		<EmptyState icon={Ticket} title={t('history.noTickets')} description={t('history.addFirst')} />
	{:else}
		{#if viewMode === 'GRID'}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
				<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
				{#each filteredTickets as ticket (ticket._id)}
					<TicketCard
						{ticket}
						onfavoriteToggle={handleToggleFavorite}
						onupdateNote={handleNoteUpdate}
						oneditTicket={(t_val) => (editingTicket = t_val)}
						ondeleteTicket={(id) => openDeleteModal(id)}
					/>
				{/each}
			</div>
		{:else}
			<!-- Table View -->
			<TicketTable
				tickets={filteredTickets}
				onfavoriteToggle={handleToggleFavorite}
				onupdateNote={handleNoteUpdate}
				oneditTicket={(t_val) => (editingTicket = t_val)}
				ondeleteTicket={(id) => openDeleteModal(id)}
			/>
		{/if}

		<!-- Sentinel for infinite scroll -->
		{#if hasMore}
			<div use:infiniteScroll onintersect={handleIntersect} class="w-full py-6 flex justify-center">
				{#if isTicketsLoading.value}
					{#if viewMode === 'GRID'}
						<div class="w-full">
							<TicketCardSkeleton count={3} />
						</div>
					{:else}
						<div class="w-full">
							<TableSkeleton
								rows={3}
								showHeader={false}
								columns={[
									t('history.date'),
									t('history.eventDetails'),
									t('history.seat'),
									t('history.notes'),
									t('history.actions')
								]}
							/>
						</div>
					{/if}
				{/if}
			</div>
		{:else if filteredTickets.length > 0}
			<NoMoreData theme="blue" />
		{/if}
	{/if}
</div>

<!-- Edit Modal -->
{#if editingTicket}
	<EditTicketModal
		ticket={editingTicket}
		onclose={() => (editingTicket = null)}
		onsave={handleTicketUpdate}
	/>
{/if}
