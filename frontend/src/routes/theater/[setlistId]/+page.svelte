<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { setlistsApi, type SetlistDetailResponse } from '$lib/apis/setlists';
	import { ticketsApi } from '$lib/apis/tickets';
	import { tickets, showToast } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		ArrowLeft,
		Trash2,
		Calendar,
		DollarSign,
		MapPin,
		Trophy,
		Clock,
		Ticket
	} from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { DeleteConfirmationModal } from '$lib/components/history';
	import { ErrorState } from '$lib/components';

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

	// Helpers
	function formatDate(dateStr: string): string {
		if (!dateStr) return '-';
		try {
			return new Date(dateStr).toLocaleDateString('id-ID', {
				day: 'numeric',
				month: 'long',
				year: 'numeric'
			});
		} catch {
			return dateStr;
		}
	}

	function formatPrice(price: number): string {
		return new Intl.NumberFormat('id-ID', {
			style: 'currency',
			currency: 'IDR',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(price);
	}

	function getGradeColor(percentage: number) {
		if (percentage >= 100) return 'text-purple-500';
		if (percentage >= 75) return 'text-blue-500';
		if (percentage >= 50) return 'text-green-500';
		if (percentage >= 25) return 'text-yellow-500';
		return 'text-gray-400';
	}
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
		<div
			class="relative w-full min-h-[400px] rounded-[2.5rem] overflow-hidden shadow-2xl mb-8 group flex flex-col justify-end"
		>
			<!-- Background Image with Parallax-like effect -->
			<div class="absolute inset-0">
				<img
					src={detail.imageUrl}
					alt={detail.title}
					class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-105"
				/>
				<!-- Gradient Mesh Overlay -->
				<div
					class="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/60 to-transparent opacity-90"
				></div>
				<div
					class="absolute inset-0 bg-gradient-to-r from-gray-900/80 via-transparent to-transparent"
				></div>
			</div>

			<!-- Content Container -->
			<div class="relative z-10 p-8 md:p-12 w-full">
				<div class="flex items-start justify-between gap-6 mb-8 md:mb-12">
					<div class="space-y-4 max-w-2xl">
						<!-- Badges -->
						<div class="flex flex-wrap gap-2 animate-slide-up" style="animation-delay: 100ms;">
							{#if detail.watched.isMostWatched}
								<span
									class="px-3 py-1 bg-yellow-400/20 backdrop-blur-md border border-yellow-400/30 text-yellow-300 text-xs font-bold rounded-full flex items-center gap-1.5 shadow-lg shadow-yellow-900/20"
								>
									<Trophy class="w-3.5 h-3.5" />
									{$t('shows.top')}
								</span>
							{/if}
							<span
								class="px-3 py-1 bg-white/10 backdrop-blur-md border border-white/20 text-white/90 text-xs font-medium rounded-full"
							>
								{detail.type === 'setlist'
									? $t('theater.setlists.section')
									: $t('theater.setlists.events')}
							</span>
						</div>

						<!-- Title -->
						<div class="animate-slide-up" style="animation-delay: 200ms;">
							<h1
								class="text-4xl md:text-5xl lg:text-6xl font-black text-white tracking-tight leading-[1.1] mb-2 drop-shadow-lg"
							>
								{detail.title}
							</h1>
							{#if detail.titleJapanese}
								<p class="text-xl text-white/50 font-medium tracking-wide">
									{detail.titleJapanese}
								</p>
							{/if}
						</div>

						<!-- Description -->
						<p
							class="text-gray-300 text-sm md:text-base leading-relaxed max-w-xl animate-slide-up"
							style="animation-delay: 300ms;"
						>
							{detail.description}
						</p>
					</div>

					<!-- Hero Stats (Attendance) -->
					<div class="hidden md:block animate-slide-up" style="animation-delay: 400ms;">
						<div
							class="bg-white/10 backdrop-blur-xl border border-white/20 p-6 rounded-2xl flex flex-col items-center min-w-[140px]"
						>
							<span class="text-5xl font-black text-white tracking-tighter mb-1">
								{detail.watched.count}
							</span>
							<span class="text-xs font-bold text-white/60 uppercase tracking-widest text-center">
								{@html $t('shows.performancesAttended').replace(' ', '<br/>')}
							</span>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Main Content Grid -->
		<div class="grid grid-cols-1 md:grid-cols-12 gap-8">
			<!-- Left Column: Stats & Meta -->
			<div class="md:col-span-8 space-y-6">
				<!-- Primary Stats Grid -->
				<div class="grid grid-cols-2 gap-4">
					<div
						class="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 p-5 rounded-2xl hover:shadow-lg hover:shadow-purple-500/5 hover:-translate-y-1 transition-all duration-300 group"
					>
						<div class="flex items-start justify-between mb-4">
							<div
								class="p-2.5 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 rounded-xl group-hover:scale-110 transition-transform"
							>
								<MapPin class="w-5 h-5" />
							</div>
							<span
								class="text-xs font-bold text-purple-600/50 dark:text-purple-400/50 uppercase tracking-wider"
								>{$t('shows.topRow')}</span
							>
						</div>
						<div class="text-3xl font-bold text-gray-900 dark:text-white">
							{detail.stats.topRow || '-'}
						</div>
						<div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
							{$t('shows.mostFrequentedRow') || 'Most frequented row'}
						</div>
					</div>

					<div
						class="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 p-5 rounded-2xl hover:shadow-lg hover:shadow-green-500/5 hover:-translate-y-1 transition-all duration-300 group"
					>
						<div class="flex items-start justify-between mb-4">
							<div
								class="p-2.5 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 rounded-xl group-hover:scale-110 transition-transform"
							>
								<DollarSign class="w-5 h-5" />
							</div>
							<span
								class="text-xs font-bold text-green-600/50 dark:text-green-400/50 uppercase tracking-wider"
								>{$t('dashboard.theater.totalExpenses')}</span
							>
						</div>
						<div class="text-3xl font-bold text-gray-900 dark:text-white truncate">
							{formatPrice(detail.stats.totalSpent)}
						</div>
						<div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
							{$t('shows.investmentInMemories') || 'Investment in memories'}
						</div>
					</div>
				</div>

				<!-- Ticket History -->
				<div class="mt-8">
					<div class="flex items-center justify-between mb-6">
						<h2 class="text-xl font-bold text-gray-900 dark:text-white">{$t('history.title')}</h2>
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
								<div
									class="group relative bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 p-1 overflow-hidden transition-all hover:shadow-md hover:border-purple-200 dark:hover:border-purple-900/30"
								>
									<!-- Visual accent on left -->
									<div
										class="absolute left-0 top-0 bottom-0 w-1.5 bg-gradient-to-b from-purple-500 to-indigo-600 rounded-l-full"
									></div>

									<div class="flex items-center gap-4 p-4 pl-6">
										<!-- Date Box -->
										<div
											class="flex-shrink-0 flex flex-col items-center justify-center w-14 h-14 bg-gray-50 dark:bg-zinc-800 rounded-xl border border-gray-100 dark:border-zinc-700"
										>
											<span
												class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase leading-none"
											>
												{new Date(ticket.event.date).toLocaleDateString('id-ID', {
													month: 'short'
												})}
											</span>
											<span class="text-xl font-black text-gray-900 dark:text-white leading-tight">
												{new Date(ticket.event.date).getDate()}
											</span>
										</div>

										<!-- Ticket Info -->
										<div class="flex-1 min-w-0">
											<div class="flex items-center gap-2 mb-1">
												<span
													class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 text-xs font-bold border border-purple-100 dark:border-purple-900/30"
												>
													<Clock class="w-3 h-3" />
													{ticket.event.time}
												</span>
												<span class="text-xs text-gray-400 font-medium">
													{new Date(ticket.event.date).getFullYear()}
												</span>
											</div>
											<div class="flex items-baseline gap-2">
												<span class="text-sm text-gray-500 dark:text-gray-400 font-medium"
													>Seat</span
												>
												<span
													class="text-lg font-bold text-gray-900 dark:text-white font-mono tracking-tight"
												>
													{ticket.seat.section}-{ticket.seat.number}
												</span>
											</div>
										</div>

										<!-- Price & Check -->
										<div class="text-right hidden sm:block">
											<div class="text-sm font-bold text-gray-900 dark:text-white">
												{formatPrice(ticket.price)}
											</div>
											{#if ticket.notes}
												<div class="text-xs text-gray-400 italic max-w-[150px] truncate">
													"{ticket.notes}"
												</div>
											{/if}
										</div>

										<!-- Delete Action -->
										<button
											on:click|stopPropagation={() => (deleteId = ticket.ticketId)}
											class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl opacity-0 group-hover:opacity-100 transition-all transform scale-90 group-hover:scale-100 cursor-pointer"
										>
											<Trash2 class="w-4.5 h-4.5" />
										</button>
									</div>
								</div>
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
								{formatPrice(detail.stats.avgPrice)}
							</div>
						</div>

						<div class="h-px bg-white/10"></div>

						<div>
							<div class="flex justify-between text-sm mb-2 opacity-80">
								<span>{$t('theater.setlists.attendanceRate')}</span>
							</div>
							<div class="flex items-end gap-2">
								<span class="text-3xl font-bold">{detail.watched.percentage}%</span>
								<span class="text-sm opacity-60 mb-1">{$t('theater.setlists.ofMax')}</span>
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
				<div
					class="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 rounded-3xl p-6"
				>
					<h3 class="font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
						<Calendar class="w-5 h-5 text-purple-600" />
						{$t('theater.setlists.timeline')}
					</h3>

					<div
						class="relative pl-6 space-y-8 border-l-2 border-dashed border-gray-200 dark:border-zinc-700 ml-2"
					>
						<!-- First -->
						<div class="relative">
							<div
								class="absolute -left-[31px] w-4 h-4 rounded-full bg-green-100 dark:bg-green-900/30 border-2 border-green-500"
							></div>
							<p
								class="text-xs font-bold text-green-600 dark:text-green-400 uppercase tracking-wider mb-1"
							>
								{$t('theater.setlists.firstShow')}
							</p>
							<p class="font-bold text-gray-900 dark:text-white">
								{formatDate(detail.stats.firstDate || '')}
							</p>
						</div>

						<!-- Last -->
						<div class="relative">
							<div
								class="absolute -left-[31px] w-4 h-4 rounded-full bg-blue-100 dark:bg-blue-900/30 border-2 border-blue-500"
							></div>
							<p
								class="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider mb-1"
							>
								{$t('theater.setlists.latestShow')}
							</p>
							<p class="font-bold text-gray-900 dark:text-white">
								{formatDate(detail.stats.lastDate || '')}
							</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	/* Custom animations */
	@keyframes slide-up {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.animate-slide-up {
		animation: slide-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
		opacity: 0;
	}
</style>
