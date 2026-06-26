<script lang="ts">
	import { MapPin, StretchHorizontal, Grid3x3, Maximize } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import TheaterSeatMap from '$lib/components/TheaterSeatMap.svelte';

	interface Props {
		rowStats: { counts: Record<string, number>; maxCount: number; uniqueVisited: number };
		seatStats: Record<string, number>;
		isLoading?: boolean;
	}

	let { rowStats, seatStats, isLoading = false }: Props = $props();

	const { t } = useTranslation();
	let mapView: 'ROWS' | 'SEATS' = $state('SEATS');
	let isFullscreen = $state(false);
</script>

<div
	class="bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] p-5 sm:p-6 relative overflow-hidden shadow-2xl shadow-red-500/10 dark:shadow-red-950/40 transition-all duration-300 hover:shadow-red-500/15"
>
	<div class="flex items-center justify-between mb-5">
		<h3
			class="font-black text-[10px] sm:text-xs uppercase tracking-[0.2em] text-gray-400 flex items-center gap-2"
		>
			<MapPin class="w-4 h-4 text-red-500" />
			{t('dashboard.seatMap.title')}
		</h3>

		<div class="flex items-center">
			<div class="h-8 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg flex items-center gap-1">
				<button
					onclick={() => (mapView = 'ROWS')}
					class={`h-full aspect-square flex items-center justify-center rounded-md transition-all cursor-pointer ${mapView === 'ROWS' ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
				>
					<StretchHorizontal class="w-3.5 h-3.5" />
				</button>
				<button
					onclick={() => (mapView = 'SEATS')}
					class={`h-full aspect-square flex items-center justify-center rounded-md transition-all cursor-pointer ${mapView === 'SEATS' ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
				>
					<Grid3x3 class="w-3.5 h-3.5" />
				</button>
			</div>
			<button
				onclick={() => (isFullscreen = true)}
				class="sm:hidden h-8 w-8 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-all cursor-pointer shadow-sm ml-2"
			>
				<Maximize class="w-3.5 h-3.5" />
			</button>
		</div>
	</div>

	<TheaterSeatMap
		embedded
		showHeader={false}
		{rowStats}
		{seatStats}
		{isLoading}
		bind:mapView
		bind:isFullscreen
	/>
</div>
