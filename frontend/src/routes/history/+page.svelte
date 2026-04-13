<script lang="ts">
	import { ticketsStore, showToast, isInitialDataLoaded, isTicketsLoading } from '$lib/stores';
	import { invalidateDashboard } from '$lib/stores/dashboard';
	import { invalidateTheater } from '$lib/stores/theater';
	import { onMount } from 'svelte';

	import type { Ticket as TicketType, TicketFilters } from '$lib/types';
	import EditTicketModal from '$lib/components/EditTicketModal.svelte';
	import { History, Ticket } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';

	import { useTranslation } from '$lib/i18n/useTranslation';

	// Shared components and utils
	import { PageHeader, EmptyState, ErrorState } from '$lib/components';
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

	// Store data via derived runes
	let ticketsState = $derived($ticketsStore);
	let filteredTickets = $derived(ticketsState.list);
	let pagination = $derived(ticketsState.pagination);
	let filters = $derived(ticketsState.filters);
	let error = $derived(ticketsState.error);
	let hasMore = $derived(pagination.current_page < pagination.last_page);

	// Main Component Logic
	let viewMode: 'GRID' | 'TABLE' = $state('GRID');
	let deleteId: string | null = $state(null);
	let isDeleting = $state(false);

	/* Loading State */
	let mounted = $state(false);

	onMount(() => {
		mounted = true;

		// Initial load check
		if (filteredTickets.length === 0 || isCacheExpired($ticketsStore.lastUpdated)) {
			loadTickets(1);
		}
	});

	async function loadTickets(page: number, currentFilters: TicketFilters = {}) {
		// Store handles locking if needed, or we rely on UI not triggering double loads
		try {
			// Use store action
			await ticketsStore.load(page, currentFilters);
			isInitialDataLoaded.set(true);
		} catch {
			// Error logged and handled by store
			showToast($t('history.errorTitle') || 'Failed to load tickets', 'error');
		}
	}

	function handleIntersect() {
		if (!mounted || $isTicketsLoading || !hasMore) return;
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
	const handleNoteUpdate = async (ticketId: string, note: string) => {
		try {
			// Use store action (handles API + optimistic update)
			await ticketsStore.updateNote(ticketId, note);
			showToast($t('history.notesSaved'), 'success');
		} catch {
			// Error logged by store
			showToast($t('common.error'), 'error');
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

			deleteId = null;
			showToast($t('history.ticketDeleted'), 'success');
		} catch {
			// Error logged by store
			showToast($t('common.error'), 'error');
		} finally {
			isDeleting = false;
		}
	};

	let editingTicket: TicketType | null = $state(null);

	const handleTicketUpdate = (updated: TicketType) => {
		ticketsStore.update((s) => ({
			...s,
			list: s.list.map((t) => (t._id === updated._id ? updated : t)),
			defaultCache: s.defaultCache
				? {
						...s.defaultCache,
						list: s.defaultCache.list.map((t) => (t._id === updated._id ? updated : t))
					}
				: null
		}));

		// Invalidate dashboard cache
		invalidateDashboard();

		editingTicket = null;
	};
</script>

<SEO title={$t('history.title')} path="/history" description={$t('history.description')} />

<DeleteConfirmationModal
	show={!!deleteId}
	{isDeleting}
	onCancel={() => (deleteId = null)}
	onConfirm={confirmDelete}
/>

<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 animate-fade-in pb-32">
	<!-- Page Header -->
	<div class="mb-8">
		<PageHeader
			title={$t('history.title')}
			subtitle={$t('history.subtitle')}
			icon={History}
			theme="blue"
		>
			{#snippet actions()}
				<div class="flex items-center gap-3">
					<HistoryFilter
						{filters}
						onfilterChange={(newFilters) => handleFilterChange(newFilters)}
						bind:viewMode
					/>
				</div>
			{/snippet}
		</PageHeader>
	</div>

	<!-- Content Area -->
	<!-- Content Area -->
	{#if error && filteredTickets.length === 0}
		<ErrorState
			title={$t('history.errorTitle') || 'Failed to load tickets'}
			description={$t('history.errorDesc') || error || ''}
			onRetry={() => loadTickets(1, filters)}
		/>
	{:else if $isTicketsLoading && filteredTickets.length === 0}
		{#if viewMode === 'GRID'}
			<TicketCardSkeleton count={6} />
		{:else}
			<TableSkeleton
				rows={5}
				columns={[
					$t('history.date'),
					$t('history.eventDetails'),
					$t('history.seat'),
					$t('history.price'),
					$t('history.notes'),
					$t('history.actions')
				]}
			/>
		{/if}
	{:else if filteredTickets.length === 0}
		<EmptyState
			icon={Ticket}
			title={$t('history.noTickets')}
			description={$t('history.addFirst')}
		/>
	{:else}
		{#if viewMode === 'GRID'}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
				<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
				{#each filteredTickets as ticket (ticket._id)}
					<TicketCard
						{ticket}
						onupdateNote={handleNoteUpdate}
						oneditTicket={(t) => (editingTicket = t)}
						ondeleteTicket={(id) => openDeleteModal(id)}
					/>
				{/each}
			</div>
		{:else}
			<!-- Table View -->
			<TicketTable
				tickets={filteredTickets}
				onupdateNote={handleNoteUpdate}
				oneditTicket={(t) => (editingTicket = t)}
				ondeleteTicket={(id) => openDeleteModal(id)}
			/>
		{/if}

		<!-- Sentinel for infinite scroll -->
		{#if hasMore}
			<div use:infiniteScroll onintersect={handleIntersect} class="w-full py-6 flex justify-center">
				{#if $isTicketsLoading}
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
									$t('history.date'),
									$t('history.eventDetails'),
									$t('history.seat'),
									$t('history.price'),
									$t('history.notes'),
									$t('history.actions')
								]}
							/>
						</div>
					{/if}
				{/if}
			</div>
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
