<script lang="ts">
	import type { Setlist } from '$lib/apis/setlists';
	import { ShowCard } from '$lib/components/shows';

	interface Props {
		title: string;
		items: Setlist[];
		maxAttendance: number;
		isActive?: boolean;
		onclick?: (id: string) => void;
	}

	let { title, items, maxAttendance, isActive = false, onclick }: Props = $props();

	function toShowData(s: Setlist) {
		return {
			title: s.title,
			image: s.imageUrl,
			imageMedium: s.imageUrl_medium,
			imageSmall: s.imageUrl_small,
			blurHash: s.blurHash,
			count: s.watched.count,
			percentage: s.watched.percentage,
			isMostWatched: s.watched.isMostWatched
		};
	}
</script>

<div class="mb-8 last:mb-0">
	<h3 class="text-lg font-semibold text-gray-600 dark:text-gray-400 mb-4 flex items-center gap-2">
		{#if isActive}
			<div class="w-2 h-2 rounded-full bg-green-500"></div>
		{/if}
		{title}
	</h3>
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
		{#each items as item (item.setlistId)}
			{@const show = toShowData(item)}
			<ShowCard
				{show}
				count={show.count}
				{maxAttendance}
				onClick={() => onclick?.(item.setlistId)}
			/>
		{/each}
	</div>
</div>
