<script lang="ts">
	import { tickets, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { onMount } from 'svelte';
	import { Image as ImageIcon } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { PageHeader, EmptyState } from '$lib/components';
	import { Lightbox, MemoryFilters, MemoryCard, type FilterType } from '$lib/components/memories';
	import type { Ticket } from '$lib/types';

	const { t } = useTranslation();

	interface MemoryItem {
		uniqueId: string;
		type: 'TICKET' | '2SHOT';
		imageUrl: string;
		date: string;
		time: string;
		title: string;
		subtitle: string;
		notes?: string;
		originalTicket: Ticket;
	}

	let filter: FilterType = 'ALL';
	let selectedImage: MemoryItem | null = null;

	// Derived
	$: memoryItems = (() => {
		const items: MemoryItem[] = [];
		$tickets.forEach((ticket) => {
			// 1. Ticket Image
			if (ticket.imageUrl) {
				items.push({
					uniqueId: `${ticket._id}-ticket`,
					type: 'TICKET',
					imageUrl: ticket.imageUrl,
					date: ticket.event.date,
					time: ticket.event.time,
					title: ticket.event.title,
					subtitle: `${ticket.seat.section}-${ticket.seat.number}`,
					notes: ticket.notes,
					originalTicket: ticket
				});
			}
			// 2. 2-Shot Image
			if (ticket.two_shot?.imageUrl) {
				items.push({
					uniqueId: `${ticket._id}-2shot`,
					type: '2SHOT',
					imageUrl: ticket.two_shot.imageUrl,
					date: ticket.event.date,
					time: ticket.event.time,
					title: `2-Shot: ${ticket.two_shot.member_name}`,
					subtitle: ticket.two_shot.type, // Roulette / Birthday
					notes: ticket.notes,
					originalTicket: ticket
				});
			}
		});
		return items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
	})();

	$: filteredItems =
		filter === 'ALL' ? memoryItems : memoryItems.filter((item) => item.type === filter);

	// Scroll lock
	$: if (typeof document !== 'undefined') {
		document.body.style.overflow = selectedImage ? 'hidden' : 'unset';
	}

	/* Loading State */
	let mounted = false;

	onMount(() => {
		mounted = true;
	});

	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded);
</script>

<SEO title={$t('memories.title')} path="/memories" description={$t('seo.memories')} />

<!-- Lightbox -->
<Lightbox {selectedImage} onClose={() => (selectedImage = null)} />

<div class="max-w-7xl mx-auto p-4 pb-32 animate-fade-in">
	<!-- Header -->
	<div class="mb-8">
		<PageHeader
			icon={ImageIcon}
			title={$t('memories.title')}
			subtitle={$t('memories.subtitle')}
			theme="pink"
		>
			<div slot="actions">
				<MemoryFilters bind:filter />
			</div>
		</PageHeader>
	</div>

	<!-- Gallery Grid -->
	{#if isLoading}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 md:gap-10 px-4">
			<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
			{#each Array(8) as _unused, index}
				{@const rotation = (index % 5) - 2}
				<div class="relative" style={`transform: rotate(${rotation}deg)`}>
					<div
						class="bg-white dark:bg-zinc-900 p-3 pb-12 shadow-md border border-gray-100 dark:border-zinc-700 rounded-sm"
					>
						<div class="aspect-[4/5] w-full bg-gray-200 dark:bg-zinc-800 animate-pulse mb-4"></div>
						<div class="px-2">
							<div
								class="h-4 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse w-3/4 mx-auto mb-2"
							></div>
							<div
								class="h-3 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse w-1/2 mx-auto"
							></div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{:else if filteredItems.length === 0}
		<EmptyState
			icon={ImageIcon}
			title={$t('memories.noMemories')}
			description={$t('upload.subtitle')}
		/>
	{:else}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 md:gap-10 px-4">
			{#each filteredItems as item, index (item.uniqueId)}
				{@const rotation = (index % 5) - 2}
				<MemoryCard {item} {rotation} onClick={(i) => (selectedImage = i)} />
			{/each}
		</div>
	{/if}
</div>
