<script lang="ts">
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { LoaderCircle, AlertTriangle, PenLine, PanelLeft } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { ticketsStore, showToast } from '$lib/stores';
	import { isTicketsLoading } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import JournalSidebar from '$lib/components/journal/JournalSidebar.svelte';
	import JournalEditor from '$lib/components/journal/JournalEditor.svelte';
	import { isCacheExpired } from '$lib/utils/cache';

	const { t } = useTranslation();

	let innerWidth = 0;
	let isSidebarVisible = true;
	let isResizing = false;

	// Store data
	$: state = $ticketsStore;
	$: tickets = state.list;
	$: filters = state.filters;
	$: error = state.error;
	$: loading = $isTicketsLoading;

	let selectedTicketId: string | null = null;
	$: selectedTicket = tickets.find((t) => t._id === selectedTicketId) || null;

	$: hasMore = state.pagination
		? state.pagination.current_page < state.pagination.last_page
		: false;
	$: totalData = state.pagination?.total_data || tickets.length;

	onMount(() => {
		if (tickets.length === 0 || isCacheExpired($ticketsStore.lastUpdated)) {
			ticketsStore.load(1);
		}
	});

	function handleSelect(event: CustomEvent<{ id: string }>) {
		selectedTicketId = event.detail.id;
		if (innerWidth < 768) {
			isSidebarVisible = false; // collapse sidebar on mobile when selected
		}
	}

	function handleToggleSidebar() {
		isSidebarVisible = !isSidebarVisible;
	}

	async function handleSaveNote(event: CustomEvent<{ ticketId: string; note: string }>) {
		const { ticketId, note } = event.detail;
		try {
			await ticketsStore.updateNote(ticketId, note);
			showToast($t('journal.saved'), 'success');
		} catch (err) {
			showToast($t('common.error'), 'error');
		}
	}

	function handleLoadMore() {
		if (hasMore && !loading && state.pagination) {
			ticketsStore.load(state.pagination.current_page + 1, filters);
		}
	}

	function handleFilterChange(event: CustomEvent<import('$lib/types').TicketFilters>) {
		ticketsStore.load(1, event.detail);
	}

	function startResizing(e: MouseEvent) {
		isResizing = true;
		document.body.style.cursor = 'col-resize';
		document.body.style.userSelect = 'none';
		// We don't resize the right side like playground, because there's no response pane.
		// The central pane is full width minus sidebar.
		// Resizing sidebar is possible, but for now we just keep it fixed to emulate the layout clean look.
		stopResizing();
	}

	function stopResizing() {
		isResizing = false;
		document.body.style.cursor = 'default';
		document.body.style.userSelect = 'auto';
	}
</script>

<svelte:window bind:innerWidth />

<SEO title={$t('nav.journal')} description={$t('seo.journal')} />

<div
	class="h-[calc(100vh-64px)] flex flex-col bg-slate-50/50 dark:bg-zinc-900/40 overflow-hidden relative overscroll-none"
>
	{#if loading && tickets.length === 0}
		<div class="flex-1 flex flex-col items-center justify-center space-y-4 pb-32" in:fade>
			<LoaderCircle class="w-10 h-10 animate-spin text-red-500" />
			<p class="text-sm font-bold text-gray-500 uppercase tracking-widest">
				{$t('common.loading')}
			</p>
		</div>
	{:else if error && tickets.length === 0}
		<div
			class="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-6 pb-32"
			in:fade
		>
			<div
				class="w-20 h-20 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center"
			>
				<AlertTriangle class="w-10 h-10 text-red-600" />
			</div>
			<div class="max-w-md">
				<h2 class="text-2xl font-black text-gray-900 dark:text-white mb-2">{$t('common.error')}</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400 mb-6">{error}</p>
				<button
					on:click={() => window.location.reload()}
					class="px-6 py-3 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 transition-colors shadow-lg shadow-red-500/20"
				>
					{$t('errors.tryAgain')}
				</button>
			</div>
		</div>
	{:else}
		<div class="flex-1 flex flex-col md:flex-row overflow-hidden relative" in:fade>
			<!-- Desktop Content Spacer -->
			{#if innerWidth >= 768}
				<div
					class="hidden md:block transition-all duration-300 ease-in-out shrink-0 overflow-hidden"
					style="width: {isSidebarVisible ? '320px' : '0px'}; opacity: {isSidebarVisible
						? '1'
						: '0'};"
				></div>
			{/if}

			<!-- Sidebar Drawer -->
			<div
				class="h-full overflow-hidden border-r border-gray-100 dark:border-white/5 shrink-0
					   absolute inset-y-0 left-0 z-30 md:z-[60] bg-white dark:bg-zinc-900/60 backdrop-blur-md
					   transition-transform duration-300 ease-in-out w-full md:w-[320px] md:shadow-none
					   {isSidebarVisible ? 'translate-x-0' : '-translate-x-full'}"
			>
				<div class="w-full h-full">
					<JournalSidebar
						{tickets}
						{loading}
						{hasMore}
						{totalData}
						{filters}
						selectedId={selectedTicketId}
						on:select={handleSelect}
						on:loadMore={handleLoadMore}
						on:filterChange={handleFilterChange}
						on:toggleSidebar={handleToggleSidebar}
					/>
				</div>
			</div>

			<!-- Main Content Area -->
			<div class="flex-1 flex flex-col md:flex-row overflow-hidden relative">
				<!-- Floating Toggle Button (Sleek Edge Tab) -->
				{#if !isSidebarVisible}
					<div
						class="absolute top-4 left-0 z-[50] transition-all duration-300"
						transition:fade={{ duration: 200 }}
					>
						<button
							on:click={handleToggleSidebar}
							class="flex items-center justify-center w-8 h-10 bg-white dark:bg-zinc-900 border-y border-r border-gray-200 dark:border-white/10 rounded-r-xl shadow-lg text-gray-400 hover:text-red-500 transition-all hover:w-10 active:scale-95 cursor-pointer"
							title={$t('journal.showSidebar')}
						>
							<PanelLeft class="w-4 h-4 ml-1" />
						</button>
					</div>
				{/if}

				<div class="flex-1 min-h-0 min-w-0 overflow-hidden flex relative">
					{#if !selectedTicket}
						<div
							class="flex-1 flex flex-col items-center justify-center p-12 text-center relative pb-32"
						>
							<div
								class="w-24 h-24 bg-gray-50 dark:bg-zinc-900/50 rounded-full flex items-center justify-center mb-6"
							>
								<PenLine class="w-10 h-10 text-gray-300 dark:text-gray-700" />
							</div>
							<h2 class="text-2xl font-black text-gray-900 dark:text-gray-100 mb-2">
								{$t('journal.emptyTitle')}
							</h2>
							<p class="text-gray-500 dark:text-gray-400 max-w-sm mx-auto leading-relaxed">
								{$t('journal.emptyState')}
							</p>
						</div>
					{:else}
						<JournalEditor
							ticket={selectedTicket}
							on:save={handleSaveNote}
							on:toggleSidebar={handleToggleSidebar}
						/>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>
