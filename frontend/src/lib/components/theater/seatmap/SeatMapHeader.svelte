<script lang="ts">
	import { MapPin, StretchHorizontal, Grid3x3 } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		showSubtitle?: boolean;
		rowStats: { uniqueVisited: number };
		totalRows: number;
		mapView: 'ROWS' | 'SEATS';
	}

	let { showSubtitle = true, rowStats, totalRows, mapView = $bindable() }: Props = $props();

	const { t } = useTranslation();
</script>

<div class="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
	<div>
		<h3 class="text-xl font-bold text-themed">
			{$t('dashboard.seatMap.title')}
		</h3>
		{#if showSubtitle}
			<p class="text-xs text-gray-400">{$t('dashboard.seatMap.subtitle')}</p>
		{/if}
	</div>
	<div class="flex items-center gap-2 w-full sm:w-auto justify-between sm:justify-end">
		<div
			class="h-9 bg-red-50 dark:bg-red-500/20 text-red-600 dark:text-red-400 px-3 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm border border-red-100 dark:border-red-500/20"
		>
			<MapPin class="w-3.5 h-3.5" />
			<span>{rowStats.uniqueVisited}/{totalRows} {$t('dashboard.seatMap.rowsCollected')}</span>
		</div>
		<div class="h-9 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg flex items-center gap-1">
			<button
				onclick={() => (mapView = 'ROWS')}
				class={`h-full aspect-square flex items-center justify-center rounded-md transition-all cursor-pointer ${mapView === 'ROWS' ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
			>
				<StretchHorizontal class="w-4 h-4" />
			</button>
			<button
				onclick={() => (mapView = 'SEATS')}
				class={`h-full aspect-square flex items-center justify-center rounded-md transition-all cursor-pointer ${mapView === 'SEATS' ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
			>
				<Grid3x3 class="w-4 h-4" />
			</button>
		</div>
	</div>
</div>
