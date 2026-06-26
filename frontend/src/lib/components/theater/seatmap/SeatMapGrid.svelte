<script lang="ts">
	interface SeatRowLayout {
		readonly groups: readonly (readonly [number, number])[];
		readonly start: number;
	}

	interface Props {
		rows: readonly string[];
		seatLayout?: Record<string, SeatRowLayout>;
		seatStats: Record<string, number>;
		maxSeatCount: number;
		isLoading: boolean;
		compact: boolean;
		fitParent?: boolean;
		stage?: import('svelte').Snippet;
	}

	let {
		rows,
		seatStats,
		maxSeatCount,
		isLoading,
		compact,
		fitParent = false,
		stage
	}: Props = $props();

	// Exact configuration from row-theater
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

	// Calculates the CSS Grid column for a given seat.
	// We add +1 at the end so it starts at column 2 (column 1 is reserved for the row label).
	function getGridColumn(rowChar: string, seatNum: number): number {
		const leftCount = LEFT_COUNTS[rowChar];
		if (!leftCount) return 2; // fallback

		if (seatNum <= leftCount) {
			// Left block right-aligns to column 9
			return 9 - leftCount + seatNum + 1;
		} else if (seatNum <= leftCount + 6) {
			// Middle-left block starts at column 11
			return 11 + (seatNum - leftCount - 1) + 1;
		} else if (seatNum <= leftCount + 12) {
			// Middle-right block starts at column 18
			return 18 + (seatNum - leftCount - 7) + 1;
		} else {
			// Right block starts at column 25
			return 25 + (seatNum - leftCount - 13) + 1;
		}
	}
</script>

{#if isLoading}
	<!-- Skeleton Loading for Seats -->
	<div
		class={fitParent
			? 'w-fit pt-8 pb-4'
			: 'w-full overflow-x-auto lg:overflow-x-visible pt-8 pb-4 hide-scrollbar'}
	>
		<div
			class="seat-map-grid {fitParent ? 'is-fit-parent' : 'min-w-[700px] md:min-w-0'} {compact
				? 'is-compact'
				: ''}"
		>
			{#if stage}
				<div
					style="grid-column: 7 / 32; grid-row: 1; display: flex; justify-content: center; margin-bottom: 2rem;"
				>
					{@render stage()}
				</div>
			{/if}

			{#each rows as row, rowIndex}
				<!-- Row Label Skeleton -->
				<div class="row-label" style="grid-column: 1; grid-row: {rowIndex + (stage ? 2 : 1)};">
					<div class="w-3/4 h-3/4 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
				</div>

				{#each Array(ROW_COUNTS[row] || 22) as _, i}
					{@const gridCol = getGridColumn(row, i + 1)}
					<div
						class="map-seat bg-gray-200 dark:bg-zinc-700 animate-pulse border-none"
						style="grid-column: {gridCol}; grid-row: {rowIndex + (stage ? 2 : 1)};"
					></div>
				{/each}
			{/each}
		</div>
	</div>
{:else}
	<div
		class={fitParent
			? 'w-fit pt-8 pb-4'
			: 'w-full overflow-x-auto lg:overflow-x-visible pt-8 pb-4 hide-scrollbar'}
	>
		<div
			class="seat-map-grid {fitParent ? 'is-fit-parent' : 'min-w-[700px] md:min-w-0'} {compact
				? 'is-compact'
				: ''}"
		>
			{#if stage}
				<div
					style="grid-column: 7 / 32; grid-row: 1; display: flex; justify-content: center; align-items: end; margin-bottom: 2rem; position: relative;"
				>
					{@render stage()}
				</div>
			{/if}

			{#each rows as row, rowIndex}
				<!-- Row Label -->
				<div class="row-label" style="grid-column: 1; grid-row: {rowIndex + (stage ? 2 : 1)};">
					{row}
				</div>

				<!-- Seats -->
				{#each Array(ROW_COUNTS[row] || 0) as _, i}
					{@const seatNum = i + 1}
					{@const gridCol = getGridColumn(row, seatNum)}
					{@const seatKey = `${row}-${seatNum}`}
					{@const count = seatStats[seatKey] || 0}
					{@const hasVisit = count > 0}
					{@const intensity = hasVisit ? Math.max(0.25, count / maxSeatCount) : 0}

					<div
						class="map-seat {hasVisit ? 'active' : ''}"
						style="grid-column: {gridCol}; grid-row: {rowIndex + (stage ? 2 : 1)}; {hasVisit
							? `--intensity: ${intensity}`
							: ''}"
						data-title="{seatKey}: {count}x"
					>
						<span class="seat-id">{seatKey}</span>
						{#if hasVisit}<span class="seat-count">{count}x</span>{/if}
					</div>
				{/each}
			{/each}
		</div>
	</div>
{/if}

<style>
	/* Responsive Seat Map Styles */
	.seat-map-grid {
		--seat-w: 24px;
		--aisle-w: 12px;
		display: grid;
		/* 1 column for row label + 34 columns for the theater map layout */
		/* Columns 10, 17, and 24 are the aisles */
		grid-template-columns:
			max-content repeat(9, var(--seat-w)) var(--aisle-w) repeat(6, var(--seat-w))
			var(--aisle-w) repeat(6, var(--seat-w)) var(--aisle-w) repeat(10, var(--seat-w));
		gap: 2px 2px;
		width: fit-content;
		margin: 0 auto;
	}

	.is-fit-parent.seat-map-grid {
		margin: 0;
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
		margin-right: 6px;
	}

	:global(.dark) .row-label {
		color: #f9a8d4;
		background: rgba(227, 0, 15, 0.2);
	}

	.map-seat {
		display: flex;
		width: 24px;
		height: 24px;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		border-radius: 3px;
		border: 1px solid #e0e0e0;
		background-color: #f5f5f5;
		cursor: default;
		transition: transform 0.15s ease;
		position: relative;
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
		.seat-map-grid {
			--seat-w: 32px;
			--aisle-w: 12px;
			gap: 2px 2px;
		}

		.row-label {
			width: 24px;
			height: 32px;
			font-size: 11px;
			margin-right: 8px;
		}

		.map-seat {
			width: 32px;
			height: 32px;
			border-radius: 5px;
		}

		.map-seat .seat-id {
			font-size: 8px;
		}

		.map-seat .seat-count {
			font-size: 7px;
		}

		/* Compact Mode (Public Profile) */
		.is-compact .row-label {
			width: 18px;
			height: 22px;
			font-size: 9px;
			margin-right: 6px;
		}

		.is-compact.seat-map-grid {
			--seat-w: 22px;
			--aisle-w: 10px;
			gap: 1px 1px;
		}

		.is-compact .map-seat {
			width: 22px;
			height: 22px;
			border-radius: 3px;
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

	/* Mobile Adjustments */
	@media (max-width: 767px) {
		.map-seat .seat-id {
			font-size: 7px;
		}
		.map-seat .seat-count {
			font-size: 6px;
		}
		.seat-map-grid {
			gap: 1px 1px;
		}
	}
</style>
