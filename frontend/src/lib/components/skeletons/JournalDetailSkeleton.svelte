<script lang="ts">
	let isWide = $state(false);

	$effect(() => {
		if (typeof window !== 'undefined') {
			isWide = window.innerWidth >= 768;
			const mq = window.matchMedia('(min-width: 768px)');
			const handler = (e: MediaQueryListEvent) => (isWide = e.matches);
			mq.addEventListener('change', handler);
			return () => mq.removeEventListener('change', handler);
		}
	});
</script>

<div
	class="h-[calc(100vh-64px)] flex flex-col bg-slate-50/50 dark:bg-zinc-900/40 overflow-hidden relative overscroll-none"
>
	<div class="flex-1 flex flex-col md:flex-row overflow-hidden relative">
		<!-- Sidebar (full screen mobile, 320px desktop) -->
		<div
			class="h-full overflow-hidden border-r border-gray-100 dark:border-white/5 shrink-0
				   {isWide ? 'md:w-[320px]' : 'w-full'}
				   bg-white dark:bg-zinc-900/60 backdrop-blur-md z-30"
		>
			<div class="w-full h-full flex flex-col overflow-hidden">
				<!-- Header -->
				<div
					class="flex p-3 border-b border-gray-100 dark:border-white/5 bg-white/95 dark:bg-zinc-950/95 backdrop-blur z-10 flex-shrink-0 justify-between items-center"
				>
					<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-16 animate-pulse"></div>
					<div class="flex items-center gap-2">
						<div class="w-8 h-5 bg-gray-200 dark:bg-zinc-700 rounded-full animate-pulse"></div>
						<div class="w-5 h-5 bg-gray-200 dark:bg-zinc-700 rounded-lg animate-pulse"></div>
					</div>
				</div>
				<!-- Filter Bar -->
				<div
					class="px-3 py-2 border-b border-gray-100 dark:border-white/5 bg-white/50 dark:bg-zinc-950/50"
				>
					<div class="h-8 bg-gray-200 dark:bg-zinc-700 rounded-lg w-full animate-pulse"></div>
				</div>
				<!-- Ticket List -->
				<div class="flex-1 overflow-y-auto px-2 py-3 overscroll-contain">
					<div class="space-y-2">
						{#each Array(5) as _}
							<div
								class="animate-pulse px-3 py-2.5 rounded-lg bg-white/50 dark:bg-zinc-800/50 border border-gray-100 dark:border-white/5 w-full flex flex-col gap-2"
							>
								<div class="flex items-center justify-between">
									<div class="h-[9px] bg-gray-200 dark:bg-zinc-700 rounded w-20"></div>
									<div class="h-[9px] bg-gray-200 dark:bg-zinc-700 rounded w-10"></div>
								</div>
								<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-3/4"></div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>

		<!-- Main Content (desktop only) -->
		{#if isWide}
			<div class="flex-1 flex flex-col relative overflow-hidden">
				<div class="h-full flex flex-col relative w-full bg-white dark:bg-zinc-950">
					<div
						class="px-4 md:px-8 py-4 shrink-0 bg-white/95 dark:bg-zinc-950/95 backdrop-blur-md sticky top-0 z-20"
					>
						<div class="flex items-start justify-between gap-3 md:gap-4 w-full max-w-3xl mx-auto">
							<div class="flex-1 space-y-3 animate-pulse">
								<div class="h-8 bg-gray-200 dark:bg-zinc-700 rounded-lg w-2/3"></div>
								<div class="h-5 bg-gray-200 dark:bg-zinc-700 rounded-full w-40"></div>
							</div>
							<div class="flex items-center gap-2 shrink-0 pt-1 animate-pulse">
								<div class="w-5 h-5 bg-gray-200 dark:bg-zinc-700 rounded"></div>
								<div class="w-16 h-7 bg-gray-200 dark:bg-zinc-700 rounded-lg"></div>
							</div>
						</div>
					</div>
					<div class="flex-1 overflow-y-auto px-6 md:px-10 py-6 flex justify-center">
						<div class="w-full max-w-3xl flex flex-col min-h-full animate-pulse space-y-4">
							<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-full"></div>
							<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-5/6"></div>
							<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-4/5"></div>
							<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-3/4"></div>
							<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-2/3"></div>
							<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-5/6"></div>
							<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-1/2"></div>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>
