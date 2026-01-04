<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { setlistsApi, type SetlistDetailResponse } from '$lib/apis/setlists';
	import { ticketsApi } from '$lib/apis/tickets';
	import { tickets, showToast } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { ArrowLeft, Ticket, DollarSign, Trophy } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { DeleteConfirmationModal } from '$lib/components/history';
	import { ErrorState } from '$lib/components';
	import { formatCurrency } from '$lib/utils/formatting';
	import SetlistHero from '$lib/components/theater/SetlistHero.svelte';
	import SetlistStats from '$lib/components/theater/SetlistStats.svelte';
	import Timeline from '$lib/components/history/Timeline.svelte';
	import SetlistTicketItem from '$lib/components/theater/SetlistTicketItem.svelte';

	const { t } = useTranslation();

	// Get setlistId from URL
	$: setlistId = $page.params.setlistId;

	// State
	let detail: SetlistDetailResponse | null = null;
	let loading = true;
	let error = false;
	let deleteId: string | null = null;
	let isDeleting = false;

	async function fetchDetail() {
		if (!setlistId) return;
		try {
			loading = true;
			error = false;
			detail = await setlistsApi.getDetail(setlistId);
		} catch (e) {
			console.error('Failed to fetch setlist detail:', e);
			error = true;
			showToast('Failed to load setlist detail', 'error');
		} finally {
			loading = false;
		}
	}

	async function confirmDelete() {
		if (!deleteId || isDeleting) return;

		const idToDelete = deleteId;
		isDeleting = true;

		try {
			await ticketsApi.deleteTicket(idToDelete);
			// Fetch fresh data
			const freshTickets = await ticketsApi.getMyTickets();
			tickets.set(freshTickets.data);
			// Re-fetch detail to update stats
			await fetchDetail();
			showToast($t('history.ticketDeleted'), 'success');
		} catch (e) {
			console.error('Failed to delete ticket:', e);
			showToast('Failed to delete ticket', 'error');
		} finally {
			isDeleting = false;
			deleteId = null;
		}
	}

	onMount(() => {
		fetchDetail();
	});
</script>

<SEO
	title={detail?.title || 'Setlist Detail'}
	path={`/theater/${setlistId}`}
	description={detail?.description || ''}
/>

<DeleteConfirmationModal
	show={!!deleteId}
	{isDeleting}
	onCancel={() => (deleteId = null)}
	onConfirm={confirmDelete}
/>

{#if loading}
	<div class="animate-pulse space-y-8 max-w-5xl mx-auto">
		<!-- New Hero Skeleton -->
		<div class="h-[400px] w-full bg-gray-200 dark:bg-zinc-800 rounded-3xl"></div>
		<!-- Grid Skeleton -->
		<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
			<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
			{#each Array(4) as _}
				<div class="h-32 bg-gray-200 dark:bg-zinc-800 rounded-2xl"></div>
			{/each}
		</div>
	</div>
{:else if error}
	<ErrorState
		title={$t('theater.setlists.errorTitle') || 'Failed to load detail'}
		description={$t('theater.setlists.errorDesc') ||
			'Something went wrong while fetching the setlist information.'}
		onRetry={fetchDetail}
	/>
{:else if detail}
	<div class="max-w-5xl mx-auto animate-fade-in pb-20">
		<!-- Back Button -->
		<button
			on:click={() => goto('/theater')}
			class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/50 dark:bg-zinc-800/50 backdrop-blur-sm text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-white dark:hover:bg-zinc-800 transition-all mb-6 group border border-gray-100 dark:border-zinc-700/50 cursor-pointer"
		>
			<ArrowLeft class="w-4 h-4 transition-transform group-hover:-translate-x-1" />
			{$t('shows.backTitle')}
		</button>

		<!-- Immersive Hero Section -->
		<SetlistHero {detail} />

		<!-- Main Content Grid -->
		<div class="grid grid-cols-1 md:grid-cols-12 gap-8">
			<!-- Left Column: Stats & Meta -->
			<div class="md:col-span-8 space-y-6">
				<!-- Primary Stats Grid -->
				<SetlistStats stats={detail.stats} />

				<!-- Ticket History -->
				<div class="mt-8">
					<div class="flex items-center justify-between mb-6">
						<h2 class="text-xl font-bold text-gray-900 dark:text-white">
							{$t('history.title')}
						</h2>
						<span
							class="text-sm text-gray-500 dark:text-gray-400 font-medium bg-gray-100 dark:bg-zinc-800 px-3 py-1 rounded-full"
						>
							{detail.tickets.length}
							{$t('dashboard.theater.tickets')}
						</span>
					</div>

					{#if detail.tickets.length === 0}
						<div
							class="flex flex-col items-center justify-center py-12 px-4 bg-gray-50 dark:bg-zinc-900/50 rounded-3xl border border-dashed border-gray-200 dark:border-zinc-800"
						>
							<div
								class="w-16 h-16 bg-gray-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mb-4"
							>
								<Ticket class="w-6 h-6 text-gray-400" />
							</div>
							<p class="font-medium text-gray-600 dark:text-gray-300">No tickets found</p>
							<p class="text-sm text-gray-500 dark:text-gray-400 text-center max-w-[250px] mt-1">
								{$t('theater.setlists.notAttended')}
							</p>
						</div>
					{:else}
						<div class="space-y-3">
							{#each detail.tickets as ticket (ticket.ticketId)}
								<SetlistTicketItem {ticket} on:click={() => (deleteId = ticket.ticketId)} />
							{/each}
						</div>
					{/if}
				</div>
			</div>

			<!-- Right Column: Sidebar Stats -->
			<div class="md:col-span-4 space-y-6">
				<!-- Quick Stats Card -->
				<div
					class="bg-gradient-to-br from-gray-900 to-gray-800 rounded-3xl p-6 text-white shadow-xl relative overflow-hidden"
				>
					<div class="absolute top-0 right-0 p-8 opacity-10">
						<Trophy class="w-32 h-32 rotate-12" />
					</div>

					<h3 class="text-lg font-bold mb-6 flex items-center gap-2">
						<DollarSign class="w-5 h-5 text-yellow-400" />
						{$t('theater.setlists.statsOverview')}
					</h3>

					<div class="space-y-6 relative z-10">
						<div>
							<div class="flex justify-between text-sm mb-2 opacity-80">
								<span>{$t('theater.setlists.avgPricePerTicket')}</span>
							</div>
							<div class="text-2xl font-bold text-yellow-400">
								{formatCurrency(detail.stats.avgPrice)}
							</div>
						</div>

						<div class="h-px bg-white/10"></div>

						<div>
							<div class="flex justify-between text-sm mb-2 opacity-80">
								<span>{$t('theater.setlists.attendanceRate')}</span>
							</div>
							<div class="flex items-end gap-2">
								<span class="text-3xl font-bold">{detail.watched.percentage}%</span>
								<span class="text-sm opacity-60 mb-1">
									{$t('theater.setlists.ofMax')}
								</span>
							</div>
							<!-- Progress bar -->
							<div class="w-full bg-white/10 h-1.5 rounded-full mt-3 overflow-hidden">
								<div
									class="h-full bg-yellow-400 rounded-full"
									style="width: {detail.watched.percentage}%"
								></div>
							</div>
						</div>
					</div>
				</div>

				<!-- Timeline Card -->
				<Timeline firstDate={detail.stats.firstDate} lastDate={detail.stats.lastDate} />
			</div>
		</div>
	</div>
{/if}
