<script lang="ts">
	import {
		tickets,
		ticketsPagination,
		showToast,
		isAuthenticated,
		isInitialDataLoaded,
		ticketsFilters,
		defaultTickets,
		defaultTicketsPagination
	} from '$lib/stores';
	import { invalidateDashboard } from '$lib/stores/dashboard';
	import { onMount } from 'svelte';
	import { ticketsApi } from '$lib/apis/tickets';
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

	import { get } from 'svelte/store';

	const { t } = useTranslation();

	// Main Component Logic
	let viewMode: 'GRID' | 'TABLE' = 'GRID';
	let filters: TicketFilters = {};
	let deleteId: string | null = null;
	let isDeleting = false;
	let error = false;

	/* Loading State */
	let mounted = false;
	let isLoadingMore = false;

	onMount(() => {
		mounted = true;

		// Check if we already have default data, or restore from cache if needed.
		// If no data exists, fetch from API.

		const cachedFilters = get(ticketsFilters);
		const currentTicketCount = get(tickets).length;

		// Check if the data currently in store matches "Default"
		const storeIsDefault = Object.keys(cachedFilters).length === 0;

		if (currentTicketCount > 0 && storeIsDefault) {
			// Current store is already default data. No fetch needed.
			return;
		}

		// Current store is NOT default (it has filtered data).
		// Do we have default data cached? If so, restore it.
		const defaults = get(defaultTickets);
		const defaultPagination = get(defaultTicketsPagination);
		if (defaults && defaultPagination) {
			// Restore default from cache
			tickets.set(defaults);
			ticketsPagination.set(defaultPagination);
			ticketsFilters.set({}); // Mark store as default
			return;
		}

		// No cache, must fetch
		loadTickets(1);
	});

	async function loadTickets(page: number, currentFilters: TicketFilters = {}) {
		if (isLoadingMore) return;
		isLoadingMore = true;
		isLoadingMore = true;
		try {
			error = false;
			const res = await ticketsApi.getMyTickets(page, 20, currentFilters);
			if (page === 1) {
				tickets.set(res.data);
				// Update cached filters when we start a new search
				ticketsFilters.set(currentFilters);

				// If this is a default load, cache it for later
				if (Object.keys(currentFilters).length === 0) {
					defaultTickets.set(res.data);
				}
			} else {
				tickets.update((curr) => [...curr, ...res.data]);
			}

			const currentPagination = {
				page,
				hasMore: res.meta.current_page < res.meta.last_page
			};
			ticketsPagination.set(currentPagination);

			// If this is a default load, keep the default cache in sync
			if (Object.keys(currentFilters).length === 0) {
				defaultTicketsPagination.set(currentPagination);
			}

			isInitialDataLoaded.set(true);
		} catch (e) {
			console.error(e);
			error = true;
			showToast($t('history.errorTitle') || 'Failed to load tickets', 'error');
		} finally {
			isLoadingMore = false;
		}
	}

	function handleScroll() {
		if (!mounted || isLoadingMore || !$ticketsPagination.hasMore) return;

		const threshold = 300;
		const position = window.innerHeight + window.scrollY;
		const height = document.body.offsetHeight;

		if (position > height - threshold) {
			loadTickets($ticketsPagination.page + 1, filters);
		}
	}

	let searchTimeout: ReturnType<typeof setTimeout>;

	function handleFilterChange(newFilters: TicketFilters) {
		if (!mounted) return;
		// Skip if initial data hasn't loaded yet (prevents duplicate calls on refresh)
		if (!get(isInitialDataLoaded)) return;
		filters = newFilters;
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			loadTickets(1, filters);
		}, 500);
	}

	// We'll bind this to the Filter component later
	// $: handleFilterChange(filters);

	$: isLoading = !mounted || ($isAuthenticated && $tickets.length === 0 && !$isInitialDataLoaded);

	$: filteredTickets = [...$tickets];

	// Actions
	// Logic for note update
	const handleNoteUpdate = async (e: CustomEvent<{ ticketId: string; note: string }>) => {
		const { ticketId, note } = e.detail;
		try {
			// Update locally immediately
			tickets.update((items) => items.map((t) => (t._id === ticketId ? { ...t, notes: note } : t)));
			defaultTickets.update((items) =>
				items ? items.map((t) => (t._id === ticketId ? { ...t, notes: note } : t)) : null
			);

			// Sync with API
			await ticketsApi.updateTicket(ticketId, { notes: note });
			showToast($t('history.noteSaved'), 'success');
		} catch (err) {
			console.error('Failed to update note', err);
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
			await ticketsApi.deleteTicket(deleteId);
			tickets.update((current) => current.filter((t) => t._id !== deleteId));
			defaultTickets.update((current) =>
				current ? current.filter((t) => t._id !== deleteId) : null
			);

			// Invalidate dashboard cache
			invalidateDashboard();

			deleteId = null;
			showToast($t('history.ticketDeleted'), 'success');
		} catch (e) {
			console.error('Failed to delete ticket', e);
			showToast($t('common.error'), 'error');
		} finally {
			isDeleting = false;
		}
	};

	let editingTicket: TicketType | null = null;

	const handleTicketUpdate = (e: CustomEvent<TicketType>) => {
		const updated = e.detail;
		tickets.update((current) => current.map((t) => (t._id === updated._id ? updated : t)));
		defaultTickets.update((current) =>
			current ? current.map((t) => (t._id === updated._id ? updated : t)) : null
		);

		// Invalidate dashboard cache
		invalidateDashboard();

		editingTicket = null;
	};
</script>

<SEO title={$t('history.title')} path="/history" description={$t('history.description')} />
<svelte:window on:scroll={handleScroll} />

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
	{:else if isLoading || (isLoadingMore && filteredTickets.length === 0)}
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

		{#if isLoadingMore}
			{#if viewMode === 'GRID'}
				<TicketCardSkeleton count={3} className="mt-6" />
			{:else}
				<div class="mt-4">
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
	{/if}
</div>

<!-- Delete Modal -->

<!-- Edit Modal -->
{#if editingTicket}
	<EditTicketModal
		ticket={editingTicket}
		on:close={() => (editingTicket = null)}
		on:save={handleTicketUpdate}
	/>
{/if}
