<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SeatMapHeader from './theater/seatmap/SeatMapHeader.svelte';
	import SeatMapRows from './theater/seatmap/SeatMapRows.svelte';
	import SeatMapGrid from './theater/seatmap/SeatMapGrid.svelte';

	export let rowStats: { counts: Record<string, number>; maxCount: number; uniqueVisited: number };
	export let seatStats: Record<string, number>;
	export let isLoading: boolean = false;
	export let showSubtitle: boolean = true;
	export let compact: boolean = false;

	const { t } = useTranslation();
	let mapView: 'ROWS' | 'SEATS' = 'SEATS';

	const THEATER_ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'] as const;

	const SEAT_LAYOUT = {
		A: {
			start: 3,
			seats: 22,
			groups: [
				[3, 6],
				[7, 12],
				[13, 18],
				[19, 24]
			]
		},
		B: {
			start: 3,
			seats: 23,
			groups: [
				[3, 6],
				[7, 12],
				[13, 18],
				[19, 25]
			]
		},
		C: {
			start: 2,
			seats: 25,
			groups: [
				[2, 6],
				[7, 12],
				[13, 18],
				[19, 26]
			]
		},
		D: {
			start: 2,
			seats: 26,
			groups: [
				[2, 6],
				[7, 12],
				[13, 18],
				[19, 27]
			]
		},
		E: {
			start: 2,
			seats: 26,
			groups: [
				[2, 6],
				[7, 12],
				[13, 18],
				[19, 27]
			]
		},
		F: {
			start: 1,
			seats: 28,
			groups: [
				[1, 6],
				[7, 12],
				[13, 18],
				[19, 28]
			]
		},
		G: {
			start: 1,
			seats: 28,
			groups: [
				[1, 6],
				[7, 12],
				[13, 18],
				[19, 28]
			]
		},
		H: {
			start: 1,
			seats: 27,
			groups: [
				[1, 6],
				[7, 12],
				[13, 18],
				[19, 27]
			]
		},
		I: {
			start: 2,
			seats: 26,
			groups: [
				[2, 6],
				[7, 12],
				[13, 18],
				[19, 27]
			]
		},
		J: {
			start: 2,
			seats: 26,
			groups: [
				[2, 6],
				[7, 12],
				[13, 18],
				[19, 27]
			]
		}
	} as const;

	$: maxSeatCount = seatStats ? Math.max(...Object.values(seatStats), 1) : 1;
</script>

<div class="glass-panel p-6 rounded-3xl">
	<SeatMapHeader {showSubtitle} {rowStats} totalRows={THEATER_ROWS.length} bind:mapView />

	<div class="w-full">
		<div class="w-full mx-auto px-1 sm:px-2">
			<div class="w-full">
				{#if mapView === 'SEATS'}
					<div
						class="w-3/4 mx-auto mt-8 md:mt-0 h-4 bg-gradient-to-b from-gray-200 dark:from-gray-700 to-white dark:to-gray-800 rounded-t-2xl mb-1 relative shadow-sm border-t border-x border-gray-300 dark:border-gray-600"
						style="transform: translateX(-24px)"
					>
						<div class="absolute inset-0 bg-red-600 opacity-5 blur-xl"></div>
						<div
							class="absolute -top-6 left-1/2 bg-gray-100 dark:bg-gray-800 px-4 py-1 rounded-full border border-gray-200 dark:border-gray-700 stage-pill"
							class:is-compact={compact}
						>
							<span
								class="text-[8px] sm:text-[10px] font-black tracking-[0.3em] text-gray-400 uppercase block text-center"
								>{$t('dashboard.seatMap.stage')}</span
							>
						</div>
					</div>
				{/if}

				{#if mapView === 'ROWS'}
					<SeatMapRows rows={THEATER_ROWS} {rowStats} {isLoading} />
				{/if}

				{#if mapView === 'SEATS'}
					<SeatMapGrid
						rows={THEATER_ROWS}
						seatLayout={SEAT_LAYOUT}
						{seatStats}
						{maxSeatCount}
						{isLoading}
						{compact}
					/>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.stage-pill {
		--stage-offset: 31px; /* Default Desktop Offset */
		transform: translateX(calc(-50% - var(--stage-offset, 0px)));
		white-space: nowrap;
	}

	.stage-pill.is-compact {
		--stage-offset: 11px; /* Compact Mode Offset */
	}

	@media (max-width: 767px) {
		.stage-pill,
		.stage-pill.is-compact {
			--stage-offset: 0px; /* Center on Mobile */
		}
	}
</style>
