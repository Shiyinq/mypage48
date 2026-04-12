<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { Ticket } from '$lib/types';
	import { CalendarDays, MapPin, PanelLeftClose } from 'lucide-svelte';
	import { formatDate } from '$lib/i18n';
	import HistoryFilter from '$lib/components/history/HistoryFilter.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';

	interface Props {
		tickets?: Ticket[];
		selectedId?: string | null;
		filters?: import('$lib/types').TicketFilters;
		loading?: boolean;
		hasMore?: boolean;
		totalData?: number;
		onselect?: (id: string) => void;
		onloadMore?: () => void;
		onfilterChange?: (filters: import('$lib/types').TicketFilters) => void;
		ontoggleSidebar?: () => void;
	}

	let {
		tickets = [],
		selectedId = null,
		filters = {},
		loading = false,
		hasMore = false,
		totalData = 0,
		onselect,
		onloadMore,
		onfilterChange,
		ontoggleSidebar
	}: Props = $props();

	const { t } = useTranslation();

	function handleSelect(id: string) {
		onselect?.(id);
	}
</script>

<div class="h-full flex flex-col bg-slate-50/30 dark:bg-zinc-900/50 overscroll-none">
	<div
		class="hidden md:flex p-3 border-b border-gray-100 dark:border-white/5 sticky top-0 bg-white/95 dark:bg-zinc-950/95 backdrop-blur z-10 flex-shrink-0 justify-between items-center"
	>
		<h2 class="font-black text-gray-900 dark:text-white flex items-center gap-2 text-sm pr-2">
			<CalendarDays class="w-4 h-4 text-red-500" />
			{$t('journal.title')}
		</h2>
		<div class="flex items-center gap-1">
			<div
				class={`text-[10px] bg-gray-100 dark:bg-zinc-800 text-gray-500 dark:text-gray-400 font-bold px-2 py-0.5 rounded-full flex items-center gap-1.5 transition-all ${loading ? 'opacity-70 ring-1 ring-red-500/10' : ''}`}
			>
				{#if loading}
					<div
						class="w-2 h-2 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin"
					></div>
				{/if}
				{totalData || tickets.length}
				{$t('shows.unit')}
			</div>
			<button
				onclick={() => ontoggleSidebar?.()}
				class="hidden md:flex p-1.5 text-gray-400 hover:text-gray-900 hover:bg-gray-100 dark:hover:bg-zinc-800 dark:hover:text-white rounded-lg transition-colors cursor-pointer shrink-0"
				title="Hide Sidebar"
			>
				<PanelLeftClose class="w-5 h-5" />
			</button>
		</div>
	</div>

	<div
		class="px-3 py-2 border-b border-gray-100 dark:border-white/5 bg-white/50 dark:bg-zinc-950/50 relative z-20"
	>
		<HistoryFilter
			{filters}
			showViewToggle={false}
			isSidebar={true}
			onfilterChange={(newFilters) => onfilterChange?.(newFilters)}
		/>
	</div>

	<div class="flex-1 overflow-y-auto px-2 py-3 custom-scrollbar relative overscroll-contain">
		{#if loading && tickets.length === 0}
			<div class="space-y-2">
				{#each Array(5) as _}
					<div
						class="animate-pulse bg-white/50 dark:bg-zinc-800/50 h-24 rounded-xl border border-gray-100 dark:border-white/5 w-full"
					></div>
				{/each}
			</div>
		{:else if tickets.length === 0}
			<div class="h-full flex flex-col items-center justify-center p-6 text-center text-gray-500">
				<CalendarDays class="w-8 h-8 mb-3 opacity-20" />
				<p class="text-sm font-medium">{$t('journal.noRecords')}</p>
				<p class="text-xs mt-1 text-gray-400">{$t('journal.noRecordsDesc')}</p>
			</div>
		{:else}
			<div class="space-y-1 flex flex-col pb-10">
				{#each tickets as ticket}
					{@const isSelected = selectedId === ticket._id}
					<button
						onclick={() => handleSelect(ticket._id)}
						class={`w-full text-left px-3 py-2.5 mx-0 rounded-lg transition-all duration-200 border cursor-pointer flex flex-col group
							${
								isSelected
									? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-900/30 relative after:absolute after:left-0 after:top-1.5 after:bottom-1.5 after:w-1 after:bg-red-500 after:rounded-r'
									: 'bg-white dark:bg-zinc-900/80 border-transparent hover:border-gray-200 dark:hover:border-zinc-800 hover:bg-white dark:hover:bg-zinc-800'
							}`}
					>
						<div class="flex items-center justify-between mb-1">
							<div
								class="text-[9px] font-bold tracking-wider uppercase {isSelected
									? 'text-red-500'
									: 'text-gray-400 dark:text-gray-500'}"
							>
								{$formatDate(ticket.event.date, {
									day: 'numeric',
									month: 'short',
									year: 'numeric'
								})}
							</div>
							<div
								class="flex items-center gap-0.5 font-mono text-[9px] font-bold {isSelected
									? 'text-red-500/80'
									: 'text-gray-400'}"
							>
								<MapPin class="w-2.5 h-2.5" />
								{ticket.seat.section}{ticket.seat.number ? `-${ticket.seat.number}` : ''}
							</div>
						</div>

						<div class="flex items-start justify-between gap-2">
							<h3
								class={`text-xs font-bold leading-tight line-clamp-2 transition-colors flex-1 ${isSelected ? 'text-gray-900 dark:text-white' : 'text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white'}`}
							>
								{ticket.event.title}
							</h3>
							{#if ticket.notes}
								<span
									class="mt-1 w-1.5 h-1.5 rounded-full bg-green-500 shrink-0 shadow-[0_0_8px_rgba(34,197,94,0.4)]"
									title="Journal Written"
								></span>
							{/if}
						</div>
					</button>
				{/each}

				{#if hasMore}
					<div
						use:infiniteScroll
						onintersect={() => onloadMore?.()}
						class="w-full py-4 flex justify-center"
					>
						{#if loading}
							<span
								class="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin"
							></span>
						{/if}
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>
