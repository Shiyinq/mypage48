<script lang="ts">
	import { MapPin, AlignJustify, Grid3X3 } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let rowStats: { counts: Record<string, number>; maxCount: number; uniqueVisited: number };
	export let seatStats: Record<string, number>;
	export let isLoading: boolean = false;
	export let showSubtitle: boolean = true;
	export let compact: boolean = false;

	const { t } = useTranslation();
	let mapView: 'ROWS' | 'SEATS' = 'SEATS';

	const THEATER_ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];

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

	function getLayout(row: string) {
		return SEAT_LAYOUT[row as keyof typeof SEAT_LAYOUT];
	}
</script>

<div class="glass-panel p-6 rounded-3xl">
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
				<span
					>{rowStats.uniqueVisited}/{THEATER_ROWS.length}
					{$t('dashboard.seatMap.rowsCollected')}</span
				>
			</div>
			<div class="h-9 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg flex items-center gap-1">
				<button
					on:click={() => (mapView = 'ROWS')}
					class={`h-full aspect-square flex items-center justify-center rounded-md transition-all cursor-pointer ${mapView === 'ROWS' ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
				>
					<AlignJustify class="w-4 h-4" />
				</button>
				<button
					on:click={() => (mapView = 'SEATS')}
					class={`h-full aspect-square flex items-center justify-center rounded-md transition-all cursor-pointer ${mapView === 'SEATS' ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
				>
					<Grid3X3 class="w-4 h-4" />
				</button>
			</div>
		</div>
	</div>

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

				<!-- MAP VIEW: ROWS -->
				{#if mapView === 'ROWS'}
					{#if isLoading}
						<!-- Skeleton Loading for Rows -->
						<div
							class="grid grid-cols-2 gap-x-6 md:gap-x-16 gap-y-4 max-w-4xl mx-auto mt-2 pt-4 pb-4 px-4"
						>
							<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
							{#each THEATER_ROWS as row}
								<div class="flex items-center gap-3">
									<div
										class="w-9 h-9 md:w-10 md:h-10 flex-shrink-0 rounded-xl bg-gray-200 dark:bg-zinc-700 animate-pulse"
									></div>
									<div
										class="flex-1 h-9 md:h-10 rounded-xl bg-gray-200 dark:bg-zinc-700 animate-pulse"
									></div>
								</div>
							{/each}
						</div>
					{:else}
						<div
							class="grid grid-cols-2 gap-x-6 md:gap-x-16 gap-y-4 max-w-4xl mx-auto mt-2 pt-4 pb-4 px-4"
						>
							{#each THEATER_ROWS as row}
								{@const count = rowStats.counts[row] || 0}
								{@const intensity = rowStats.maxCount > 0 ? count / rowStats.maxCount : 0}
								{@const hasData = count > 0}
								<div class="flex items-center gap-3 group">
									<div
										class={`w-9 h-9 md:w-10 md:h-10 flex-shrink-0 flex items-center justify-center rounded-xl text-sm font-bold transition-all duration-300 shadow-sm ${!hasData ? 'bg-gray-100 dark:bg-gray-800 text-gray-400' : ''}`}
										style={hasData
											? `background-color: rgba(220, 38, 38, ${0.2 + intensity * 0.8}); color: ${intensity > 0.4 ? 'white' : '#dc2626'}; box-shadow: 0 4px 12px -2px rgba(220, 38, 38, ${intensity * 0.5})`
											: ''}
									>
										{row}
									</div>
									<div
										class={`flex-1 h-9 md:h-10 rounded-xl flex items-center px-3 md:px-4 relative overflow-hidden transition-all duration-300 ${hasData ? 'bg-white dark:bg-gray-800 border border-red-100 dark:border-red-500/30 shadow-sm' : 'bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700 border-dashed'}`}
									>
										{#if hasData}
											<div
												class="absolute left-0 top-0 bottom-0 transition-all duration-1000"
												style={`width: ${intensity * 100}%; background-color: rgba(220, 38, 38, ${0.1 + intensity * 0.9});`}
											>
												<div
													class="absolute right-0 top-0 bottom-0 w-[1px] bg-red-400 opacity-20"
												></div>
											</div>
										{/if}
										<div class="relative z-10 w-full flex justify-between items-center px-1">
											<span
												class={`text-[10px] md:text-xs font-bold uppercase tracking-wide transition-colors duration-300 ${hasData && intensity <= 0.3 ? 'text-gray-600 dark:text-gray-300' : ''} ${!hasData ? 'text-gray-300 dark:text-gray-600' : ''}`}
												style={hasData && intensity > 0.3
													? 'color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.3)'
													: ''}>{$t('dashboard.seatMap.row')} {row}</span
											>
											<span
												class={`text-base md:text-lg font-black transition-colors duration-300 ${hasData && intensity <= 0.85 ? 'text-red-600 dark:text-red-400' : ''} ${!hasData ? 'text-gray-300 dark:text-gray-600' : ''}`}
												style={hasData && intensity > 0.85
													? 'color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.3)'
													: ''}>{count}</span
											>
										</div>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				{/if}

				<!-- MAP VIEW: SEATS -->
				{#if mapView === 'SEATS'}
					{#if isLoading}
						<!-- Skeleton Loading for Seats -->
						<!-- Skeleton Loading for Seats -->
						<div class="w-full overflow-x-auto pt-8 pb-4">
							<div class="seat-map-grid min-w-[700px] md:min-w-0 {compact ? 'is-compact' : ''}">
								{#each THEATER_ROWS as row}
									{@const layout = getLayout(row)}
									<div class="grid-row">
										<!-- Row Label -->
										<div class="row-label">
											<div
												class="w-3/4 h-3/4 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"
											></div>
										</div>

										<!-- Group 1 (columns 1-6) -->
										{#each [1, 2, 3, 4, 5, 6] as col}
											{@const isValidSeat =
												col >= layout.groups[0][0] && col <= layout.groups[0][1]}
											{#if isValidSeat}
												<div
													class="map-seat bg-gray-200 dark:bg-zinc-700 animate-pulse border-none"
												></div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}

										<div class="aisle-gap"></div>

										<!-- Group 2 (columns 7-12) -->
										{#each [7, 8, 9, 10, 11, 12] as col}
											{@const isValidSeat =
												col >= layout.groups[1][0] && col <= layout.groups[1][1]}
											{#if isValidSeat}
												<div
													class="map-seat bg-gray-200 dark:bg-zinc-700 animate-pulse border-none"
												></div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}

										<div class="aisle-gap"></div>

										<!-- Group 3 (columns 13-18) -->
										{#each [13, 14, 15, 16, 17, 18] as col}
											{@const isValidSeat =
												col >= layout.groups[2][0] && col <= layout.groups[2][1]}
											{#if isValidSeat}
												<div
													class="map-seat bg-gray-200 dark:bg-zinc-700 animate-pulse border-none"
												></div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}

										<div class="aisle-gap"></div>

										<!-- Group 4 (columns 19-28) -->
										{#each [19, 20, 21, 22, 23, 24, 25, 26, 27, 28] as col}
											{@const isValidSeat =
												col >= layout.groups[3][0] && col <= layout.groups[3][1]}
											{#if isValidSeat}
												<div
													class="map-seat bg-gray-200 dark:bg-zinc-700 animate-pulse border-none"
												></div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}
									</div>
								{/each}
							</div>
						</div>
					{:else}
						<div class="w-full overflow-x-auto pt-8 pb-4">
							<div class="seat-map-grid min-w-[700px] md:min-w-0 {compact ? 'is-compact' : ''}">
								{#each THEATER_ROWS as row}
									{@const layout = getLayout(row)}
									<div class="grid-row">
										<!-- Row Label -->
										<div class="row-label">{row}</div>

										<!-- Group 1 (columns 1-6) -->
										{#each [1, 2, 3, 4, 5, 6] as col}
											{@const seatNum = col - layout.start + 1}
											{@const isValidSeat =
												col >= layout.groups[0][0] && col <= layout.groups[0][1]}
											{@const seatKey = `${row}-${seatNum}`}
											{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
											{@const hasVisit = count > 0}
											{@const intensity = hasVisit ? Math.max(0.25, count / maxSeatCount) : 0}

											{#if isValidSeat}
												<div
													class="map-seat {hasVisit ? 'active' : ''}"
													style={hasVisit ? `--intensity: ${intensity}` : ''}
													data-title="{seatKey}: {count}x"
												>
													<span class="seat-id">{seatKey}</span>
													{#if hasVisit}<span class="seat-count">{count}x</span>{/if}
												</div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}

										<!-- Aisle 1 -->
										<div class="aisle-gap"></div>

										<!-- Group 2 (columns 7-12) -->
										{#each [7, 8, 9, 10, 11, 12] as col}
											{@const seatNum = col - layout.start + 1}
											{@const isValidSeat =
												col >= layout.groups[1][0] && col <= layout.groups[1][1]}
											{@const seatKey = `${row}-${seatNum}`}
											{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
											{@const hasVisit = count > 0}
											{@const intensity = hasVisit ? Math.max(0.25, count / maxSeatCount) : 0}

											{#if isValidSeat}
												<div
													class="map-seat {hasVisit ? 'active' : ''}"
													style={hasVisit ? `--intensity: ${intensity}` : ''}
													data-title="{seatKey}: {count}x"
												>
													<span class="seat-id">{seatKey}</span>
													{#if hasVisit}<span class="seat-count">{count}x</span>{/if}
												</div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}

										<!-- Aisle 2 -->
										<div class="aisle-gap"></div>

										<!-- Group 3 (columns 13-18) -->
										{#each [13, 14, 15, 16, 17, 18] as col}
											{@const seatNum = col - layout.start + 1}
											{@const isValidSeat =
												col >= layout.groups[2][0] && col <= layout.groups[2][1]}
											{@const seatKey = `${row}-${seatNum}`}
											{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
											{@const hasVisit = count > 0}
											{@const intensity = hasVisit ? Math.max(0.25, count / maxSeatCount) : 0}

											{#if isValidSeat}
												<div
													class="map-seat {hasVisit ? 'active' : ''}"
													style={hasVisit ? `--intensity: ${intensity}` : ''}
													data-title="{seatKey}: {count}x"
												>
													<span class="seat-id">{seatKey}</span>
													{#if hasVisit}<span class="seat-count">{count}x</span>{/if}
												</div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}

										<!-- Aisle 3 -->
										<div class="aisle-gap"></div>

										<!-- Group 4 (columns 19-28) -->
										{#each [19, 20, 21, 22, 23, 24, 25, 26, 27, 28] as col}
											{@const seatNum = col - layout.start + 1}
											{@const isValidSeat =
												col >= layout.groups[3][0] && col <= layout.groups[3][1]}
											{@const seatKey = `${row}-${seatNum}`}
											{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
											{@const hasVisit = count > 0}
											{@const intensity = hasVisit ? Math.max(0.25, count / maxSeatCount) : 0}

											{#if isValidSeat}
												<div
													class="map-seat {hasVisit ? 'active' : ''}"
													style={hasVisit ? `--intensity: ${intensity}` : ''}
													data-title="{seatKey}: {count}x"
												>
													<span class="seat-id">{seatKey}</span>
													{#if hasVisit}<span class="seat-count">{count}x</span>{/if}
												</div>
											{:else}
												<div class="empty-cell"></div>
											{/if}
										{/each}
									</div>
								{/each}
							</div>
						</div>
					{/if}
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	/* Responsive Seat Map Styles */
	.seat-map-grid {
		display: flex;
		flex-direction: column;
		gap: 2px;
		width: fit-content;
		margin: 0 auto;
	}

	.stage-pill {
		--stage-offset: 31px; /* Default Desktop Offset */
		transform: translateX(calc(-50% - var(--stage-offset, 0px)));
		white-space: nowrap;
	}

	.stage-pill.is-compact {
		--stage-offset: 11px; /* Compact Mode Offset */
	}

	.stage-pill.is-row-mode {
		--stage-offset: 0px; /* Center for Row Mode */
	}

	@media (max-width: 767px) {
		.stage-pill,
		.stage-pill.is-compact,
		.stage-pill.is-row-mode {
			--stage-offset: 0px; /* Center on Mobile */
		}
	}

	.grid-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0; /* Gaps handled by flex children spacing if needed, or minimal */
		width: 100%;
	}

	.row-label {
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 10px;
		font-weight: 700;
		color: #664d57;
		background: #fff5f8;
		border-radius: 4px;
		width: 20px;
		height: 24px;
		flex-shrink: 0;
		margin-right: 6px;
		/* margin-left removed to prevent scroll */
	}

	:global(.dark) .row-label {
		color: #f9a8d4;
		background: rgba(227, 0, 15, 0.2);
	}

	.empty-cell {
		width: 24px;
		height: 24px;
		flex-shrink: 0;
		visibility: hidden;
		margin: 0 1px;
	}

	.aisle-gap {
		width: 8px;
		flex-shrink: 0;
	}

	.map-seat {
		display: flex;
		width: 24px;
		height: 24px;
		flex-shrink: 0;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		border-radius: 3px;
		border: 1px solid #e0e0e0;
		background-color: #f5f5f5;
		cursor: default;
		transition: transform 0.15s ease;
		position: relative;
		margin: 0 1px;
	}

	:global(.dark) .map-seat {
		border-color: #374151;
		background-color: #1f2937;
	}

	.map-seat .seat-id {
		font-size: 8px; /* Use Clamp or small font */
		font-weight: 700;
		color: #999;
		line-height: 1;
		white-space: nowrap;
		overflow: hidden;
	}

	:global(.dark) .map-seat .seat-id {
		color: #9ca3af;
	}

	.map-seat .seat-count {
		font-size: 7px;
		font-weight: 600;
		color: #999;
		line-height: 1;
		display: none;
	}

	:global(.dark) .map-seat .seat-count {
		color: #9ca3af;
	}

	.map-seat.active {
		background-color: rgba(227, 0, 15, var(--intensity, 0.5));
		border-color: rgba(200, 0, 13, var(--intensity, 0.6));
	}

	.map-seat.active .seat-id {
		color: #ffffff;
		text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
	}

	.map-seat.active .seat-count {
		display: block;
		color: rgba(255, 255, 255, 0.9);
	}

	/* Tooltip */
	.map-seat::after {
		content: attr(data-title);
		position: absolute;
		bottom: 100%;
		left: 50%;
		transform: translateX(-50%) translateY(-5px);
		background: #1f2937;
		color: #fff;
		padding: 4px 6px;
		border-radius: 4px;
		font-size: 10px;
		white-space: nowrap;
		opacity: 0;
		pointer-events: none;
		transition: opacity 0.15s;
		z-index: 20;
	}

	.map-seat:hover::after {
		opacity: 1;
	}

	@media (min-width: 768px) {
		/* Default Mode (Dashboard) - Large sizes */
		.row-label {
			width: 24px;
			height: 32px;
			font-size: 11px;
			margin-right: 8px;
		}

		.empty-cell {
			width: 32px;
			height: 32px;
		}

		.aisle-gap {
			width: 12px;
		}

		.map-seat {
			width: 32px;
			height: 32px;
			border-radius: 5px;
		}

		.grid-row {
			gap: 2px;
		}

		.map-seat .seat-id {
			font-size: 8px;
		}

		.map-seat .seat-count {
			font-size: 7px;
		}

		/* Compact Mode (Public Profile) - Small sizes to fit ~816px available width */
		/* Calculation: 28*22 + 3*6 + 18 + 27 = 679px (Safe) */
		.is-compact .row-label {
			width: 18px;
			height: 22px;
			font-size: 9px;
			margin-right: 6px;
		}

		.is-compact .empty-cell {
			width: 22px;
			height: 22px;
		}

		.is-compact .aisle-gap {
			width: 6px;
		}

		.is-compact .map-seat {
			width: 22px;
			height: 22px;
			border-radius: 3px;
		}

		.is-compact .grid-row {
			gap: 1px;
		}

		.is-compact .map-seat .seat-id {
			font-size: 5px;
		}

		.is-compact .map-seat .seat-count {
			font-size: 4px; /* Tiny font for tiny seats */
		}
	}

	/* Hide text on very small screens if needed, or scale down */
	@container (max-width: 500px) {
		.seat-id {
			display: none;
		}
	}

	/* Mobile Adjustments (Default is mobile-first, but explicit overrides just in case) */
	@media (max-width: 767px) {
		.map-seat .seat-id {
			font-size: 7px;
		}
		.map-seat .seat-count {
			font-size: 6px;
		}
		.grid-row {
			gap: 1px;
		}
	}
</style>
