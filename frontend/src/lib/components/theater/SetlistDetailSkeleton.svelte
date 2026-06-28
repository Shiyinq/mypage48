<script lang="ts">
</script>

<div class="animate-pulse bg-white dark:bg-zinc-900 overflow-hidden">
	<!-- Hero Skeleton -->
	<div class="relative w-full flex flex-col">
		<div
			class="relative w-full min-h-[280px] sm:min-h-[350px] flex flex-col justify-end bg-gray-200 dark:bg-zinc-800"
		>
			<!-- Gradient Overlay -->
			<div
				class="absolute inset-0 bg-gradient-to-t from-white via-white/95 to-transparent dark:from-zinc-900 dark:via-zinc-900/95"
			></div>

			<!-- Content Container -->
			<div
				class="relative z-20 px-6 sm:px-10 pt-[150px] sm:pt-[200px] pb-6 sm:pb-10 flex flex-col justify-end w-full"
			>
				<div class="w-full flex items-end justify-between gap-6 max-w-5xl mx-auto">
					<div class="space-y-3 w-full md:max-w-2xl">
						<div class="flex gap-2">
							<div class="w-20 h-6 bg-gray-300 dark:bg-zinc-700 rounded-full"></div>
							<div class="w-28 h-6 bg-gray-300 dark:bg-zinc-700 rounded-full"></div>
						</div>
						<div class="w-3/4 h-10 md:h-12 bg-gray-300 dark:bg-zinc-700 rounded-lg"></div>
						<div class="w-1/2 h-5 md:h-6 bg-gray-300/50 dark:bg-zinc-700/50 rounded-lg"></div>
						<div class="w-full max-w-xl h-4 bg-gray-300 dark:bg-zinc-700 rounded-lg"></div>
						<div class="w-2/3 max-w-sm h-4 bg-gray-300 dark:bg-zinc-700 rounded-lg"></div>
					</div>
					<div class="hidden md:block">
						<div class="w-[140px] h-[110px] bg-gray-300 dark:bg-zinc-700 rounded-2xl"></div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content Grid -->
	<div class="p-6 sm:p-8 lg:p-10 max-w-5xl mx-auto flex flex-col gap-8">
		<!-- Stats Cards Skeleton -->
		<div class="w-full">
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
				{#each Array(6) as _}
					<div
						class="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 p-4 rounded-2xl flex items-center gap-3.5"
					>
						<div
							class="w-11 h-11 md:w-12 md:h-12 bg-gray-200 dark:bg-zinc-800 rounded-xl shrink-0"
						></div>
						<div class="flex-1 space-y-2">
							<div class="w-20 h-5 md:h-6 bg-gray-200 dark:bg-zinc-800 rounded-lg"></div>
							<div class="w-28 h-3 bg-gray-200 dark:bg-zinc-800 rounded"></div>
						</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- Grid for Ticket History & 2-Shot -->
		<div class="w-full grid grid-cols-1 md:grid-cols-12 gap-8">
			<!-- Ticket History Section Skeleton -->
			<div class="mt-4 md:mt-0 order-2 md:order-1 md:col-span-8 lg:col-span-8">
				<div class="flex items-center justify-between mb-6">
					<div class="w-32 h-6 md:h-8 bg-gray-200 dark:bg-zinc-800 rounded-lg"></div>
					<div class="w-16 h-6 bg-gray-200 dark:bg-zinc-800 rounded-full"></div>
				</div>

				<div class="space-y-3">
					{#each Array(3) as _}
						<div
							class="bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 overflow-hidden p-1"
						>
							<div class="flex items-center gap-4 p-4 pl-6">
								<div class="w-14 h-14 bg-gray-200 dark:bg-zinc-800 rounded-xl shrink-0"></div>
								<div class="flex-1 space-y-2">
									<div class="w-24 h-5 bg-gray-200 dark:bg-zinc-800 rounded-lg"></div>
									<div class="w-36 h-6 bg-gray-200 dark:bg-zinc-800 rounded-lg"></div>
								</div>
								<div class="w-20 h-5 bg-gray-200 dark:bg-zinc-800 rounded-lg hidden sm:block"></div>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- 2-Shot Skeleton -->
			<div class="md:col-span-4 lg:col-span-4 mt-4 md:mt-0 order-1 md:order-2">
				<div class="flex items-center justify-between mb-6">
					<div class="w-24 h-6 md:h-8 bg-gray-200 dark:bg-zinc-800 rounded-lg"></div>
					<div class="w-16 h-6 bg-gray-200 dark:bg-zinc-800 rounded-full"></div>
				</div>
				<div class="space-y-3">
					{#each Array(2) as _}
						<div
							class="flex items-center gap-4 bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 p-3 rounded-2xl"
						>
							<div class="w-12 h-12 rounded-xl bg-gray-200 dark:bg-zinc-800 shrink-0"></div>
							<div class="flex-1 space-y-2">
								<div class="w-28 h-5 bg-gray-200 dark:bg-zinc-800 rounded-lg"></div>
								<div class="w-10 h-4 bg-gray-200 dark:bg-zinc-800 rounded"></div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>
