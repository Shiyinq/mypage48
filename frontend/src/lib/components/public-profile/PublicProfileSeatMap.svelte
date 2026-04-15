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

	let maxSeatCount = $derived(seatStats ? Math.max(...Object.values(seatStats), 1) : 1);

	function getLayout(row: string) {
		return SEAT_LAYOUT[row as keyof typeof SEAT_LAYOUT];
	}
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
			{#if mapView === 'SEATS'}
				<div class="w-full flex justify-center mb-6">
					<div
						class="px-8 py-1 bg-gray-100 dark:bg-zinc-800 rounded-full text-[10px] uppercase font-black tracking-[0.3em] text-gray-300 dark:text-zinc-600"
					>
						Stage
					</div>
				</div>
			{/if}

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
					<div class="grid grid-cols-2 gap-x-4 gap-y-3">
						{#each THEATER_ROWS as row}
							{@const count = rowStats.counts[row] || 0}
							{@const intensity = rowStats.maxCount > 0 ? count / rowStats.maxCount : 0}
							{@const hasData = count > 0}

							<div class="flex items-center gap-2 group">
								<div
									class={`w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-lg text-xs font-black transition-all ${!hasData ? 'bg-gray-100 dark:bg-zinc-800/50 text-gray-300 dark:text-zinc-700' : ''}`}
									style={hasData
										? `background-color: rgba(220, 38, 38, ${0.1 + intensity * 0.9}); color: ${intensity > 0.5 ? 'white' : '#dc2626'};`
										: ''}
								>
									{row}
								</div>
								<div
									class="flex-1 h-8 rounded-lg relative overflow-hidden bg-gray-50 dark:bg-zinc-800/30"
								>
									<!-- Bar -->
									<div
										class="absolute inset-y-0 left-0 bg-red-500/10 transition-all duration-1000"
										style={`width: ${intensity * 100}%`}
									></div>
									<!-- Label -->
									<div
										class="absolute inset-0 flex items-center justify-between px-3 text-xs font-medium"
									>
										<span class="text-gray-400 dark:text-zinc-500">Row {row}</span>
										<span
											class="font-bold {hasData
												? 'text-gray-900 dark:text-white'
												: 'text-gray-300 dark:text-zinc-700'}"
										>
											{count}
										</span>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			{:else}
				<!-- Seats View -->
				{#if isLoading}
					<div class="h-64 flex items-center justify-center text-gray-400">Loading map...</div>
				{:else}
					<div class="w-full overflow-x-auto pb-4 hide-scrollbar">
						<div class="seat-map-grid w-full max-w-full mx-auto">
							{#each THEATER_ROWS as row}
								{@const layout = getLayout(row)}
								<div class="grid-row">
									<div class="row-label">{row}</div>

									<!-- Group 1 -->
									{#each [1, 2, 3, 4, 5, 6] as col}
										{@const seatNum = col - layout.start + 1}
										{@const isValidSeat = col >= layout.groups[0][0] && col <= layout.groups[0][1]}
										{@const seatKey = `${row}-${seatNum}`}
										{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
										{@const hasVisit = count > 0}
										{@const intensity = hasVisit ? Math.max(0.2, count / maxSeatCount) : 0}

										{#if isValidSeat}
											<div
												class="map-seat {hasVisit
													? 'active'
													: ''} group/seat relative cursor-default"
												style={hasVisit
													? `--intensity: ${intensity}; background-color: rgba(220, 38, 38, ${intensity});`
													: ''}
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
										{:else}
											<div class="empty-cell"></div>
										{/if}
									{/each}

									<div class="aisle-gap"></div>

									<!-- Group 2 -->
									{#each [7, 8, 9, 10, 11, 12] as col}
										{@const seatNum = col - layout.start + 1}
										{@const isValidSeat = col >= layout.groups[1][0] && col <= layout.groups[1][1]}
										{@const seatKey = `${row}-${seatNum}`}
										{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
										{@const hasVisit = count > 0}
										{@const intensity = hasVisit ? Math.max(0.2, count / maxSeatCount) : 0}

										{#if isValidSeat}
											<div
												class="map-seat {hasVisit
													? 'active'
													: ''} group/seat relative cursor-default"
												style={hasVisit
													? `--intensity: ${intensity}; background-color: rgba(220, 38, 38, ${intensity});`
													: ''}
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
										{:else}
											<div class="empty-cell"></div>
										{/if}
									{/each}

									<div class="aisle-gap"></div>

									<!-- Group 3 -->
									{#each [13, 14, 15, 16, 17, 18] as col}
										{@const seatNum = col - layout.start + 1}
										{@const isValidSeat = col >= layout.groups[2][0] && col <= layout.groups[2][1]}
										{@const seatKey = `${row}-${seatNum}`}
										{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
										{@const hasVisit = count > 0}
										{@const intensity = hasVisit ? Math.max(0.2, count / maxSeatCount) : 0}

										{#if isValidSeat}
											<div
												class="map-seat {hasVisit
													? 'active'
													: ''} group/seat relative cursor-default"
												style={hasVisit
													? `--intensity: ${intensity}; background-color: rgba(220, 38, 38, ${intensity});`
													: ''}
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
										{:else}
											<div class="empty-cell"></div>
										{/if}
									{/each}

									<div class="aisle-gap"></div>

									<!-- Group 4 -->
									{#each [19, 20, 21, 22, 23, 24, 25, 26, 27, 28] as col}
										{@const seatNum = col - layout.start + 1}
										{@const isValidSeat = col >= layout.groups[3][0] && col <= layout.groups[3][1]}
										{@const seatKey = `${row}-${seatNum}`}
										{@const count = isValidSeat ? seatStats[seatKey] || 0 : 0}
										{@const hasVisit = count > 0}
										{@const intensity = hasVisit ? Math.max(0.2, count / maxSeatCount) : 0}

										{#if isValidSeat}
											<div
												class="map-seat {hasVisit
													? 'active'
													: ''} group/seat relative cursor-default"
												style={hasVisit
													? `--intensity: ${intensity}; background-color: rgba(220, 38, 38, ${intensity});`
													: ''}
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
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.grid-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1px;
	}

	.row-label {
		width: 10px;
		font-size: 7px;
		font-weight: 900;
		color: #9ca3af;
		text-align: center;
		margin-right: 1px;
	}

	.empty-cell {
		width: 20px;
		height: 16px;
		flex-shrink: 0;
	}

	.aisle-gap {
		width: 6px;
		flex-shrink: 0;
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
		.row-label {
			width: 14px;
			font-size: 8px;
			margin-right: 2px;
		}
		.empty-cell,
		.map-seat {
			width: 24px;
			height: 18px;
			font-size: 8px;
		}
		.aisle-gap {
			width: 8px;
		}
	}
</style>
