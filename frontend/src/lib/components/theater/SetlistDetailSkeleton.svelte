<script lang="ts">
</script>

<div class="animate-pulse space-y-8">
	<!-- Hero Skeleton -->
	<div
		class="relative w-full min-h-[400px] rounded-[2.5rem] overflow-hidden mb-8 bg-gray-200 dark:bg-zinc-800"
	>
		<div
			class="absolute inset-0 bg-gradient-to-t from-gray-900/60 via-gray-900/30 to-transparent"
		></div>
		<div
			class="absolute inset-0 bg-gradient-to-r from-gray-900/80 via-transparent to-transparent"
		></div>
		<div class="relative z-10 p-6 md:p-12 w-full flex items-end h-full">
			<div class="flex items-start justify-between gap-6 w-full">
				<div class="space-y-3 md:space-y-4 max-w-full md:max-w-2xl">
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

	<!-- Main Content Grid -->
	<div class="grid grid-cols-1 md:grid-cols-12 gap-6 md:gap-8">
		<!-- Left Column -->
		<div class="md:col-span-8 space-y-8">
			<!-- Stats Cards -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
				<div
					class="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 p-4 md:p-5 rounded-2xl"
				>
					<div class="w-10 h-10 bg-gray-200 dark:bg-zinc-800 rounded-xl mb-3"></div>
					<div class="w-28 h-8 bg-gray-200 dark:bg-zinc-800 rounded-lg mb-1"></div>
					<div class="w-36 h-4 bg-gray-200 dark:bg-zinc-800 rounded-lg"></div>
				</div>
				<div
					class="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 p-4 md:p-5 rounded-2xl"
				>
					<div class="w-10 h-10 bg-gray-200 dark:bg-zinc-800 rounded-xl mb-3"></div>
					<div class="w-28 h-8 bg-gray-200 dark:bg-zinc-800 rounded-lg mb-1"></div>
					<div class="w-36 h-4 bg-gray-200 dark:bg-zinc-800 rounded-lg"></div>
				</div>
			</div>

			<!-- Ticket History Section -->
			<div>
				<div class="flex items-center justify-between mb-6">
					<div class="w-36 h-7 md:h-8 bg-gray-200 dark:bg-zinc-800 rounded-lg"></div>
					<div class="w-20 h-6 bg-gray-200 dark:bg-zinc-800 rounded-full"></div>
				</div>

				<div class="space-y-3">
					{#each Array(3) as _}
						<div
							class="bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 overflow-hidden"
						>
							<div class="flex items-center gap-4 p-4 pl-6">
								<div
									class="w-14 h-14 bg-gray-200 dark:bg-zinc-800 rounded-xl border border-gray-100 dark:border-zinc-700"
								></div>
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
		</div>

		<!-- Right Column -->
		<div class="md:col-span-4 space-y-6">
			<!-- Quick Stats Card -->
			<div
				class="bg-gradient-to-br from-gray-900 to-gray-800 rounded-[2rem] p-6 md:p-8 shadow-xl relative overflow-hidden"
			>
				<div class="absolute top-0 right-0 p-8 opacity-5">
					<div class="w-32 h-32 bg-gray-700 rounded-2xl rotate-12"></div>
				</div>
				<div class="w-40 h-6 bg-gray-700 rounded-lg mb-6"></div>
				<div class="space-y-6 relative z-10">
					<div>
						<div class="w-32 h-4 bg-gray-700 rounded mb-2"></div>
						<div class="w-24 h-8 md:h-9 bg-gray-700 rounded-lg"></div>
					</div>
					<div class="h-px bg-white/10"></div>
					<div>
						<div class="w-28 h-4 bg-gray-700 rounded mb-2"></div>
						<div class="w-16 h-9 md:h-10 bg-gray-700 rounded-lg mb-3"></div>
						<div class="w-full h-1.5 bg-gray-700 rounded-full"></div>
					</div>
				</div>
			</div>

			<!-- Timeline Card Skeleton -->
			<div
				class="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 rounded-3xl p-6"
			>
				<div class="w-28 h-6 bg-gray-200 dark:bg-zinc-800 rounded-lg mb-6"></div>
				<div
					class="relative pl-6 space-y-8 border-l-2 border-dashed border-gray-200 dark:border-zinc-700 ml-2"
				>
					<div class="relative">
						<div class="w-16 h-3 bg-gray-200 dark:bg-zinc-800 rounded mb-1"></div>
						<div class="w-44 h-5 bg-gray-200 dark:bg-zinc-800 rounded-lg"></div>
					</div>
					<div class="relative">
						<div class="w-16 h-3 bg-gray-200 dark:bg-zinc-800 rounded mb-1"></div>
						<div class="w-44 h-5 bg-gray-200 dark:bg-zinc-800 rounded-lg"></div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
