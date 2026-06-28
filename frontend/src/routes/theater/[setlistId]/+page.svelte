<script lang="ts">
	import { page } from '$app/stores';
	import { type SetlistDetailResponse } from '$lib/apis/setlists';

	import { ticketsStore, showToast } from '$lib/stores';
	import { setlistsStore } from '$lib/stores/theater.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Ticket } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { DeleteConfirmationModal } from '$lib/components/history';
	import { ErrorState } from '$lib/components';
	import { OptimizedImage } from '$lib/components/common';
	import SetlistHero from '$lib/components/theater/SetlistHero.svelte';
	import SetlistStats from '$lib/components/theater/SetlistStats.svelte';
	import SetlistTicketItem from '$lib/components/theater/SetlistTicketItem.svelte';
	import SetlistDetailSkeleton from '$lib/components/theater/SetlistDetailSkeleton.svelte';
	import { fade, slide } from 'svelte/transition';
	import { untrack } from 'svelte';

	// Import theater components and stores
	import { TheaterFilters } from '$lib/components/theater';
	import { dashboardFilter, dashboardStatsData } from '$lib/stores/dashboard.svelte';
	import { pageHeaderStore } from '$lib/stores/ui.svelte';
	import { goto } from '$app/navigation';
	import { AudioLines, PanelLeftClose, PanelLeft, Filter } from 'lucide-svelte';
	import { MONTHS } from '$lib/constants';
	import type { DashboardFilterState } from '$lib/stores/dashboard.svelte';

	let { data: _data } = $props();

	const { t } = useTranslation();

	// Get setlistId from URL
	let setlistId = $derived($page.params.setlistId);

	// State from store
	let detail: SetlistDetailResponse | null = $state(null);
	let error = $derived($setlistsStore.detailError);
	let isLoading = $state(true);
	let deleteId: string | null = $state(null);
	let isDeleting = $state(false);

	// Filter state
	let isFilterOpen = $state(false);
	const currentYear: number = new Date().getFullYear();
	let availableYears = $derived(dashboardStatsData.data?.available_years ?? [currentYear]);

	function getFilterLabel(filter: DashboardFilterState, tParams: (key: string) => string) {
		if (filter.isAllData) return tParams('common.allData');

		const startMonthKey = MONTHS[filter.startMonth].substring(0, 3).toLowerCase();
		const endMonthKey = MONTHS[filter.endMonth].substring(0, 3).toLowerCase();

		const startMonthStr = tParams(`time.monthsShort.${startMonthKey}`);
		const endMonthStr = tParams(`time.monthsShort.${endMonthKey}`);

		if (filter.startMonth === 0 && filter.endMonth === 11) {
			return `${filter.selectedYear}`;
		}

		return `${startMonthStr} - ${endMonthStr} ${filter.selectedYear}`;
	}
	let displayLabel = $derived(dashboardFilter ? getFilterLabel(dashboardFilter, t) : '');

	function clickOutside(node: HTMLElement) {
		const handleClick = (event: MouseEvent) => {
			const target = event.target as Element;
			if (node && !node.contains(target) && !target.closest('[data-filter-toggle="true"]')) {
				isFilterOpen = false;
			}
		};

		document.addEventListener('click', handleClick, true);

		return {
			destroy() {
				document.removeEventListener('click', handleClick, true);
			}
		};
	}

	async function fetchDetail(
		year?: number,
		startMonth?: number,
		endMonth?: number,
		isAllData?: boolean
	) {
		if (!setlistId) return;
		isLoading = true;
		try {
			const filter = {
				year: year ?? dashboardFilter.selectedYear,
				startMonth: startMonth ?? dashboardFilter.startMonth,
				endMonth: endMonth ?? dashboardFilter.endMonth,
				isAllData: isAllData ?? dashboardFilter.isAllData
			};

			// Use store loadDetail which handles caching
			detail = await setlistsStore.loadDetail(setlistId, filter);
		} catch {
			// Error is handled by store
			showToast(t('theater.setlists.errorTitle') || 'Failed to load detail', 'error');
		} finally {
			isLoading = false;
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
			showToast(t('history.ticketDeleted'), 'success');
		} catch {
			// Error is handled by ticketsStore internally
			showToast('Failed to delete ticket', 'error');
		} finally {
			isDeleting = false;
			deleteId = null;
		}
	}

	let isSidebarVisible = $state(false);
	let innerWidth = $state(0);
	let mainContentEl: HTMLElement | null = $state(null);

	function toggleSidebar() {
		isSidebarVisible = !isSidebarVisible;
	}

	// Mobile behavior
	$effect(() => {
		if (innerWidth < 768) {
			isSidebarVisible = false;
		} else {
			isSidebarVisible = true;
		}
	});

	let setlistItems = $derived(
		[...(setlistsStore.data || [])].sort((a, b) => b.watched.count - a.watched.count)
	);

	$effect(() => {
		// Track dependencies explicitly so the effect re-runs when filter changes
		const year = dashboardFilter?.selectedYear;
		const start = dashboardFilter?.startMonth;
		const end = dashboardFilter?.endMonth;
		const all = dashboardFilter?.isAllData;
		const id = setlistId;

		untrack(() => {
			if (id) {
				fetchDetail(year, start, end, all);
				if (mainContentEl) {
					mainContentEl.scrollTo({ top: 0, behavior: 'smooth' });
				}
				if (!setlistsStore.isLoading) {
					setlistsStore
						.load({
							year: year!,
							startMonth: start!,
							endMonth: end!,
							isAllData: all!
						})
						.catch(() => {});
				}
			}
		});
	});

	$effect(() => {
		if (detail) {
			pageHeaderStore.set({
				title: detail.title,
				subtitle: t('theater.subtitle') || 'Perjalanan teatermu',
				icon: AudioLines,
				theme: 'purple',
				showBackButton: true,
				handleBack: () => goto('/theater')
			});
		} else {
			pageHeaderStore.set({
				title: 'Setlists',
				icon: AudioLines,
				theme: 'purple',
				showBackButton: true,
				handleBack: () => goto('/theater')
			});
		}
		return () => pageHeaderStore.reset();
	});
</script>

<svelte:window bind:innerWidth />

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

<div
	class="h-[calc(100dvh-64px)] flex flex-col bg-slate-50/50 dark:bg-zinc-900/40 overflow-hidden relative"
>
	<div class="flex-1 flex flex-col md:flex-row overflow-hidden relative">
		<!-- Mobile Sidebar Backdrop -->
		{#if isSidebarVisible && innerWidth < 768}
			<button
				onclick={toggleSidebar}
				class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[55] md:hidden transition-opacity"
				aria-label="Close Sidebar"
				transition:fade={{ duration: 200 }}
			></button>
		{/if}

		<!-- Desktop Content Spacer -->
		{#if innerWidth >= 768}
			<div
				class="hidden md:block transition-all duration-300 ease-in-out shrink-0 overflow-hidden"
				style="width: {isSidebarVisible ? '256px' : '0px'}; opacity: {isSidebarVisible
					? '1'
					: '0'};"
			></div>
		{/if}

		<!-- Sidebar Container -->
		<aside
			class="fixed md:absolute top-0 bottom-0 left-0 z-[60] md:z-40 bg-white md:bg-white/80 dark:bg-zinc-900 md:dark:bg-zinc-900/80 backdrop-blur-md border-r border-gray-100 dark:border-white/5 shadow-2xl md:shadow-none w-full md:w-64 transition-transform duration-300 ease-in-out flex flex-col"
			class:-translate-x-full={!isSidebarVisible}
			class:translate-x-0={isSidebarVisible}
		>
			<!-- Sidebar Header -->
			<div
				class="relative p-4 border-b border-gray-100 dark:border-zinc-800/50 shrink-0 bg-white/95 dark:bg-zinc-900/95 backdrop-blur z-20"
			>
				<div class="flex items-center justify-between mb-3">
					<h2 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
						<div class="w-1.5 h-4 bg-purple-500 rounded-full"></div>
						{t('theater.setlists.section') || 'Setlists'}
					</h2>
					<button
						onclick={toggleSidebar}
						class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-zinc-300 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
						title={t('theater.closeSidebar') || 'Close sidebar'}
					>
						<PanelLeftClose class="w-4 h-4" />
					</button>
				</div>

				<div class="flex items-center justify-between gap-2 relative w-full">
					<span
						class="flex-1 text-[10px] sm:text-xs font-black text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-zinc-800 px-3 py-1.5 rounded-full border border-gray-200 dark:border-zinc-700 shadow-sm whitespace-nowrap text-center"
					>
						{displayLabel}
					</span>
					<button
						onclick={() => (isFilterOpen = !isFilterOpen)}
						data-filter-toggle="true"
						class={`flex-1 flex items-center justify-center gap-2 px-3 py-1.5 rounded-full font-bold text-xs shadow-sm border transition-all cursor-pointer ${
							isFilterOpen
								? 'bg-purple-50 dark:bg-purple-500/10 border-purple-200 dark:border-purple-500/30 text-purple-600 dark:text-purple-400'
								: 'bg-white dark:bg-zinc-800 border-gray-200 dark:border-zinc-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-zinc-700'
						}`}
					>
						<Filter class="w-3.5 h-3.5" />
						<span>{t('common.filters') || 'Filters'}</span>
					</button>

					{#if isFilterOpen}
						<div
							use:clickOutside
							transition:slide={{ duration: 200 }}
							class="absolute top-full left-0 mt-2 z-[7000] w-[calc(100vw-2rem)] md:w-[320px] max-w-[400px]"
						>
							<TheaterFilters
								bind:isAllData={dashboardFilter.isAllData}
								bind:selectedYear={dashboardFilter.selectedYear}
								bind:startMonth={dashboardFilter.startMonth}
								bind:endMonth={dashboardFilter.endMonth}
								{availableYears}
							/>
						</div>
					{/if}
				</div>
			</div>

			<!-- Setlist List -->
			<div
				class="flex-1 overflow-y-auto custom-scrollbar p-3 pt-2 pb-28"
				style="overscroll-behavior: contain;"
			>
				{#if setlistsStore.isLoading}
					<div class="space-y-3">
						{#each Array(5)}
							<div class="w-full h-20 rounded-xl bg-gray-100 dark:bg-zinc-800 animate-pulse"></div>
						{/each}
					</div>
				{:else}
					<div class="space-y-2">
						{#each setlistItems as s}
							{@const isActive = setlistId === String(s.setlistId)}
							<a
								href={`/theater/${encodeURIComponent(String(s.setlistId))}`}
								class="w-full cursor-pointer group flex items-start p-2.5 rounded-xl transition-all duration-200 border {isActive
									? 'bg-purple-50 dark:bg-purple-500/10 border-purple-200 dark:border-purple-500/30'
									: 'border-transparent hover:bg-slate-100 dark:hover:bg-zinc-800/50'}"
								onclick={() => {
									if (innerWidth < 768) isSidebarVisible = false;
								}}
							>
								<div class="flex-1 text-left">
									<h3
										class="font-semibold text-sm line-clamp-2 {isActive
											? 'text-purple-700 dark:text-purple-400'
											: 'text-gray-900 dark:text-gray-200 group-hover:text-purple-600 dark:group-hover:text-purple-400'}"
									>
										{s.title}
									</h3>
									<div class="flex items-center justify-end mt-1.5">
										<div
											class="flex items-center gap-1 text-[11px] font-bold {isActive
												? 'text-purple-600 dark:text-purple-400'
												: 'text-gray-500 dark:text-gray-400'} bg-white dark:bg-zinc-900 px-1.5 py-0.5 rounded-md border border-gray-100 dark:border-zinc-800 shadow-sm"
										>
											<Ticket class="w-3 h-3" />
											<span>{s.watched.count}x</span>
										</div>
									</div>
								</div>
							</a>
						{/each}
					</div>
				{/if}
			</div>
		</aside>

		<!-- Floating Toggle Sidebar Button -->
		{#if !isSidebarVisible}
			<div
				class="absolute top-3 left-0 z-30 transition-all duration-300"
				transition:fade={{ duration: 200 }}
			>
				<button
					onclick={toggleSidebar}
					class="flex items-center justify-center w-8 h-10 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-md shadow-lg border-y border-r border-gray-200 dark:border-white/10 rounded-r-xl text-gray-400 hover:text-purple-500 transition-all hover:w-10 active:scale-95 cursor-pointer"
					title={t('common.openSidebar')}
				>
					<PanelLeft class="w-4 h-4 ml-1" />
				</button>
			</div>
		{/if}

		<!-- Main Content Area -->
		<main
			bind:this={mainContentEl}
			class="flex-1 overflow-y-auto relative h-full custom-scrollbar bg-white dark:bg-zinc-900"
			style="overscroll-behavior: contain;"
		>
			<div class="pb-28 md:pb-12 max-w-none w-full mx-auto">
				{#if isLoading}
					<SetlistDetailSkeleton />
				{:else if error}
					<ErrorState
						title={t('theater.setlists.errorTitle') || 'Failed to load detail'}
						description={error ||
							t('theater.setlists.errorDesc') ||
							'Something went wrong while fetching the setlist information.'}
						onRetry={fetchDetail}
					/>
				{:else if detail}
					<div class="bg-white dark:bg-zinc-900 overflow-hidden">
						<!-- Immersive Hero Section -->
						<SetlistHero {detail} />

						<!-- Main Content Grid -->
						<div class="p-6 sm:p-8 lg:p-10 max-w-5xl mx-auto flex flex-col gap-8">
							<div class="w-full">
								<SetlistStats stats={detail.stats} watched={detail.watched} />
							</div>

							<div
								class="w-full grid grid-cols-1 {detail.twoShots?.length
									? 'md:grid-cols-12'
									: ''} gap-8"
							>
								<div
									class="mt-4 md:mt-0 order-2 md:order-1 {detail.twoShots?.length
										? 'md:col-span-8 lg:col-span-8'
										: 'w-full'}"
								>
									<div class="flex items-center justify-between mb-6">
										<h2
											class="text-xl md:text-2xl font-black text-gray-900 dark:text-white uppercase tracking-tight"
										>
											{t('history.title')}
										</h2>
										<span
											class="text-xs md:text-sm text-gray-500 dark:text-gray-400 font-bold bg-gray-100 dark:bg-zinc-800 px-3 py-1 rounded-full border border-gray-200 dark:border-zinc-700"
										>
											{detail.tickets.length}
											<span class="hidden sm:inline">{t('dashboard.theater.tickets')}</span>
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
											<p class="font-bold text-gray-600 dark:text-gray-300">
												{t('theater.setlists.noTicketsFound')}
											</p>
											<p
												class="text-xs md:text-sm text-gray-500 dark:text-gray-400 text-center max-w-[250px] mt-1"
											>
												{t('theater.setlists.notAttended')}
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

								{#if detail.twoShots?.length > 0}
									<div class="md:col-span-4 lg:col-span-4 mt-4 md:mt-0 order-1 md:order-2">
										<div class="flex items-center justify-between mb-6">
											<h2
												class="text-xl md:text-2xl font-black text-gray-900 dark:text-white uppercase tracking-tight"
											>
												{t('memories.twoShots') || '2-Shot'}
											</h2>
											<span
												class="text-xs md:text-sm text-gray-500 dark:text-gray-400 font-bold bg-gray-100 dark:bg-zinc-800 px-3 py-1 rounded-full border border-gray-200 dark:border-zinc-700"
											>
												{detail.stats.total2Shot}
												{t('top2shot.total') || 'Total'}
											</span>
										</div>
										<div class="space-y-3">
											{#each detail.twoShots as item}
												<div
													class="flex items-center gap-4 bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 p-3 rounded-2xl hover:shadow-md transition-all"
												>
													{#if item.imageUrl}
														<div class="w-12 h-12 rounded-xl overflow-hidden shrink-0">
															<OptimizedImage
																src={item.imageUrl}
																srcMedium={item.imageUrl_medium}
																srcSmall={item.imageUrl_small}
																blurHash={item.blurHash}
																alt={item.name}
																sizes="48px"
																class="w-full h-full object-cover"
															/>
														</div>
													{:else}
														<div
															class="w-12 h-12 rounded-xl bg-gray-100 dark:bg-zinc-800 flex items-center justify-center shrink-0"
														>
															<span class="text-gray-400 text-sm font-bold"
																>{item.name.charAt(0)}</span
															>
														</div>
													{/if}
													<div class="flex-1 min-w-0">
														<div class="font-bold text-gray-900 dark:text-white truncate">
															{item.name}
														</div>
														<div class="text-sm font-semibold text-pink-500">{item.count}x</div>
													</div>
												</div>
											{/each}
										</div>
									</div>
								{/if}
							</div>
						</div>
					</div>
				{/if}
			</div>
		</main>
	</div>
</div>
