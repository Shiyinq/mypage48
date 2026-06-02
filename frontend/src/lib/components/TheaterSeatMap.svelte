<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SeatMapHeader from './theater/seatmap/SeatMapHeader.svelte';
	import SeatMapRows from './theater/seatmap/SeatMapRows.svelte';
	import SeatMapGrid from './theater/seatmap/SeatMapGrid.svelte';

	interface Props {
		rowStats: { counts: Record<string, number>; maxCount: number; uniqueVisited: number };
		seatStats: Record<string, number>;
		isLoading?: boolean;
		showSubtitle?: boolean;
		compact?: boolean;
	}

	let {
		rowStats,
		seatStats,
		isLoading = false,
		showSubtitle = true,
		compact = false
	}: Props = $props();

	const { t } = useTranslation();
	let mapView: 'ROWS' | 'SEATS' = $state('SEATS');

	const THEATER_ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'] as const;

	let maxSeatCount = $derived(seatStats ? Math.max(...Object.values(seatStats), 1) : 1);
</script>

<div class="glass-panel p-6 rounded-3xl">
	<SeatMapHeader {showSubtitle} {rowStats} totalRows={THEATER_ROWS.length} bind:mapView />

	<div class="w-full">
		<div class="w-full mx-auto px-1 sm:px-2">
			<div class="w-full">
				{#if mapView === 'ROWS'}
					<SeatMapRows rows={THEATER_ROWS} {rowStats} {isLoading} />
				{/if}

				{#if mapView === 'SEATS'}
					{#snippet stage()}
						<div
							class="w-full h-4 bg-gradient-to-b from-gray-200 dark:from-gray-700 to-white dark:to-gray-800 rounded-t-2xl relative shadow-sm border-t border-x border-gray-300 dark:border-gray-600"
						>
							<div class="absolute inset-0 bg-red-600 opacity-5 blur-xl"></div>
							<div
								class="absolute -top-6 -translate-x-1/2 bg-gray-100 dark:bg-gray-800 px-4 py-1 rounded-full border border-gray-200 dark:border-gray-700"
								style="left: calc((10 * var(--seat-w) + 1.5 * var(--aisle-w) + 22px) / (22 * var(--seat-w) + 3 * var(--aisle-w) + 48px) * 100%);"
							>
								<span
									class="text-[8px] sm:text-[10px] font-black tracking-[0.3em] text-gray-400 uppercase block text-center"
									>{t('dashboard.seatMap.stage')}</span
								>
							</div>
						</div>
					{/snippet}
					<SeatMapGrid
						rows={THEATER_ROWS}
						{seatStats}
						{maxSeatCount}
						{isLoading}
						{compact}
						{stage}
					/>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
</style>
