<script lang="ts">
	interface Props {
		/**
		 * Skeleton for Event Cards matching the aspect-video design
		 */
		className?: string;
	}

	let { className = '' }: Props = $props();
</script>

<div
	class="relative flex flex-row sm:block h-[8.5rem] sm:h-auto sm:aspect-[2/3] bg-white dark:bg-zinc-900 shadow-sm rounded-[20px] sm:rounded-2xl overflow-hidden animate-pulse {className}"
	role="status"
	aria-label="Loading Event"
>
	<!-- Image Skeleton -->
	<div class="w-[38%] sm:w-full sm:h-full bg-gray-200 dark:bg-zinc-800 shrink-0"></div>

	<!-- Content Area -->
	<div
		class="relative flex-1 p-3.5 sm:p-5 flex flex-col justify-start sm:justify-end sm:absolute sm:inset-0"
	>
		<div class="sm:static absolute top-3.5 right-3.5">
			<div class="w-8 h-8 sm:w-16 sm:h-16 rounded-full bg-gray-300 dark:bg-zinc-700"></div>
		</div>

		<div class="flex flex-col gap-2 mt-2 sm:mt-0">
			<!-- Title Skeleton -->
			<div class="h-5 sm:h-6 w-3/4 bg-gray-300 dark:bg-zinc-700 rounded line-clamp-2"></div>

			<!-- Metadata Skeletons -->
			<div class="flex flex-col gap-1.5 mt-1">
				<div class="flex items-center gap-2">
					<div class="w-3.5 h-3.5 sm:w-4 sm:h-4 bg-gray-200 dark:bg-zinc-800 rounded"></div>
					<div class="h-3 w-32 bg-gray-200 dark:bg-zinc-800 rounded"></div>
				</div>
				<div class="flex items-center gap-2">
					<div class="w-3.5 h-3.5 sm:w-4 sm:h-4 bg-gray-200 dark:bg-zinc-800 rounded"></div>
					<div class="h-3 w-20 bg-gray-200 dark:bg-zinc-800 rounded"></div>
				</div>
			</div>
		</div>
	</div>
</div>
