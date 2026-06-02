<script lang="ts">
	import { MapPin, Grid3x3 } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		rowStats: { counts: Record<string, number>; maxCount: number; uniqueVisited: number };
		seatStats: Record<string, number>;
		isLoading?: boolean;
	}

	let { rowStats, seatStats, isLoading = false }: Props = $props();

	const { t } = useTranslation();
	let mapView: 'ROWS' | 'SEATS' = $state('SEATS');

	const THEATER_ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];

	const ROW_COUNTS: Record<string, number> = {
		A: 22,
		B: 23,
		C: 25,
		D: 26,
		E: 26,
		F: 28,
		G: 28,
		H: 27,
		I: 26,
		J: 26
	};
	const LEFT_COUNTS: Record<string, number> = {
		A: 4,
		B: 5,
		C: 6,
		D: 7,
		E: 7,
		F: 8,
		G: 8,
		H: 8,
		I: 8,
		J: 8
	};

	function getGridColumn(rowChar: string, seatNum: number): number {
		const leftCount = LEFT_COUNTS[rowChar];
		if (!leftCount) return 2; // fallback

		if (seatNum <= leftCount) {
			return 9 - leftCount + seatNum + 1;
		} else if (seatNum <= leftCount + 6) {
			return 11 + (seatNum - leftCount - 1) + 1;
		} else if (seatNum <= leftCount + 12) {
			return 18 + (seatNum - leftCount - 7) + 1;
		} else {
			return 25 + (seatNum - leftCount - 13) + 1;
		}
	}

	let maxSeatCount = $derived(seatStats ? Math.max(...Object.values(seatStats), 1) : 1);
</script>

<div
	class="bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] p-5 sm:p-6 relative shadow-2xl shadow-red-500/10 dark:shadow-red-950/40 transition-all duration-300 hover:shadow-red-500/15"
>
	<div class="relative z-10">
		<div class="flex flex-wrap items-center justify-between mb-8 gap-3">
			<h3
				class="font-black text-sm uppercase tracking-widest text-gray-400 flex items-center gap-2"
			>
				<MapPin class="w-4 h-4" />
				{t('dashboard.seatMap.title')}
			</h3>

			<div class="flex items-center gap-2 sm:gap-3 ml-auto">
				<div
					class="bg-white/50 dark:bg-black/20 backdrop-blur-sm border border-white/20 px-2 sm:px-3 py-1.5 rounded-full text-[10px] sm:text-xs font-bold text-gray-600 dark:text-gray-300"
				>
					<span class="text-red-500 dark:text-red-400 font-black"
						>{rowStats.uniqueVisited}/{THEATER_ROWS.length}</span
					>
					{t('dashboard.seatMap.rowsCollected')}
				</div>

				<div class="bg-gray-100/50 dark:bg-gray-800/50 p-1 rounded-full flex items-center gap-1">
					<button
						onclick={() => (mapView = 'ROWS')}
						class={`w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center rounded-full transition-all cursor-pointer ${mapView === 'ROWS' ? 'bg-white dark:bg-zinc-700 text-gray-900 dark:text-white shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
					>
						<p class="font-black text-[10px]">R</p>
					</button>
					<button
						onclick={() => (mapView = 'SEATS')}
						class={`w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center rounded-full transition-all cursor-pointer ${mapView === 'SEATS' ? 'bg-white dark:bg-zinc-700 text-gray-900 dark:text-white shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
					>
						<Grid3x3 class="w-4 h-4" />
					</button>
				</div>
			</div>
		</div>

		<div class="w-full">
			{#if mapView === 'ROWS'}
				<!-- Rows View -->
				{#if isLoading}
					<div class="grid grid-cols-2 gap-4 animate-pulse">
						<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
						{#each Array(10)}
							<div class="h-10 bg-gray-200 dark:bg-gray-800 rounded-xl"></div>
						{/each}
					</div>
				{:else}
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3">
						{#each THEATER_ROWS as row}
							{@const count = rowStats.counts[row] || 0}
							{@const intensity = rowStats.maxCount > 0 ? count / rowStats.maxCount : 0}
							{@const hasData = count > 0}

							<div class="flex items-center gap-2 group">
								<div
									class={`w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-lg text-xs font-black transition-all ${!hasData ? 'bg-gray-100 dark:bg-zinc-800/50 text-gray-300 dark:text-zinc-700' : ''}`}
									style={hasData
										? `background-color: rgba(220, 38, 38, ${0.2 + intensity * 0.8}); color: ${intensity > 0.4 ? 'white' : '#dc2626'};`
										: ''}
								>
									{row}
								</div>
								<div
									class="flex-1 h-8 rounded-lg relative overflow-hidden bg-gray-50 dark:bg-zinc-800/30"
								>
									<!-- Bar -->
									<div
										class="absolute inset-y-0 left-0 transition-all duration-1000"
										style={`width: ${intensity * 100}%; background-color: rgba(220, 38, 38, ${0.1 + intensity * 0.9});`}
									></div>
									<!-- Label -->
									<div
										class="absolute inset-0 flex items-center justify-between px-3 text-xs font-medium"
									>
										<span
											class={`transition-colors duration-300 ${hasData && intensity <= 0.3 ? 'text-gray-600 dark:text-gray-300' : ''} ${!hasData ? 'text-gray-400 dark:text-zinc-500' : ''}`}
											style={hasData && intensity > 0.3
												? 'color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.3)'
												: ''}>{t('dashboard.seatMap.row')} {row}</span
										>
										<span
											class={`font-bold transition-colors duration-300 ${hasData && intensity <= 0.85 ? 'text-red-600 dark:text-red-400' : ''} ${!hasData ? 'text-gray-300 dark:text-zinc-700' : ''}`}
											style={hasData && intensity > 0.85
												? 'color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.3)'
												: ''}
										>
											{count}
										</span>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			{:else if mapView === 'SEATS'}
				<!-- Seats View -->
				{#if isLoading}
					<div class="h-64 flex items-center justify-center text-gray-400">Loading map...</div>
				{:else}
					<div class="w-full overflow-x-auto pb-4 hide-scrollbar">
						<div class="seat-map-grid w-full max-w-full mx-auto">
							<!-- Stage Pill -->
							<div
								style="grid-column: 12 / 25; grid-row: 1; display: flex; justify-content: center; margin-bottom: 1.5rem;"
							>
								<div
									class="px-8 py-1 bg-gray-100 dark:bg-zinc-800 rounded-full text-[10px] uppercase font-black tracking-[0.3em] text-gray-300 dark:text-zinc-600 h-fit"
								>
									{t('dashboard.seatMap.stage')}
								</div>
							</div>

							{#each THEATER_ROWS as row, rowIndex}
								<div class="row-label" style="grid-column: 1; grid-row: {rowIndex + 2};">{row}</div>

								<!-- Seats -->
								{#each Array(ROW_COUNTS[row] || 0) as _, i}
									{@const seatNum = i + 1}
									{@const gridCol = getGridColumn(row, seatNum)}
									{@const seatKey = `${row}-${seatNum}`}
									{@const count = seatStats[seatKey] || 0}
									{@const hasVisit = count > 0}
									{@const intensity = hasVisit ? Math.max(0.2, count / maxSeatCount) : 0}

									<div
										class="map-seat {hasVisit ? 'active' : ''} group/seat relative cursor-default"
										style="grid-column: {gridCol}; grid-row: {rowIndex + 2}; {hasVisit
											? `--intensity: ${intensity}; background-color: rgba(220, 38, 38, ${intensity});`
											: ''}"
									>
										{row}-{seatNum}
										<div
											class="absolute opacity-0 group-hover/seat:opacity-100 left-1/2 -translate-x-1/2 px-2 py-1 bg-gray-900 text-white text-[10px] font-bold rounded shadow-xl whitespace-nowrap pointer-events-none z-[100] transition-opacity duration-200 {row ===
											'A'
												? 'top-full mt-1.5'
												: 'bottom-full mb-1.5'}"
										>
											{row}-{seatNum} ({count}x)
										</div>
									</div>
								{/each}
							{/each}
						</div>
					</div>
				{/if}
			{/if}
		</div>

		<!-- Footer Legend -->
		<div
			class="mt-6 flex items-center justify-center gap-6 text-[10px] text-gray-400 font-bold uppercase tracking-wide"
		>
			<div class="flex items-center gap-2">
				<div class="w-3 h-3 rounded bg-gray-100 dark:bg-zinc-800"></div>
				<span>No Visit</span>
			</div>
			<div class="flex items-center gap-2">
				<div class="w-3 h-3 rounded bg-red-500/20"></div>
				<span>visited</span>
			</div>
			<div class="flex items-center gap-2">
				<div class="w-3 h-3 rounded bg-red-600 shadow-sm"></div>
				<span>Top Seat</span>
			</div>
		</div>
	</div>
</div>

<style>
	.hide-scrollbar::-webkit-scrollbar {
		display: none;
	}
	.hide-scrollbar {
		-ms-overflow-style: none; /* IE and Edge */
		scrollbar-width: none; /* Firefox */
	}

	.seat-map-grid {
		--seat-w: 20px;
		--aisle-w: 8px;
		display: grid;
		grid-template-columns:
			auto repeat(9, var(--seat-w)) var(--aisle-w) repeat(6, var(--seat-w))
			var(--aisle-w) repeat(6, var(--seat-w)) var(--aisle-w) repeat(10, var(--seat-w));
		gap: 2px 2px;
	}

	.row-label {
		width: 10px;
		font-size: 7px;
		font-weight: 900;
		color: #9ca3af;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-right: 1px;
	}

	.map-seat {
		width: 20px;
		height: 16px;
		border-radius: 3px;
		background-color: #f3f4f6;
		flex-shrink: 0;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 7px;
		font-weight: 700;
		color: #d1d5db; /* Default text color for empty seats */
		border: 1px solid transparent;
	}

	:global(.dark) .map-seat {
		background-color: #1f2937;
		color: #4b5563;
	}

	/* Visited Styling */
	.map-seat.active {
		box-shadow: 0 1px 2px -1px rgba(220, 38, 38, 0.1);
		color: white !important; /* Text is white when visited */
		border-color: rgba(255, 255, 255, 0.2);
	}

	@media (min-width: 768px) {
		.seat-map-grid {
			--seat-w: 24px;
			--aisle-w: 10px;
		}
		.row-label {
			width: 14px;
			font-size: 8px;
			margin-right: 2px;
		}
		.map-seat {
			width: 24px;
			height: 18px;
			font-size: 8px;
		}
	}
</style>
