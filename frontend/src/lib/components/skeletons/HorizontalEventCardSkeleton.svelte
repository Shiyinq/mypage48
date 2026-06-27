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
	class="relative flex flex-row h-32 sm:h-36 lg:h-40 bg-white dark:bg-zinc-900 shadow-sm rounded-2xl overflow-hidden animate-pulse border border-gray-100 dark:border-white/5 {className}"
	role="status"
	aria-label="Loading Event"
>
	<!-- Image Skeleton -->
	<div class="w-1/3 sm:w-2/5 h-full bg-gray-200 dark:bg-zinc-800 shrink-0"></div>

	<!-- Content Area -->
	<div class="flex-1 p-3 sm:p-5 flex flex-col">
		<!-- Labels Row -->
		<div class="flex items-center gap-2 mb-3">
			<div class="w-12 sm:w-16 h-4 bg-gray-200 dark:bg-zinc-800 rounded"></div>
			<div class="w-12 sm:w-16 h-4 bg-gray-200 dark:bg-zinc-800 rounded"></div>
		</div>

		<!-- Title Lines -->
		<div class="space-y-2 mb-3">
			<div class="w-full h-5 sm:h-6 bg-gray-200 dark:bg-zinc-800 rounded"></div>
			<div class="w-2/3 h-5 sm:h-6 bg-gray-200 dark:bg-zinc-800 rounded"></div>
		</div>

		<div class="mt-auto flex flex-col gap-2">
			<!-- Date & Time -->
			<div class="w-1/2 h-3 sm:h-4 bg-gray-200 dark:bg-zinc-800 rounded"></div>
			<!-- Members (Optional) -->
			<div class="w-1/3 h-3 sm:h-4 bg-gray-200 dark:bg-zinc-800 rounded"></div>
		</div>
	</div>
</div>
