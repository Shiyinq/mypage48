<script lang="ts">
</script>

<div class="grid lg:grid-cols-3 gap-6">
	<!-- Skeleton: Kami Oshi Card -->
	<div class="lg:col-span-1">
		<div
			class="relative overflow-hidden bg-white dark:bg-zinc-800 rounded-3xl shadow-sm border border-gray-100 dark:border-zinc-700 p-8 flex flex-col items-center"
		>
			<div class="h-6 w-32 bg-gray-200 dark:bg-zinc-700 rounded-full mb-6 animate-pulse"></div>
			<div class="w-36 h-36 rounded-full bg-gray-200 dark:bg-zinc-700 mb-6 animate-pulse"></div>
			<div class="h-8 w-48 bg-gray-200 dark:bg-zinc-700 rounded mb-4 animate-pulse"></div>
			<div class="h-6 w-24 bg-gray-200 dark:bg-zinc-700 rounded mb-8 animate-pulse"></div>
			<div class="grid grid-cols-2 gap-4 w-full">
				<div class="h-20 bg-gray-100 dark:bg-zinc-700/50 rounded-2xl animate-pulse"></div>
				<div class="h-20 bg-gray-100 dark:bg-zinc-700/50 rounded-2xl animate-pulse"></div>
			</div>
		</div>
	</div>

	<!-- Skeleton: Leaderboard -->
	<div class="lg:col-span-2">
		<div
			class="bg-white dark:bg-zinc-800 rounded-3xl border border-gray-100 dark:border-zinc-700 shadow-sm overflow-hidden"
		>
			<div
				class="p-6 border-b border-gray-100 dark:border-zinc-700 flex justify-between items-center"
			>
				<div class="h-6 w-40 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
				<div class="h-6 w-24 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
			</div>
			<div class="divide-y divide-gray-50 dark:divide-zinc-700">
				<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
				{#each Array(5)}
					<div class="p-4 flex items-center gap-4">
						<div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
						<div class="w-12 h-12 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
						<div class="flex-1 space-y-2">
							<div class="h-4 w-32 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
							<div class="h-3 w-20 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
						</div>
						<div
							class="w-24 h-4 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse hidden sm:block"
						></div>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>
