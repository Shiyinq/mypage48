<script lang="ts">
	/**
	 * Skeleton for Event Cards matching the aspect-video design
	 */
	export let className: string = '';
</script>

<div
	class="relative aspect-video bg-gray-100 dark:bg-zinc-800 rounded-2xl overflow-hidden shadow-sm animate-pulse {className}"
	role="status"
	aria-label="Loading Event"
>
	<!-- Background Placeholder -->
	<div class="absolute inset-0 bg-gray-200 dark:bg-zinc-700 w-full h-full"></div>

	<!-- Bottom Content Area -->
	<div class="absolute inset-x-0 bottom-0 p-5 z-10">
		<!-- Icon Row -->
		<div class="flex items-start justify-between mb-1">
			<!-- Team Icon Skeleton -->
			<div class="w-16 h-16 rounded-full bg-gray-300 dark:bg-zinc-600"></div>
		</div>

		<!-- Title Skeleton -->
		<div class="h-6 w-3/4 bg-gray-300 dark:bg-zinc-600 rounded mb-2"></div>

		<!-- Metadata Row Skeleton -->
		<div class="flex items-center gap-2">
			<div class="h-3 w-16 bg-gray-300 dark:bg-zinc-600 rounded"></div>
			<div class="h-3 w-1 bg-gray-300 dark:bg-zinc-600 rounded-full"></div>
			<div class="h-3 w-12 bg-gray-300 dark:bg-zinc-600 rounded"></div>
			<div class="h-3 w-1 bg-gray-300 dark:bg-zinc-600 rounded-full"></div>
			<div class="h-3 w-20 bg-gray-300 dark:bg-zinc-600 rounded"></div>
		</div>
	</div>

	<!-- Gradient Overlay Simulation -->
	<div
		class="absolute inset-0 bg-gradient-to-t from-gray-100/50 via-transparent to-transparent dark:from-zinc-900/50"
	></div>
</div>
