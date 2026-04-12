<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { type SetlistDetailResponse } from '$lib/apis/setlists';

	import { ticketsStore, showToast } from '$lib/stores';
	import { setlistsStore, isSetlistDetailLoading } from '$lib/stores/theater';
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

	let { data: _data } = $props();

	const { t } = useTranslation();

	// Get setlistId from URL
	let setlistId = $derived($page.params.setlistId);

	// State from store
	let detail: SetlistDetailResponse | null = $state(null);
	let error = $derived($setlistsStore.detailError);
	let deleteId: string | null = $state(null);
	let isDeleting = $state(false);

	async function fetchDetail() {
		if (!setlistId) return;
		try {
			// Use store loadDetail which handles caching
			detail = await setlistsStore.loadDetail(setlistId);
		} catch (e) {
			// Error is handled by store
			showToast($t('theater.setlists.errorTitle') || 'Failed to load detail', 'error');
		}
	}

	async function confirmDelete() {
		if (!deleteId || isDeleting) return;

		const idToDelete = deleteId;
		isDeleting = true;

		try {
			// Use store action (handles API call internally)
			await ticketsStore.deleteTicket(idToDelete);

			// Re-fetch detail to update stats
			await fetchDetail();
			showToast($t('history.ticketDeleted'), 'success');
		} catch (e) {
			// Error is handled by ticketsStore internally
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

{#if $isSetlistDetailLoading}
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
		description={error ||
			$t('theater.setlists.errorDesc') ||
			'Something went wrong while fetching the setlist information.'}
		onRetry={fetchDetail}
	/>
{:else if detail}
	<div class="max-w-5xl mx-auto animate-fade-in pb-20">
		<!-- Immersive Hero Section -->
		<SetlistHero {detail} />

		<!-- Main Content Grid -->
		<div class="grid grid-cols-1 md:grid-cols-12 gap-6 md:gap-8">
			<!-- stats & History (Left Column on Desktop) -->
			<div class="md:col-span-8 contents md:flex md:flex-col md:gap-8">
				<div class="order-1">
					<SetlistStats stats={detail.stats} />
				</div>

				<div class="order-3 md:order-2">
					<div class="mt-4 md:mt-0">
						<div class="flex items-center justify-between mb-6">
							<h2
								class="text-xl md:text-2xl font-black text-gray-900 dark:text-white uppercase tracking-tight"
							>
								{$t('history.title')}
							</h2>
							<span
								class="text-xs md:text-sm text-gray-500 dark:text-gray-400 font-bold bg-gray-100 dark:bg-zinc-800 px-3 py-1 rounded-full border border-gray-200 dark:border-zinc-700"
							>
								{detail.tickets.length}
								<span class="hidden sm:inline">{$t('dashboard.theater.tickets')}</span>
							</span>
						</div>

						{#if detail.tickets.length === 0}
							<div
								class="flex flex-col items-center justify-center py-16 px-4 bg-gray-50 dark:bg-zinc-900/50 rounded-[2rem] border border-dashed border-gray-200 dark:border-zinc-800"
							>
								<div
									class="w-16 h-16 bg-gray-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mb-4"
								>
									<Ticket class="w-6 h-6 text-gray-400" />
								</div>
								<p class="font-bold text-gray-600 dark:text-gray-300">No tickets found</p>
								<p
									class="text-xs md:text-sm text-gray-500 dark:text-gray-400 text-center max-w-[250px] mt-1"
								>
									{$t('theater.setlists.notAttended')}
								</p>
							</div>
						{:else}
							<div class="space-y-3">
								{#each detail.tickets as ticket (ticket.ticketId)}
									<SetlistTicketItem {ticket} onclick={() => (deleteId = ticket.ticketId)} />
								{/each}
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- Summary & Timeline (Right Column on Desktop) -->
			<div class="md:col-span-4 contents md:flex md:flex-col md:gap-6">
				<!-- Quick Stats Card -->
				<div
					class="order-2 bg-gradient-to-br from-gray-900 to-gray-800 rounded-[2rem] p-6 md:p-8 text-white shadow-xl relative overflow-hidden"
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
							<div class="text-2xl md:text-3xl font-bold text-yellow-400 leading-none">
								{formatCurrency(detail.stats.avgPrice)}
							</div>
						</div>

						<div class="h-px bg-white/10"></div>

						<div>
							<div class="flex justify-between text-sm mb-2 opacity-80">
								<span>{$t('theater.setlists.attendanceRate')}</span>
							</div>
							<div class="flex items-end gap-2">
								<span class="text-3xl md:text-4xl font-black">{detail.watched.percentage}%</span>
								<span class="text-sm opacity-60 mb-1 font-medium">
									{$t('theater.setlists.ofMax')}
								</span>
							</div>
							<!-- Progress bar -->
							<div class="w-full bg-white/10 h-1.5 rounded-full mt-3 overflow-hidden">
								<div
									class="h-full bg-yellow-400 rounded-full shadow-[0_0_10px_rgba(250,204,21,0.5)]"
									style="width: {detail.watched.percentage}%"
								></div>
							</div>
						</div>
					</div>
				</div>

				<!-- Timeline Card -->
				<div class="order-2">
					<Timeline firstDate={detail.stats.firstDate} lastDate={detail.stats.lastDate} />
				</div>
			</div>
		</div>
	</div>
{/if}
