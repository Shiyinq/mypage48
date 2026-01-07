<script lang="ts">
	export let params: Record<string, string> | undefined = undefined;
	import { ticketsStore, showToast, isInitialDataLoaded } from '$lib/stores';
	import { invalidateDashboard } from '$lib/stores/dashboard';
	import { invalidateTheater } from '$lib/stores/theater';
	import { logger } from '$lib/utils/logger';
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

	// Store subscriptions
	$: state = $ticketsStore;
	$: filteredTickets = state.list;
	$: pagination = state.pagination;
	$: filters = state.filters;

	// Main Component Logic
	let viewMode: 'GRID' | 'TABLE' = 'GRID';
	let deleteId: string | null = null;
	let isDeleting = false;
	let error = false;

	/* Loading State */
	let mounted = false;
	let isLoadingMore = false;
	let isLoading = false;

	onMount(() => {
		mounted = true;

		// Initial load check
		if (filteredTickets.length === 0 || isCacheExpired($ticketsStore.lastUpdated)) {
			loadTickets(1);
		}
	});

	async function loadTickets(page: number, currentFilters: TicketFilters = {}) {
		if (isLoadingMore) return;

		if (page === 1) isLoading = true;
		else isLoadingMore = true;

		try {
			error = false;
			// Use store action
			await ticketsStore.load(page, currentFilters);

			isInitialDataLoaded.set(true);
		} catch (e) {
			logger.error('Failed to load tickets', e, { context: 'HistoryPage' });
			error = true;
			showToast($t('history.errorTitle') || 'Failed to load tickets', 'error');
		} finally {
			isLoadingMore = false;
			isLoading = false;
		}
	}

	function handleIntersect() {
		if (!mounted || isLoadingMore || !pagination.hasMore) return;
		loadTickets(pagination.page + 1, filters);
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
	const handleNoteUpdate = async (e: CustomEvent<{ ticketId: string; note: string }>) => {
		const { ticketId, note } = e.detail;
		try {
			// Use store action (handles API + optimistic update)
			await ticketsStore.updateNote(ticketId, note);
			showToast($t('history.noteSaved'), 'success');
		} catch (err) {
			logger.error('Failed to update note', err, { context: 'HistoryPage' });
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
		} catch (e) {
			logger.error('Failed to delete ticket', e, { context: 'HistoryPage' });
			showToast($t('common.error'), 'error');
		} finally {
			isDeleting = false;
		}
	};

	let editingTicket: TicketType | null = null;

	const handleTicketUpdate = (e: CustomEvent<TicketType>) => {
		const updated = e.detail;
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

<div class="max-w-7xl mx-auto p-4 animate-fade-in pb-24">
	<!-- Page Header -->
	<div class="mb-8">
		<PageHeader
			title={$t('history.title')}
			subtitle={$t('history.subtitle')}
			icon={History}
			theme="blue"
		>
			<div slot="actions" class="flex items-center gap-3">
				<HistoryFilter
					{filters}
					on:filterChange={(e) => handleFilterChange(e.detail)}
					bind:viewMode
				/>
			</div>
		</PageHeader>
	</div>

	<!-- Content Area -->
	<!-- Content Area -->
	{#if error && filteredTickets.length === 0}
		<ErrorState
			title={$t('history.errorTitle') || 'Failed to load tickets'}
			description={$t('history.errorDesc') || 'Something went wrong while fetching your history.'}
			onRetry={() => loadTickets(1, filters)}
		/>
	{:else if isLoading && filteredTickets.length === 0}
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
						on:updateNote={handleNoteUpdate}
						on:editTicket={(e) => (editingTicket = e.detail)}
						on:deleteTicket={(e) => openDeleteModal(e.detail)}
					/>
				{/each}
			</div>
		{:else}
			<!-- Table View -->
			<TicketTable
				tickets={filteredTickets}
				on:updateNote={handleNoteUpdate}
				on:editTicket={(e) => (editingTicket = e.detail)}
				on:deleteTicket={(e) => openDeleteModal(e.detail)}
			/>
		{/if}

		<!-- Sentinel for infinite scroll -->
		{#if pagination.hasMore}
			<div
				use:infiniteScroll
				on:intersect={handleIntersect}
				class="w-full py-6 flex justify-center"
			>
				{#if isLoadingMore}
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
		on:close={() => (editingTicket = null)}
		on:save={handleTicketUpdate}
	/>
{/if}
