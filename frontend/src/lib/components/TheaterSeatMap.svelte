<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { X } from 'lucide-svelte';
	import { portal } from '$lib/actions/portal';
	import SeatMapHeader from './theater/seatmap/SeatMapHeader.svelte';
	import SeatMapRows from './theater/seatmap/SeatMapRows.svelte';
	import SeatMapGrid from './theater/seatmap/SeatMapGrid.svelte';
	import SeatMapFitScaler from './theater/seatmap/SeatMapFitScaler.svelte';

	interface Props {
		rowStats: { counts: Record<string, number>; maxCount: number; uniqueVisited: number };
		seatStats: Record<string, number>;
		isLoading?: boolean;
		showHeader?: boolean;
		showSubtitle?: boolean;
		showRowStats?: boolean;
		compact?: boolean;
		embedded?: boolean;
		mapView?: 'ROWS' | 'SEATS';
		isFullscreen?: boolean;
	}

	let {
		rowStats,
		seatStats,
		isLoading = false,
		showHeader = true,
		showSubtitle = true,
		showRowStats = true,
		compact = false,
		embedded = false,
		mapView = $bindable('SEATS'),
		isFullscreen = $bindable(false)
	}: Props = $props();

	const { t } = useTranslation();

	const THEATER_ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'] as const;

	let maxSeatCount = $derived(seatStats ? Math.max(...Object.values(seatStats), 1) : 1);

	let isMobile = $state(false);

	$effect(() => {
		const mq = window.matchMedia('(max-width: 767px)');
		const update = () => {
			isMobile = mq.matches;
		};
		update();
		mq.addEventListener('change', update);
		return () => mq.removeEventListener('change', update);
	});

	let useFitScaler = $derived(embedded && !isMobile);
</script>

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

{#snippet seatMapContent()}
	{#if showHeader}
		<SeatMapHeader
			{showSubtitle}
			{showRowStats}
			{rowStats}
			totalRows={THEATER_ROWS.length}
			bind:mapView
			onfullscreen={() => (isFullscreen = true)}
		/>
	{/if}

	<div class="w-full">
		<div class="w-full mx-auto px-1 sm:px-2">
			<div class="w-full">
				{#if mapView === 'ROWS'}
					<SeatMapRows rows={THEATER_ROWS} {rowStats} {isLoading} />
				{/if}

				{#if mapView === 'SEATS'}
					{#if useFitScaler}
						<SeatMapFitScaler>
							{#snippet children()}
								<SeatMapGrid
									rows={THEATER_ROWS}
									{seatStats}
									{maxSeatCount}
									{isLoading}
									{compact}
									fitParent={true}
									{stage}
								/>
							{/snippet}
						</SeatMapFitScaler>
					{:else}
						<SeatMapGrid
							rows={THEATER_ROWS}
							{seatStats}
							{maxSeatCount}
							{isLoading}
							{compact}
							{stage}
						/>
					{/if}
				{/if}
			</div>
		</div>
	</div>
{/snippet}

{#if embedded}
	{@render seatMapContent()}
{:else}
	<div class="glass-panel p-6 rounded-3xl">
		{@render seatMapContent()}
	</div>
{/if}

{#if isFullscreen}
	<div use:portal class="fixed inset-0 z-[9999] bg-white dark:bg-gray-900 overflow-hidden">
		<button
			class="absolute top-6 right-6 z-[10000] p-3 bg-gray-100 dark:bg-gray-800 rounded-full shadow-lg border border-gray-200 dark:border-gray-700 text-gray-500 hover:text-gray-800 dark:hover:text-gray-100 transition-all"
			onclick={() => (isFullscreen = false)}
		>
			<X class="w-6 h-6" />
		</button>

		<div class="landscape-wrapper">
			<div class="w-full h-full p-2 sm:p-6 mx-auto flex flex-col justify-center items-center">
				<SeatMapFitScaler allowScaleUp={true} fitHeight={true}>
					{#snippet children()}
						<SeatMapGrid
							rows={THEATER_ROWS}
							{seatStats}
							{maxSeatCount}
							{isLoading}
							compact={false}
							fitParent={true}
							{stage}
						/>
					{/snippet}
				</SeatMapFitScaler>
			</div>
		</div>
	</div>
{/if}

<style>
	.landscape-wrapper {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 100dvh;
		height: 100dvw;
		transform: translate(-50%, -50%) rotate(90deg);
		overflow: hidden;
		display: flex;
	}

	@media (orientation: landscape) {
		.landscape-wrapper {
			width: 100dvw;
			height: 100dvh;
			transform: translate(-50%, -50%) rotate(0deg);
		}
	}
</style>
