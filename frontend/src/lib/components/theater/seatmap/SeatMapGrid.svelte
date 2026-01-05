<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let rows: readonly string[];
	export let seatLayout: Record<string, any>;
	export let seatStats: Record<string, number>;
	export let maxSeatCount: number;
	export let isLoading: boolean;
	export let compact: boolean;

	const { t } = useTranslation();

	function getLayout(row: string) {
		return seatLayout[row as keyof typeof seatLayout];
	}
</script>

{#if isLoading}
	<!-- Skeleton Loading for Seats -->
	<div class="w-full overflow-x-auto pt-8 pb-4">
		<div class="seat-map-grid min-w-[700px] md:min-w-0 {compact ? 'is-compact' : ''}">
			{#each rows as row}
				{@const layout = getLayout(row)}
				<div class="grid-row">
					<!-- Row Label -->
					<div class="row-label">
						<div class="w-3/4 h-3/4 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
					</div>

					<!-- Group 1 (columns 1-6) -->
					{#each [1, 2, 3, 4, 5, 6] as col}
						{@const isValidSeat = col >= layout.groups[0][0] && col <= layout.groups[0][1]}
						{#if isValidSeat}
							<div class="map-seat bg-gray-200 dark:bg-zinc-700 animate-pulse border-none"></div>
						{:else}
							<div class="empty-cell"></div>
						{/if}
					{/each}

					<div class="aisle-gap"></div>

					<!-- Group 2 (columns 7-12) -->
					{#each [7, 8, 9, 10, 11, 12] as col}
						{@const isValidSeat = col >= layout.groups[1][0] && col <= layout.groups[1][1]}
						{#if isValidSeat}
							<div class="map-seat bg-gray-200 dark:bg-zinc-700 animate-pulse border-none"></div>
						{:else}
							<div class="empty-cell"></div>
						{/if}
					{/each}

					<div class="aisle-gap"></div>

					<!-- Group 3 (columns 13-18) -->
					{#each [13, 14, 15, 16, 17, 18] as col}
						{@const isValidSeat = col >= layout.groups[2][0] && col <= layout.groups[2][1]}
						{#if isValidSeat}
							<div class="map-seat bg-gray-200 dark:bg-zinc-700 animate-pulse border-none"></div>
						{:else}
							<div class="empty-cell"></div>
						{/if}
					{/each}

					<div class="aisle-gap"></div>

					<!-- Group 4 (columns 19-28) -->
					{#each [19, 20, 21, 22, 23, 24, 25, 26, 27, 28] as col}
						{@const isValidSeat = col >= layout.groups[3][0] && col <= layout.groups[3][1]}
						{#if isValidSeat}
							<div class="map-seat bg-gray-200 dark:bg-zinc-700 animate-pulse border-none"></div>
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
			{#each rows as row}
				{@const layout = getLayout(row)}
				<div class="grid-row">
					<!-- Row Label -->
					<div class="row-label">{row}</div>

					<!-- Group 1 (columns 1-6) -->
					{#each [1, 2, 3, 4, 5, 6] as col}
						{@const seatNum = col - layout.start + 1}
						{@const isValidSeat = col >= layout.groups[0][0] && col <= layout.groups[0][1]}
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
						{@const isValidSeat = col >= layout.groups[1][0] && col <= layout.groups[1][1]}
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
						{@const isValidSeat = col >= layout.groups[2][0] && col <= layout.groups[2][1]}
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
						{@const isValidSeat = col >= layout.groups[3][0] && col <= layout.groups[3][1]}
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

<style>
	/* Responsive Seat Map Styles */
	.seat-map-grid {
		display: flex;
		flex-direction: column;
		gap: 2px;
		width: fit-content;
		margin: 0 auto;
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
