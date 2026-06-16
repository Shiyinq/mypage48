<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		year: number;
		data?: Record<string, number>;
		isLoading?: boolean;
	}

	let { year, data = {}, isLoading = false }: Props = $props();

	const { t } = useTranslation();

	// Calculate calendar data
	let weeksAndLabels = $derived.by(() => {
		let wks: { date: Date | null; count: number }[][] = [];
		let labels: { label: string; colIndex: number }[] = [];

		if (year) {
			const firstDay = new Date(year, 0, 1);
			const lastDay = new Date(year, 11, 31);

			let currentWeek: { date: Date | null; count: number }[] = [];
			let currentMonth = -1;
			let colIndex = 0;

			// Fill empty days for the first week
			const firstDayOfWeek = firstDay.getDay(); // 0 is Sunday
			for (let i = 0; i < firstDayOfWeek; i++) {
				currentWeek.push({ date: null, count: 0 });
			}

			// Fill all days
			const d = new Date(year, 0, 1);
			while (d <= lastDay) {
				const yearStr = d.getFullYear();
				const monthStr = String(d.getMonth() + 1).padStart(2, '0');
				const dayStr = String(d.getDate()).padStart(2, '0');
				const dateStr = `${yearStr}-${monthStr}-${dayStr}`;

				const count = data[dateStr] || 0;
				currentWeek.push({ date: new Date(d), count });

				// Track month labels (when month changes)
				if (d.getMonth() !== currentMonth && currentWeek.length > 0) {
					// Get short month name from i18n
					const monthKey = [
						'jan',
						'feb',
						'mar',
						'apr',
						'may',
						'jun',
						'jul',
						'aug',
						'sep',
						'oct',
						'nov',
						'dec'
					][d.getMonth()];
					labels.push({
						label: t(`time.monthsShort.${monthKey}`),
						colIndex: colIndex
					});
					currentMonth = d.getMonth();
				}

				if (currentWeek.length === 7) {
					wks.push(currentWeek);
					currentWeek = [];
					colIndex++;
				}

				d.setDate(d.getDate() + 1);
			}

			// Fill empty days for the last week
			if (currentWeek.length > 0) {
				while (currentWeek.length < 7) {
					currentWeek.push({ date: null, count: 0 });
				}
				wks.push(currentWeek);
			}
		}

		return { weeks: wks, monthLabels: labels };
	});

	let weeks = $derived(weeksAndLabels.weeks);
	let monthLabels = $derived(weeksAndLabels.monthLabels);

	// Calculate color intensity
	function getIntensity(count: number): number {
		if (count === 0) return 0;
		if (count === 1) return 0.25;
		if (count === 2) return 0.5;
		if (count === 3) return 0.75;
		return 1;
	}

	// Function to format date reactively
	function formatDateStr(date: Date | null): string {
		if (!date) return '';

		const monthKey = [
			'jan',
			'feb',
			'mar',
			'apr',
			'may',
			'jun',
			'jul',
			'aug',
			'sep',
			'oct',
			'nov',
			'dec'
		][date.getMonth()];
		const month = t(`time.monthsShort.${monthKey}`);

		return `${month} ${date.getDate()}, ${date.getFullYear()}`;
	}

	let daysOfWeek = $derived([
		'',
		t('time.daysShort.mon'),
		'',
		t('time.daysShort.wed'),
		'',
		t('time.daysShort.fri'),
		''
	]);

	let monthsLabelList = $derived([
		t('time.monthsShort.jan'),
		t('time.monthsShort.feb'),
		t('time.monthsShort.mar'),
		t('time.monthsShort.apr'),
		t('time.monthsShort.may'),
		t('time.monthsShort.jun'),
		t('time.monthsShort.jul'),
		t('time.monthsShort.aug'),
		t('time.monthsShort.sep'),
		t('time.monthsShort.oct'),
		t('time.monthsShort.nov'),
		t('time.monthsShort.dec')
	]);

	// Skeleton columns for loading state
	const skeletonCols = 53;
	const skeletonRows = 7;
</script>

<div class="glass-panel p-4 sm:p-6 rounded-3xl w-full">
	<div class="mb-4 sm:mb-6">
		<h3 class="text-lg sm:text-xl font-bold text-themed">{t('dashboard.heatmap.title')}</h3>
		<p class="text-[10px] sm:text-xs text-gray-400">{t('dashboard.heatmap.subtitle')} {year}</p>
	</div>

	{#if isLoading}
		<!-- Skeleton loading -->
		<div class="w-full overflow-hidden">
			<div class="heatmap-outer">
				<!-- Skeleton month labels -->
				<div class="heatmap-month-row">
					<div class="heatmap-spacer"></div>
					<div class="flex flex-1 justify-between pr-4">
						{#each monthsLabelList as _m}
							<div class="skeleton-text"></div>
						{/each}
					</div>
				</div>
				<!-- Skeleton grid -->
				<div class="heatmap-body">
					<div class="heatmap-day-col">
						{#each daysOfWeek as day}
							<div class="heatmap-day-text">{day}</div>
						{/each}
					</div>
					<div class="heatmap-grid" style="grid-template-columns: repeat({skeletonCols}, 1fr);">
						{#each { length: skeletonCols * skeletonRows } as _}
							<div class="heatmap-cell skeleton-cell"></div>
						{/each}
					</div>
				</div>
			</div>
		</div>
	{:else}
		<!-- Scrollable heatmap area (scroll only on mobile) -->
		<div class="heatmap-scroll-wrapper">
			<div class="heatmap-outer">
				<!-- Month labels -->
				<div class="heatmap-month-row">
					<div class="heatmap-spacer"></div>
					<div class="heatmap-month-track">
						{#each monthLabels as month}
							<span
								class="heatmap-month-label"
								style="left: {(month.colIndex / weeks.length) * 100}%;"
							>
								{month.label}
							</span>
						{/each}
					</div>
				</div>

				<!-- Day labels + Heatmap grid -->
				<div class="heatmap-body">
					<!-- Day labels column -->
					<div class="heatmap-day-col">
						{#each daysOfWeek as day}
							<div class="heatmap-day-text">{day}</div>
						{/each}
					</div>

					<!-- Flat heatmap grid (auto-flow: column) -->
					<div class="heatmap-grid" style="grid-template-columns: repeat({weeks.length}, 1fr);">
						{#each weeks as week}
							{#each week as day}
								{#if day.date === null}
									<div class="heatmap-cell"></div>
								{:else if day.count === 0}
									<div class="heatmap-cell heatmap-cell-empty">
										<span class="heatmap-tooltip"
											>{t('dashboard.heatmap.noAttendance')} {formatDateStr(day.date)}</span
										>
									</div>
								{:else}
									<div
										class="heatmap-cell heatmap-cell-filled"
										style="background-color: rgba(227, 0, 15, {getIntensity(day.count)});"
									>
										<span class="heatmap-tooltip"
											>{day.count}
											{t('dashboard.heatmap.attendance')}{day.count > 1 ? 's' : ''}
											{t('dashboard.heatmap.on')}
											{formatDateStr(day.date)}</span
										>
									</div>
								{/if}
							{/each}
						{/each}
					</div>
				</div>
			</div>
		</div>

		<!-- Legend — OUTSIDE the scroll container -->
		<div class="flex items-center justify-end mt-3 gap-1.5 text-[10px] text-gray-400">
			<span>{t('dashboard.heatmap.less')}</span>
			<div class="flex gap-1">
				<div class="legend-box heatmap-cell-empty"></div>
				<div class="legend-box" style="background-color: rgba(227, 0, 15, 0.25);"></div>
				<div class="legend-box" style="background-color: rgba(227, 0, 15, 0.5);"></div>
				<div class="legend-box" style="background-color: rgba(227, 0, 15, 0.75);"></div>
				<div class="legend-box" style="background-color: rgba(227, 0, 15, 1);"></div>
			</div>
			<span>{t('dashboard.heatmap.more')}</span>
		</div>
	{/if}
</div>

<style>
	/* Scroll wrapper: scrollable on mobile, hidden on desktop */
	.heatmap-scroll-wrapper {
		width: 100%;
		overflow-x: auto;
		padding-bottom: 8px;
	}

	@media (min-width: 1024px) {
		.heatmap-scroll-wrapper {
			overflow: visible;
			padding-bottom: 0;
		}
	}

	/* Outer wrapper ensures minimum usable width on mobile */
	.heatmap-outer {
		min-width: 620px;
		width: 100%;
	}

	@media (min-width: 1024px) {
		.heatmap-outer {
			min-width: 0;
		}
	}

	/* Skeleton loading */
	.skeleton-text {
		width: 24px;
		height: 10px;
		border-radius: 3px;
		background-color: #e5e7eb;
		animation: skeleton-pulse 1.5s ease-in-out infinite;
	}

	:global(.dark) .skeleton-text {
		background-color: rgba(63, 63, 70, 0.4);
	}

	.skeleton-cell {
		background-color: #e5e7eb;
		animation: skeleton-pulse 1.5s ease-in-out infinite;
	}

	:global(.dark) .skeleton-cell {
		background-color: rgba(63, 63, 70, 0.4);
	}

	@keyframes skeleton-pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.4;
		}
	}

	/* Month label row */
	.heatmap-month-row {
		display: flex;
		margin-bottom: 4px;
	}

	.heatmap-spacer {
		width: 30px;
		flex-shrink: 0;
	}

	.heatmap-month-track {
		flex: 1;
		position: relative;
		height: 16px;
	}

	.heatmap-month-label {
		position: absolute;
		top: 0;
		font-size: 10px;
		font-weight: 500;
		color: var(--color-gray-400, #9ca3af);
		white-space: nowrap;
	}

	/* Body: day labels + grid side by side */
	.heatmap-body {
		display: flex;
		gap: 3px;
	}

	/* Day labels column — matches grid row heights via flex stretch */
	.heatmap-day-col {
		display: grid;
		grid-template-rows: repeat(7, 1fr);
		gap: 3px;
		width: 30px;
		flex-shrink: 0;
	}

	.heatmap-day-text {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding-right: 4px;
		font-size: 10px;
		font-weight: 500;
		color: var(--color-gray-400, #9ca3af);
	}

	/* The main heatmap: single flat grid, items flow column-first */
	.heatmap-grid {
		display: grid;
		grid-template-rows: repeat(7, auto);
		grid-auto-flow: column;
		gap: 3px;
		flex: 1;
	}

	/* Each cell: square via aspect-ratio */
	.heatmap-cell {
		aspect-ratio: 1;
		border-radius: 3px;
		position: relative;
		cursor: default;
	}

	/* Empty cells: visible subtle background */
	.heatmap-cell-empty {
		background-color: #ebedf0;
	}

	:global(.dark) .heatmap-cell-empty {
		background-color: rgba(63, 63, 70, 0.5);
	}

	/* Filled cells: outline on hover */
	.heatmap-cell-filled:hover {
		outline: 2px solid rgba(227, 0, 15, 0.6);
		outline-offset: -1px;
	}

	/* Tooltip */
	.heatmap-tooltip {
		position: absolute;
		bottom: calc(100% + 6px);
		left: 50%;
		transform: translateX(-50%);
		padding: 5px 10px;
		background-color: #24292f;
		color: white;
		font-size: 11px;
		font-weight: 500;
		border-radius: 6px;
		opacity: 0;
		visibility: hidden;
		white-space: nowrap;
		pointer-events: none;
		z-index: 50;
		transition:
			opacity 0.15s ease,
			visibility 0.15s ease;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
	}

	.heatmap-cell:hover .heatmap-tooltip {
		opacity: 1;
		visibility: visible;
	}

	/* Legend color boxes */
	.legend-box {
		width: 12px;
		height: 12px;
		border-radius: 3px;
	}

	/* Responsive tweaks */
	@media (min-width: 640px) {
		.heatmap-month-label {
			font-size: 11px;
		}

		.heatmap-day-text {
			font-size: 11px;
		}

		.heatmap-spacer,
		.heatmap-day-col {
			width: 34px;
		}

		.legend-box {
			width: 14px;
			height: 14px;
		}
	}
</style>
