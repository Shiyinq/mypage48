<script lang="ts">
	import { tickets, showToast, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { onMount } from 'svelte';
	import { theater } from '$lib/apis/theater';
	import type { Ticket } from '$lib/types';
	import EditTicketModal from '$lib/components/EditTicketModal.svelte';
	import {
		History,
		Search,
		LayoutGrid,
		List,
		Trash2,
		AlertTriangle,
		Pencil,
		Calendar,
		Clock,
		MapPin,
		Save,
		X,
		NotebookPen,
		Ticket as TicketIcon
	} from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { fade, scale } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';

	// Shared components and utils
	import { PageHeader, EmptyState } from '$lib/components';
	import { GridSkeleton, TableSkeleton } from '$lib/components/skeletons';
	import { formatCurrency, formatDateFull } from '$lib/utils/formatting';

	const { t } = useTranslation();

	// Main Component Logic
	let viewMode: 'GRID' | 'TABLE' = 'GRID';
	let searchQuery = '';
	let deleteId: string | null = null;
	let isDeleting = false;
	let editingId: string | null = null;
	let noteText = '';

	/* Loading State */
	let mounted = false;

	onMount(() => {
		mounted = true;
	});

	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded);

	// Derived
	$: filteredTickets = ($tickets as Ticket[]).filter((t) => {
		const q = searchQuery.toLowerCase();
		const date = new Date(t.event.date);
		const formattedDate = date
			.toLocaleDateString('id-ID', {
				day: 'numeric',
				month: 'long',
				year: 'numeric'
			})
			.toLowerCase();
		const formattedDateShort = date
			.toLocaleDateString('id-ID', {
				day: 'numeric',
				month: 'short',
				year: 'numeric'
			})
			.toLowerCase();

		return (
			t.event.title.toLowerCase().includes(q) ||
			t.ticket_id.toLowerCase().includes(q) ||
			t.event.date.includes(q) ||
			formattedDate.includes(q) ||
			formattedDateShort.includes(q) ||
			`${t.seat.section}-${t.seat.number}`.toLowerCase().includes(q)
		);
	});

	// Methods
	const confirmDelete = async () => {
		if (!deleteId || isDeleting) return;

		const idToDelete = deleteId;
		isDeleting = true;

		try {
			await theater.deleteTicket(idToDelete);
			// Fetch fresh data from server after delete
			const freshTickets = await theater.getMyTickets();
			tickets.set(freshTickets);
			showToast('Ticket deleted successfully', 'success');
		} catch (error) {
			console.error('Failed to delete ticket:', error);
			showToast('Failed to delete ticket', 'error');
		} finally {
			isDeleting = false;
			deleteId = null;
		}
	};

	const startEditingNote = (ticket: Ticket) => {
		editingId = ticket._id;
		noteText = ticket.notes || '';
	};

	const saveNote = (ticket: Ticket) => {
		tickets.update((current) =>
			current.map((t) => (t._id === ticket._id ? { ...t, notes: noteText } : t))
		);
		editingId = null;
	};

	let editingTicket: Ticket | null = null;

	const handleTicketUpdate = (e: CustomEvent<Ticket>) => {
		const updated = e.detail;
		tickets.update((current) => current.map((t) => (t._id === updated._id ? updated : t)));
		editingTicket = null;
	};
</script>

<SEO title={$t('history.title')} path="/history" description={$t('seo.history')} />

<div class="max-w-6xl mx-auto p-4 pb-24 animate-fade-in relative">
	<!-- Header Section -->
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
		<!-- Header -->
		<PageHeader
			icon={History}
			title={$t('history.title')}
			subtitle={$t('history.subtitle')}
			theme="blue"
		/>

		<!-- Toolbar -->
		<div class="flex items-center gap-3 w-full md:w-auto">
			<!-- Search Bar -->
			<div class="relative flex-1 md:w-64 group">
				<Search
					class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-red-500 transition-colors"
				/>
				<input
					type="text"
					placeholder={$t('common.search')}
					bind:value={searchQuery}
					class="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-full text-sm font-medium text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent shadow-sm transition-all"
				/>
			</div>

			<!-- View Toggle -->
			<div
				class="flex bg-white dark:bg-zinc-900 p-1 rounded-full border border-gray-200 dark:border-zinc-700 shadow-sm"
			>
				<button
					on:click={() => (viewMode = 'GRID')}
					class={`p-2 rounded-full transition-all cursor-pointer ${viewMode === 'GRID' ? 'bg-red-50 dark:bg-red-500/20 text-red-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
					title="Grid View"
				>
					<LayoutGrid class="w-4 h-4" />
				</button>
				<button
					on:click={() => (viewMode = 'TABLE')}
					class={`p-2 rounded-full transition-all cursor-pointer ${viewMode === 'TABLE' ? 'bg-red-50 dark:bg-red-500/20 text-red-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
					title="Table View"
				>
					<List class="w-4 h-4" />
				</button>
			</div>
		</div>
	</div>

	<!-- Content Area -->
	{#if isLoading}
		{#if viewMode === 'GRID'}
			<GridSkeleton count={6} aspectRatio="video" />
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
				<div
					class="bg-white dark:bg-zinc-900 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-gray-100 dark:border-zinc-700 flex flex-col group animate-fade-in h-full"
				>
					<!-- Image Section -->
					<div class="h-48 w-full relative bg-gray-50 overflow-hidden flex-shrink-0">
						{#if ticket.imageUrl}
							<div class="w-full h-full relative">
								<img
									src={ticket.imageUrl}
									alt={ticket.event.title}
									class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
								/>
								<div
									class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-90"
								></div>
							</div>
						{:else}
							<div
								class="w-full h-full idol-gradient flex items-center justify-center relative overflow-hidden bg-gray-800"
							>
								<div
									class="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(255,255,255,0.2)_1px,_transparent_1px)] bg-[length:20px_20px] opacity-30"
								></div>
								<TicketIcon class="text-white opacity-20 w-24 h-24 transform -rotate-12" />
							</div>
						{/if}

						<div class="absolute top-3 left-3">
							<span
								class="inline-block px-3 py-1 bg-black/30 backdrop-blur-md text-white text-[10px] font-bold rounded-full uppercase tracking-wider border border-white/20 shadow-lg"
							>
								{ticket.event.day
									? $t('time.days.' + ticket.event.day.toLowerCase())
									: $t('history.show')}
							</span>
						</div>

						<div class="absolute bottom-0 left-0 right-0 p-5">
							<div class="text-white/80 font-mono text-xs mb-1 tracking-wide">
								#{ticket.ticket_id}
							</div>
							<h3 class="font-bold text-white leading-tight text-xl line-clamp-2 drop-shadow-md">
								{ticket.event.title}
							</h3>
						</div>
					</div>

					<!-- Body -->
					<div class="p-5 flex-1 flex flex-col gap-4">
						<div class="grid grid-cols-2 gap-4">
							<div class="flex flex-col">
								<span class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase mb-1"
									>{$t('history.date')}</span
								>
								<div
									class="flex items-center text-gray-700 dark:text-gray-300 text-sm font-semibold"
								>
									<Calendar class="w-3.5 h-3.5 mr-1.5 text-red-500" />
									{formatDateFull(ticket.event.date)}
								</div>
							</div>
							<div class="flex flex-col">
								<span class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase mb-1"
									>{$t('history.time')}</span
								>
								<div
									class="flex items-center text-gray-700 dark:text-gray-300 text-sm font-semibold"
								>
									<Clock class="w-3.5 h-3.5 mr-1.5 text-red-500" />
									{ticket.event.time}
								</div>
							</div>
						</div>

						<div
							class="bg-red-50 dark:bg-red-900/20 rounded-xl p-3 border border-red-100 dark:border-red-500/30 flex items-center justify-between"
						>
							<div class="flex items-center gap-3">
								<div
									class="w-8 h-8 rounded-full bg-white flex items-center justify-center shadow-sm text-red-600"
								>
									<MapPin class="w-4 h-4" />
								</div>
								<div class="flex flex-col">
									<span class="text-[10px] text-red-400 dark:text-red-300 font-bold uppercase"
										>{$t('history.seat')}</span
									>
									<span class="text-gray-900 dark:text-gray-100 font-extrabold text-sm"
										>{ticket.seat.section} - {ticket.seat.number}</span
									>
								</div>
							</div>
							<div class="text-right">
								<span
									class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase block mb-0.5"
									>{$t('history.price')}</span
								>
								<span class="text-red-600 font-bold text-sm">
									{formatCurrency(ticket.price)}
								</span>
							</div>
						</div>

						<!-- Notes -->
						<div class="flex-1">
							<div class="flex items-center justify-between mb-2">
								<span
									class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase flex items-center gap-1"
								>
									<NotebookPen class="w-3 h-3" />
									{$t('history.notes')}
								</span>
								{#if editingId !== ticket._id}
									<button
										on:click={() => startEditingNote(ticket)}
										class="text-xs text-red-500 hover:text-red-700 font-medium flex items-center gap-1"
									>
										{#if ticket.notes}
											<Pencil class="w-3 h-3" /> {$t('history.editNote')}
										{:else}
											<NotebookPen class="w-3 h-3" /> {$t('history.addNote')}
										{/if}
									</button>
								{/if}
							</div>

							{#if editingId === ticket._id}
								<div class="animate-fade-in">
									<textarea
										bind:value={noteText}
										class="w-full p-3 text-sm text-gray-900 border border-gray-200 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none bg-yellow-50/50 min-h-[80px]"
										placeholder="Write about your experience..."
									></textarea>
									<div class="flex justify-end gap-2 mt-2">
										<button
											on:click={() => (editingId = null)}
											class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
										>
											<X class="w-4 h-4" />
										</button>
										<button
											on:click={() => saveNote(ticket)}
											class="px-3 py-1.5 bg-red-600 text-white text-xs font-bold rounded-md hover:bg-red-700 transition-colors flex items-center gap-1"
										>
											<Save class="w-3 h-3" />
											{$t('history.saveNote')}
										</button>
									</div>
								</div>
							{:else}
								<div
									class="bg-yellow-50/50 dark:bg-zinc-800/50 rounded-lg p-3 border border-yellow-100/50 dark:border-zinc-600 min-h-[60px]"
								>
									{#if ticket.notes}
										<p
											class="text-sm text-gray-900 dark:text-gray-200 whitespace-pre-wrap font-light italic leading-relaxed line-clamp-3"
										>
											"{ticket.notes}"
										</p>
									{:else}
										<p class="text-xs text-gray-400 dark:text-gray-500 italic">
											{$t('history.noNotes')}
										</p>
									{/if}
								</div>
							{/if}
						</div>
					</div>

					<div
						class="px-5 py-3 border-t border-gray-100 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800/50 flex justify-between items-center mt-auto"
					>
						<button
							on:click={() => (editingTicket = ticket)}
							class="text-xs font-bold text-gray-900 dark:text-gray-200 hover:text-red-600 flex items-center gap-1 px-2 py-1 rounded-md hover:bg-white dark:hover:bg-zinc-700 transition-colors cursor-pointer"
						>
							<Pencil class="w-3 h-3" />
							{$t('history.editDetails')}
						</button>
						<button
							on:click={() => (deleteId = ticket._id)}
							class="text-gray-400 hover:text-red-600 transition-colors p-2 hover:bg-white rounded-full border border-transparent hover:border-red-100 hover:shadow-sm cursor-pointer"
						>
							<Trash2 class="w-4 h-4" />
						</button>
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<!-- Table View -->
		<div class="glass-panel rounded-3xl overflow-hidden shadow-sm">
			<div class="overflow-x-auto">
				<table class="w-full text-left border-collapse">
					<thead>
						<tr
							class="bg-gray-50/80 dark:bg-zinc-800/80 border-b border-gray-200 dark:border-zinc-700 text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 font-bold"
						>
							<th class="p-4">{$t('history.date')}</th>
							<th class="p-4">{$t('history.eventDetails')}</th>
							<th class="p-4">{$t('history.seat')}</th>
							<th class="p-4">{$t('history.price')}</th>
							<th class="p-4">{$t('history.notes')}</th>
							<th class="p-4 text-right">{$t('history.actions')}</th>
						</tr>
					</thead>
					<tbody
						class="bg-white/50 dark:bg-zinc-900/50 divide-y divide-gray-100 dark:divide-zinc-700"
					>
						{#each filteredTickets as ticket (ticket._id)}
							<tr
								class="group border-b border-gray-100 dark:border-zinc-700 hover:bg-red-50/30 dark:hover:bg-red-900/10 transition-colors"
							>
								<td class="p-4">
									<div class="flex flex-col">
										<span class="font-bold text-gray-800 dark:text-gray-200 text-sm">
											{formatDateFull(ticket.event.date)}
										</span>
										<span
											class="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1 mt-0.5"
										>
											<Clock class="w-3 h-3" />
											{ticket.event.time}
										</span>
									</div>
								</td>
								<td class="p-4">
									<div class="flex items-center gap-3">
										<div
											class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-zinc-800 overflow-hidden flex-shrink-0 border border-gray-200 dark:border-zinc-700"
										>
											{#if ticket.imageUrl}
												<img src={ticket.imageUrl} alt="" class="w-full h-full object-cover" />
											{:else}
												<div
													class="w-full h-full idol-gradient flex items-center justify-center relative overflow-hidden"
												>
													<TicketIcon class="w-5 h-5 text-white/40 transform -rotate-12" />
												</div>
											{/if}
										</div>
										<div>
											<div class="font-bold text-gray-800 dark:text-gray-200 text-sm line-clamp-1">
												{ticket.event.title}
											</div>
											<div class="text-xs text-gray-400 dark:text-gray-500 font-mono">
												#{ticket.ticket_id}
											</div>
										</div>
									</div>
								</td>
								<td class="p-4">
									<div
										class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 shadow-sm"
									>
										<span
											class="text-xs font-bold text-red-500 bg-red-50 dark:bg-red-900/30 px-1.5 rounded"
											>{ticket.seat.section}</span
										>
										<span class="text-sm font-bold text-gray-700 dark:text-gray-300"
											>{ticket.seat.number}</span
										>
									</div>
								</td>
								<td class="p-4">
									<span class="text-sm font-medium text-gray-600 dark:text-gray-400">
										{formatCurrency(ticket.price)}
									</span>
								</td>
								<td class="p-4 w-1/3">
									{#if editingId === ticket._id}
										<div class="flex items-center gap-2">
											<input
												bind:value={noteText}
												class="w-full text-sm text-gray-900 dark:text-gray-100 p-2 border border-red-200 dark:border-red-500/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 bg-white dark:bg-zinc-800"
												on:keydown={(e) => e.key === 'Enter' && saveNote(ticket)}
											/>
											<button
												on:click={() => saveNote(ticket)}
												class="p-1.5 bg-red-600 text-white rounded-md hover:bg-red-700"
												><Save class="w-3 h-3" /></button
											>
											<button
												on:click={() => (editingId = null)}
												class="p-1.5 bg-gray-200 dark:bg-zinc-700 text-gray-600 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-zinc-600"
												><X class="w-3 h-3" /></button
											>
										</div>
									{:else}
										<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
										<div
											on:click={() => startEditingNote(ticket)}
											class="text-sm text-gray-500 dark:text-gray-400 italic cursor-pointer hover:text-red-600 flex items-center gap-2 group/note"
										>
											<span class="line-clamp-1">{ticket.notes || $t('history.addNote')}</span>
											<Pencil
												class="w-3 h-3 opacity-0 group-hover/note:opacity-100 transition-opacity"
											/>
										</div>
									{/if}
								</td>
								<td class="p-4 text-right">
									<div class="flex items-center justify-end gap-2">
										<button
											on:click={() => (editingTicket = ticket)}
											class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-full transition-colors cursor-pointer"
										>
											<Pencil class="w-4 h-4" />
										</button>
										<button
											on:click={() => (deleteId = ticket._id)}
											class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-full transition-colors cursor-pointer"
										>
											<Trash2 class="w-4 h-4" />
										</button>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>

<!-- Delete Modal -->
{#if deleteId}
	<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
	<div
		class="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
		on:click={() => (deleteId = null)}
		transition:fade={{ duration: 150 }}
	>
		<div
			class="bg-white rounded-3xl shadow-2xl max-w-sm w-full p-6"
			on:click={(e) => e.stopPropagation()}
			transition:scale={{ duration: 200, start: 0.95 }}
		>
			<div
				class="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mb-4 mx-auto"
			>
				<AlertTriangle class="w-6 h-6" />
			</div>
			<div class="text-center mb-6">
				<h3 class="text-xl font-bold text-gray-900 mb-2">{$t('history.deleteConfirm.title')}</h3>
				<p class="text-sm text-gray-500 leading-relaxed">
					{$t('history.deleteConfirm.description')}
				</p>
			</div>
			<div class="grid grid-cols-2 gap-3">
				<button
					on:click={() => (deleteId = null)}
					disabled={isDeleting}
					class="px-4 py-2.5 rounded-xl font-bold text-gray-600 hover:bg-gray-100 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{$t('common.cancel')}
				</button>
				<button
					on:click={confirmDelete}
					disabled={isDeleting}
					class="px-4 py-2.5 rounded-xl font-bold text-white bg-red-600 hover:bg-red-700 shadow-lg shadow-red-200 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{isDeleting ? $t('common.loading') : $t('history.deleteConfirm.confirm')}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Edit Modal -->
{#if editingTicket}
	<EditTicketModal
		ticket={editingTicket}
		on:close={() => (editingTicket = null)}
		on:save={handleTicketUpdate}
	/>
{/if}
