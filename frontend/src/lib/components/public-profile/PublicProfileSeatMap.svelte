<script lang="ts">
	import TheaterSeatMap from '$lib/components/TheaterSeatMap.svelte';

	interface Props {
		rowStats: { counts: Record<string, number>; maxCount: number; uniqueVisited: number };
		seatStats: Record<string, number>;
		isLoading?: boolean;
	}

	let { rowStats, seatStats, isLoading = false }: Props = $props();
</script>

<div
	class="bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] p-6 relative overflow-hidden shadow-2xl shadow-red-500/10 dark:shadow-red-950/40 transition-all duration-300 hover:shadow-red-500/15"
>
	<TheaterSeatMap embedded {rowStats} {seatStats} {isLoading} />
</div>
