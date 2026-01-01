<script lang="ts">
	import { tickets, showToast, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { onMount } from 'svelte';
	import { theater } from '$lib/apis/theater';
	import type { Ticket } from '$lib/types';
	import EditTicketModal from '$lib/components/EditTicketModal.svelte';
	import { History, Search } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { fade, scale } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';

	// Shared components and utils
	import { PageHeader, EmptyState } from '$lib/components';
	import { GridSkeleton, TableSkeleton, TicketCardSkeleton } from '$lib/components/skeletons';
	import {
		DeleteConfirmationModal,
		TicketCard,
		TicketTable,
		HistoryFilter
	} from '$lib/components/history';
	import { formatDateFull } from '$lib/utils/formatting';

	const { t } = useTranslation();

	// Main Component Logic
	let viewMode: 'GRID' | 'TABLE' = 'GRID';
	let searchQuery = '';
	let deleteId: string | null = null;
	let isDeleting = false;

	/* Loading State */
	let mounted = false;

	onMount(() => {
		mounted = true;
	});

	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded);

	$: sortedTickets = [...$tickets].sort(
		(a, b) => new Date(b.event.date).getTime() - new Date(a.event.date).getTime()
	);

	$: filteredTickets = sortedTickets.filter((ticket) => {
		const terms = searchQuery.toLowerCase();
		return (
			ticket.event.title.toLowerCase().includes(terms) ||
			ticket.seat.section.toLowerCase().includes(terms) ||
			ticket.notes?.toLowerCase().includes(terms) ||
			ticket.event.date.includes(terms) ||
			formatDateFull(ticket.event.date).toLowerCase().includes(terms)
		);
	});

	// Actions
	// Logic for note update
	const handleNoteUpdate = async (e: CustomEvent<{ ticketId: string; note: string }>) => {
		const { ticketId, note } = e.detail;
		try {
			// Update locally immediately
			tickets.update((items) => items.map((t) => (t._id === ticketId ? { ...t, notes: note } : t)));

			// Sync with API
			await theater.updateTicket(ticketId, { notes: note });
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
			await theater.deleteTicket(deleteId);
			deleteId = null;
			showToast($t('history.ticketDeleted'), 'success');
		} catch (e) {
			console.error('Failed to delete ticket', e);
			showToast($t('common.error'), 'error');
		} finally {
			isDeleting = false;
		}
	};

	let editingTicket: Ticket | null = null;

	const handleTicketUpdate = (e: CustomEvent<Ticket>) => {
		const updated = e.detail;
		tickets.update((current) => current.map((t) => (t._id === updated._id ? updated : t)));
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
				<HistoryFilter bind:searchQuery bind:viewMode />
			</div>
		</PageHeader>
	</div>

	<!-- Content Area -->
	{#if isLoading}
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
			icon={Search}
			title={$t('history.noTickets')}
			description={$t('history.addFirst')}
		/>
	{:else if viewMode === 'GRID'}
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
