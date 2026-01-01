<script lang="ts">
	/**
	 * Skeleton component for ticket/history cards
	 */
	export let count: number = 6;
	export let className: string = '';
</script>

<div
	class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 {className}"
	role="status"
	aria-label="Loading"
>
	{#each Array(count) as _}
		<div
			class="bg-white dark:bg-zinc-900 rounded-2xl overflow-hidden shadow-sm border border-gray-100 dark:border-zinc-700 flex flex-col h-full animate-pulse"
		>
			<!-- Image Section -->
			<div class="h-48 w-full bg-gray-200 dark:bg-zinc-800 relative">
				<!-- Label badge skeleton -->
				<div class="absolute top-3 left-3 w-16 h-5 rounded-full bg-gray-300 dark:bg-zinc-700"></div>
				<!-- Title skeleton -->
				<div class="absolute bottom-5 left-5 right-5 space-y-2">
					<div class="h-4 w-1/4 bg-gray-300 dark:bg-zinc-700 rounded"></div>
					<div class="h-6 w-3/4 bg-gray-300 dark:bg-zinc-700 rounded"></div>
				</div>
			</div>

			<!-- Body -->
			<div class="p-5 flex-1 flex flex-col gap-4">
				<!-- Date/Time Grid -->
				<div class="grid grid-cols-2 gap-4">
					<div class="flex flex-col gap-1">
						<div class="h-3 w-8 bg-gray-200 dark:bg-zinc-800 rounded"></div>
						<div class="h-4 w-24 bg-gray-100 dark:bg-zinc-800 rounded"></div>
					</div>
					<div class="flex flex-col gap-1">
						<div class="h-3 w-8 bg-gray-200 dark:bg-zinc-800 rounded"></div>
						<div class="h-4 w-16 bg-gray-100 dark:bg-zinc-800 rounded"></div>
					</div>
				</div>

				<!-- Seat/Price Box -->
				<div
					class="bg-gray-50 dark:bg-zinc-800/50 rounded-xl p-3 border border-gray-100 dark:border-zinc-800 flex items-center justify-between"
				>
					<div class="flex items-center gap-3">
						<div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700"></div>
						<div class="flex flex-col gap-1">
							<div class="h-3 w-8 bg-gray-200 dark:bg-zinc-700 rounded"></div>
							<div class="h-4 w-12 bg-gray-200 dark:bg-zinc-700 rounded"></div>
						</div>
					</div>
					<div class="flex flex-col items-end gap-1">
						<div class="h-3 w-10 bg-gray-200 dark:bg-zinc-700 rounded"></div>
						<div class="h-4 w-16 bg-gray-200 dark:bg-zinc-700 rounded"></div>
					</div>
				</div>

				<!-- Notes -->
				<div class="flex-1 space-y-2">
					<div class="flex justify-between">
						<div class="h-3 w-12 bg-gray-200 dark:bg-zinc-800 rounded"></div>
						<div class="h-3 w-16 bg-gray-200 dark:bg-zinc-800 rounded"></div>
					</div>
					<div class="h-10 bg-gray-100 dark:bg-zinc-800/30 rounded-lg"></div>
				</div>
			</div>
		</div>
	{/each}
</div>
