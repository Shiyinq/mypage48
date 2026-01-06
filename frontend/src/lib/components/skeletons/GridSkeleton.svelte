<script lang="ts">
	/**
	 * Reusable grid skeleton component for loading states
	 */
	export let columns: 1 | 2 | 3 | 4 = 3;
	export let count: number = 6;
	export let aspectRatio: 'square' | 'video' | 'portrait' = 'square';
	export let className: string = '';

	const columnClasses = {
		1: 'grid-cols-1',
		2: 'grid-cols-1 md:grid-cols-2',
		3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
		4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
	};

	const aspectClasses = {
		square: 'aspect-square',
		video: 'aspect-video',
		portrait: 'aspect-[3/4]'
	};
</script>

<div class="grid {columnClasses[columns]} gap-6 {className}" role="status" aria-label="Loading">
	<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
	{#each Array(count) as _}
		<div class="glass-panel rounded-3xl overflow-hidden animate-pulse">
			<div class="{aspectClasses[aspectRatio]} bg-gray-200 dark:bg-zinc-700"></div>
			<div class="p-4 space-y-2">
				<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-3/4"></div>
				<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-1/2"></div>
			</div>
		</div>
	{/each}
</div>
