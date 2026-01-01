<script lang="ts">
	import { tickets, showToast, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { onMount } from 'svelte';
	import { theater } from '$lib/apis/theater';
	import { Mic2 } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';

	// Import shared constants
	import { SHOW_IMAGES } from '$lib/constants';

	// Import components
	import { DeleteConfirmationModal } from '$lib/components/history';
	import { ShowCard, ShowStatsGrid, ShowTicketItem, ShowDetailHeader } from '$lib/components/shows';

	const { t } = useTranslation();

	// Use shared constant (alias for backward compatibility)
	const SHOW_DATA = SHOW_IMAGES;

	// State
	let selectedShowTitle: string | null = null;
	let deleteId: string | null = null;
	let isDeleting = false;

	/* Loading State */
	let mounted = false;

	onMount(() => {
		mounted = true;
	});

	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded);

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

	// Derived
	$: showCounts = $tickets.reduce(
		(acc, t) => {
			const title = t.event.title.trim();
			const matchedShow = SHOW_DATA.find((s) =>
				title.toLowerCase().includes(s.title.toLowerCase())
			);

			if (matchedShow) {
				acc[matchedShow.title] = (acc[matchedShow.title] || 0) + 1;
			} else {
				acc[title] = (acc[title] || 0) + 1;
			}
			return acc;
		},
		{} as Record<string, number>
	);

	$: maxAttendance = Math.max(...Object.values(showCounts), 1);

	// Detail View Data
	$: selectedShowData = selectedShowTitle
		? {
				info: SHOW_DATA.find((s) => s.title === selectedShowTitle),
				tickets: $tickets.filter((t) =>
					t.event.title.toLowerCase().includes((selectedShowTitle || '').toLowerCase())
				)
			}
		: null;

	$: if (selectedShowData) {
		selectedShowData.tickets.sort(
			(a, b) => new Date(a.event.date).getTime() - new Date(b.event.date).getTime()
		);
	}

	$: stats = selectedShowData
		? (() => {
				const t = selectedShowData.tickets;
				const first = t[0];
				const last = t[t.length - 1];
				const totalSpent = t.reduce((acc, curr) => acc + curr.price, 0);
				const avgPrice = t.length > 0 ? totalSpent / t.length : 0;

				const rowCounts = t.reduce(
					(acc, curr) => {
						const r = curr.seat.section.toUpperCase().charAt(0);
						acc[r] = (acc[r] || 0) + 1;
						return acc;
					},
					{} as Record<string, number>
				);
				const topRow = Object.entries(rowCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '-';

				return { first, last, avgPrice, topRow, totalSpent };
			})()
		: null;

	const selectShow = (title: string) => {
		selectedShowTitle = title;
	};
</script>

<SEO title={selectedShowTitle || $t('shows.title')} path="/shows" description={$t('seo.shows')} />

<!-- Delete Modal -->
<DeleteConfirmationModal
	show={!!deleteId}
	{isDeleting}
	onCancel={() => (deleteId = null)}
	onConfirm={confirmDelete}
/>

<div class="max-w-6xl mx-auto p-4 pb-24 animate-fade-in">
	{#if selectedShowTitle && selectedShowData}
		<ShowDetailHeader
			title={selectedShowTitle}
			info={selectedShowData.info}
			ticketCount={selectedShowData.tickets.length}
			onBack={() => (selectedShowTitle = null)}
		/>

		<!-- Stats Grid -->
		{#if stats && selectedShowData.tickets.length > 0}
			<ShowStatsGrid {stats} />
		{/if}

		<!-- Ticket List -->
		<div class="space-y-4">
			{#each selectedShowData.tickets as ticket (ticket._id)}
				<ShowTicketItem {ticket} onDelete={(id) => (deleteId = id)} />
			{/each}
		</div>
	{:else}
		<!-- Main List -->
		<div class="flex items-center gap-3 mb-8">
			<div
				class="p-3 rounded-2xl bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 shadow-lg shadow-purple-100 dark:shadow-purple-900/20 border-2 border-white dark:border-zinc-700 transform -rotate-6"
			>
				<Mic2 class="w-6 h-6" />
			</div>
			<div>
				<h2 class="text-2xl font-bold text-themed w-fit relative">
					{$t('shows.title')}
					<span
						class="absolute -bottom-1 left-0 w-full h-2 bg-purple-200/60 dark:bg-purple-500/30 -z-10 transform -skew-x-12 rounded-sm"
					></span>
				</h2>
				<p class="text-sm text-themed-secondary">{$t('shows.subtitle')}</p>
			</div>
		</div>

		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
			{#if isLoading}
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
							<div
								class="w-full bg-gray-200 dark:bg-zinc-700 rounded-full h-1.5 animate-pulse"
							></div>
						</div>
					</div>
				{/each}
			{:else}
				{#each SHOW_DATA as show (show.title)}
					{@const count = showCounts[show.title] || 0}
					<ShowCard {show} {count} {maxAttendance} onClick={() => selectShow(show.title)} />
				{/each}
			{/if}
		</div>
	{/if}
</div>
