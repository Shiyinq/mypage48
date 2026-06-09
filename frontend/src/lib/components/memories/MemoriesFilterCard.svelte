<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		Calendar,
		RotateCcw,
		Grid,
		Ticket as TicketIcon,
		Camera,
		Search,
		ChevronDown
	} from 'lucide-svelte';
	import type { MemoryFilters, MemoryFilterType } from '$lib/types';
	import { ticketsStore } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { onMount } from 'svelte';

	let { filters = $bindable(), onClear = () => {} } = $props<{
		filters: MemoryFilters;
		onClear?: () => void;
	}>();

	const { t } = useTranslation();

	let availableTitles: string[] = $state([]);
	let isLoadingTitles = $state(false);

	onMount(async () => {
		try {
			isLoadingTitles = true;
			availableTitles = await ticketsStore.getAvailableTitles();
		} catch (e) {
			logger.error('Failed to load ticket titles', e, { context: 'MemoriesFilterCard' });
		} finally {
			isLoadingTitles = false;
		}
	});

	function setType(type: MemoryFilterType) {
		filters.type = type;
	}

	function handleClear() {
		filters.type = 'ALL';
		filters.startDate = undefined;
		filters.endDate = undefined;
		filters.title = undefined;
		filters.isFavorite = undefined;
		onClear();
	}
</script>

<div
	class="bg-white dark:bg-zinc-900 rounded-xl shadow-lg border border-gray-100 dark:border-white/10 p-4 w-full md:w-[400px]"
>
	<!-- Setlist Selection -->
	<div class="mb-5 w-full">
		<label
			for="memories-setlist-select"
			class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2"
		>
			{t('common.setlist') || 'Setlist'}
		</label>
		<div class="relative group">
			<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none">
				{#if isLoadingTitles}
					<div
						class="w-4 h-4 border-2 border-gray-300 border-t-pink-500 rounded-full animate-spin"
					></div>
				{:else}
					<Search class="w-4 h-4" />
				{/if}
			</div>

			<select
				id="memories-setlist-select"
				bind:value={filters.title}
				class="w-full pl-10 pr-10 py-2.5 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg text-sm font-medium text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent shadow-sm transition-all appearance-none cursor-pointer"
			>
				<option value={undefined}>{t('common.allSetlists') || 'Semua Setlist'}</option>
				{#each availableTitles as title}
					<option value={title}>{title}</option>
				{/each}
			</select>

			<ChevronDown
				class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
			/>
		</div>
	</div>

	<!-- Type selection -->
	<div class="mb-5">
		<span class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2"
			>{t('memories.photoType') || 'Jenis Foto'}</span
		>
		<div
			class="flex bg-gray-50 dark:bg-zinc-800/50 p-1 rounded-lg border border-gray-100 dark:border-zinc-700"
		>
			<button
				onclick={() => setType('ALL')}
				class={`flex-1 py-2 text-xs font-bold rounded-md flex items-center justify-center gap-1.5 transition-all cursor-pointer ${!filters.type || filters.type === 'ALL' ? 'bg-pink-500 text-white shadow-sm' : 'text-gray-500 hover:bg-gray-200 dark:hover:bg-zinc-700'}`}
			>
				<Grid class="w-3.5 h-3.5" />
				{t('memories.allPhotos') || 'Semua'}
			</button>
			<button
				onclick={() => setType('TICKET')}
				class={`flex-1 py-2 text-xs font-bold rounded-md flex items-center justify-center gap-1.5 transition-all cursor-pointer ${filters.type === 'TICKET' ? 'bg-red-500 text-white shadow-sm' : 'text-gray-500 hover:bg-gray-200 dark:hover:bg-zinc-700'}`}
			>
				<TicketIcon class="w-3.5 h-3.5" />
				{t('memories.tickets') || 'Tiket'}
			</button>
			<button
				onclick={() => setType('2SHOT')}
				class={`flex-1 py-2 text-xs font-bold rounded-md flex items-center justify-center gap-1.5 transition-all cursor-pointer ${filters.type === '2SHOT' ? 'bg-purple-500 text-white shadow-sm' : 'text-gray-500 hover:bg-gray-200 dark:hover:bg-zinc-700'}`}
			>
				<Camera class="w-3.5 h-3.5" />
				{t('memories.twoShots') || '2-Shot'}
			</button>
		</div>
	</div>

	<!-- Favorite Toggle -->
	<div class="mb-5">
		<span class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2"
			>{t('common.favorite') || 'Favorite'}</span
		>
		<div class="flex items-center gap-3">
			<div
				onclick={() => (filters.isFavorite = !filters.isFavorite)}
				onkeydown={(e) => e.key === 'Enter' && (filters.isFavorite = !filters.isFavorite)}
				role="switch"
				aria-checked={!!filters.isFavorite}
				tabindex="0"
				class={'relative w-10 h-6 rounded-full transition-colors cursor-pointer ' +
					(filters.isFavorite ? 'bg-red-500' : 'bg-gray-300 dark:bg-zinc-600')}
			>
				<div
					class={'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ' +
						(filters.isFavorite ? 'translate-x-4' : '')}
				></div>
			</div>
		</div>
	</div>

	<!-- Date Range -->
	<div class="mb-4">
		<span class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2"
			>{t('common.dateRange') || 'Rentang Tanggal'}</span
		>
		<div class="flex flex-col sm:flex-row items-center gap-2">
			<!-- Start Date -->
			<div
				class="flex items-center bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg shadow-sm overflow-hidden flex-1 w-full px-3 py-2 gap-2 transition-all focus-within:ring-2 focus-within:ring-pink-500 focus-within:border-transparent"
			>
				<span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider shrink-0"
					>{t('common.fromShort') || 'Dari'}</span
				>
				<div class="relative w-full flex items-center">
					<input
						type="date"
						bind:value={filters.startDate}
						class="w-full bg-transparent text-xs font-medium text-gray-700 dark:text-gray-300 focus:outline-none cursor-pointer color-scheme-dark z-10"
					/>
					<Calendar class="absolute right-0 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
				</div>
			</div>

			<!-- End Date -->
			<div
				class="flex items-center bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg shadow-sm overflow-hidden flex-1 w-full px-3 py-2 gap-2 transition-all focus-within:ring-2 focus-within:ring-pink-500 focus-within:border-transparent"
			>
				<span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider shrink-0"
					>{t('common.toShort') || 'Ke'}</span
				>
				<div class="relative w-full flex items-center">
					<input
						type="date"
						bind:value={filters.endDate}
						class="w-full bg-transparent text-xs font-medium text-gray-700 dark:text-gray-300 focus:outline-none cursor-pointer color-scheme-dark z-10"
					/>
					<Calendar class="absolute right-0 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
				</div>
			</div>
		</div>
	</div>

	<!-- Clear Filter Button -->
	<div class="pt-3 border-t border-gray-100 dark:border-white/5">
		<button
			onclick={handleClear}
			class="flex items-center justify-center gap-2 w-full py-2 px-4 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 bg-gray-50 hover:bg-gray-100 dark:bg-zinc-800/50 dark:hover:bg-zinc-800 transition-colors border border-gray-200 dark:border-zinc-700 cursor-pointer"
		>
			<RotateCcw class="w-4 h-4" />
			{t('common.clearFilters') || 'Hapus Filter'}
		</button>
	</div>
</div>

<style>
	input[type='date'].color-scheme-dark {
		color-scheme: light dark;
	}

	input[type='date']::-webkit-calendar-picker-indicator {
		cursor: pointer;
		opacity: 0;
		width: 100%;
		height: 100%;
		position: absolute;
		right: 0;
		top: 0;
		margin: 0;
		padding: 0;
	}
</style>
