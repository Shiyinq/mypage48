<script lang="ts">
	import { PanelLeft } from 'lucide-svelte';
	import { browser } from '$app/environment';
	let isWide = $state(browser ? window.innerWidth >= 768 : true);
	let isSidebarVisible = $state(browser ? window.innerWidth >= 768 : true);

	$effect(() => {
		if (typeof window !== 'undefined') {
			isWide = window.innerWidth >= 768;
			isSidebarVisible = isWide;
			const mq = window.matchMedia('(min-width: 768px)');
			const handler = (e: MediaQueryListEvent) => {
				isWide = e.matches;
				if (isWide) isSidebarVisible = true;
			};
			mq.addEventListener('change', handler);
			return () => mq.removeEventListener('change', handler);
		}
	});
</script>

<div
	class="h-[calc(100vh-64px)] flex flex-col bg-slate-50/50 dark:bg-zinc-900/40 overflow-hidden relative"
>
	<div class="flex-1 flex flex-col md:flex-row overflow-hidden relative">
		<!-- Mobile Overlay -->
		{#if isSidebarVisible && !isWide}
			<button
				class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[55] md:hidden cursor-default w-full h-full border-none p-0 m-0 text-left"
				onclick={() => (isSidebarVisible = false)}
				aria-label="Close sidebar"
			></button>
		{/if}

		<div
			class="h-full overflow-hidden border-r border-gray-100 dark:border-white/5 shrink-0
				   fixed md:absolute inset-0 md:inset-y-0 md:left-0 z-[60] md:z-[40] bg-white md:bg-white/80 dark:bg-zinc-900 md:dark:bg-zinc-900/80 backdrop-blur-md
				   transition-transform duration-300 ease-in-out w-full md:w-64 shadow-2xl md:shadow-none
				   {isSidebarVisible ? 'translate-x-0' : '-translate-x-full'}"
		>
			<div class="w-full md:w-64 h-full flex flex-col overflow-hidden">
				<!-- Header -->
				<div
					class="p-4 pb-2 flex items-center justify-center relative border-b border-gray-100 dark:border-zinc-800/50 shrink-0 bg-white/95 dark:bg-zinc-900/95 backdrop-blur z-10"
				>
					<div class="flex items-center gap-2">
						<div class="w-16 h-7 bg-gray-200 dark:bg-zinc-700 rounded-md"></div>
						<div class="w-20 h-7 bg-gray-200 dark:bg-zinc-700 rounded-md"></div>
					</div>
					<div class="absolute right-3 top-1/2 -translate-y-1/2 p-1.5">
						<div class="w-4 h-4 bg-gray-200 dark:bg-zinc-700 rounded"></div>
					</div>
				</div>
				<!-- Member List -->
				<div class="flex-1 overflow-y-auto custom-scrollbar p-3 pt-2">
					<div class="flex flex-col gap-2">
						{#each [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] as _}
							<div class="px-4 py-2 rounded-2xl flex items-center gap-3">
								<div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-zinc-700 shrink-0"></div>
								<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-24"></div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>

		<!-- Desktop spacer -->
		{#if isWide}
			<div class="hidden md:block shrink-0" style="width: 256px;"></div>
		{/if}

		<!-- Main Content Skeleton -->
		<div class="flex-1 flex flex-col relative overflow-hidden">
			<!-- Floating Toggle Button -->
			{#if !isSidebarVisible}
				<div class="absolute top-3 left-0 z-[20]">
					<button
						onclick={() => (isSidebarVisible = true)}
						class="flex items-center justify-center w-8 h-10 bg-white dark:bg-zinc-900 border-y border-r border-gray-200 dark:border-white/10 rounded-r-xl shadow-lg text-gray-400 hover:text-red-500 transition-all hover:w-10 active:scale-95 cursor-pointer"
					>
						<PanelLeft class="w-4 h-4 ml-1" />
					</button>
				</div>
			{/if}

			<div
				class="flex-1 flex flex-col overflow-y-auto md:overflow-y-auto custom-scrollbar bg-white dark:bg-zinc-900 relative pb-16 md:pb-0"
			>
				<div class="w-full max-w-6xl mx-auto p-4 md:p-8 space-y-10 animate-pulse">
					<!-- Bio Card Skeleton -->
					<div
						class="flex flex-col md:flex-row gap-6 md:gap-8 bg-gray-50/30 dark:bg-zinc-800/20 rounded-3xl p-4 md:p-6 border border-gray-100 dark:border-zinc-800/50"
					>
						<div
							class="w-full md:w-72 aspect-[4/5] rounded-2xl bg-gray-200 dark:bg-zinc-700 shrink-0"
						></div>
						<div class="flex-1 space-y-3 pt-2">
							<div class="h-8 bg-gray-200 dark:bg-zinc-700 rounded-lg w-2/3"></div>
							<div class="h-5 bg-gray-200 dark:bg-zinc-700 rounded w-1/4"></div>
							<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-1/3"></div>
							<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-1/2"></div>
							<div class="h-10 bg-gray-200 dark:bg-zinc-700 rounded-xl w-full mt-4"></div>
							<div class="h-10 bg-gray-200 dark:bg-zinc-700 rounded-xl w-full"></div>
						</div>
					</div>

					<!-- Stats Grid Skeleton -->
					<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
						<div
							class="bg-white/60 dark:bg-zinc-900/40 rounded-3xl p-6 border border-gray-100 dark:border-zinc-800 space-y-4"
						>
							<div class="h-8 w-1.5 rounded-full bg-gray-300 dark:bg-zinc-600"></div>
							<div class="grid grid-cols-2 gap-3">
								<div
									class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
								>
									<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16"></div>
									<div class="h-8 bg-gray-200 dark:bg-zinc-700 rounded w-10"></div>
								</div>
								<div
									class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
								>
									<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16"></div>
									<div class="h-8 bg-gray-200 dark:bg-zinc-700 rounded w-10"></div>
								</div>
								<div
									class="col-span-2 bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
								>
									<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-24"></div>
									<div class="h-5 bg-gray-200 dark:bg-zinc-700 rounded w-32"></div>
								</div>
							</div>
						</div>
						<div
							class="bg-white/60 dark:bg-zinc-900/40 rounded-3xl p-6 border border-gray-100 dark:border-zinc-800 space-y-4"
						>
							<div class="h-8 w-1.5 rounded-full bg-gray-300 dark:bg-zinc-600"></div>
							<div class="grid grid-cols-2 gap-3">
								<div
									class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
								>
									<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16"></div>
									<div class="h-8 bg-gray-200 dark:bg-zinc-700 rounded w-10"></div>
								</div>
								<div
									class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
								>
									<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16"></div>
									<div class="h-5 bg-gray-200 dark:bg-zinc-700 rounded w-20"></div>
								</div>
								<div
									class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
								>
									<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16"></div>
									<div class="h-5 bg-gray-200 dark:bg-zinc-700 rounded w-12"></div>
								</div>
								<div
									class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
								>
									<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-20"></div>
									<div class="h-5 bg-gray-200 dark:bg-zinc-700 rounded w-24"></div>
								</div>
							</div>
						</div>
					</div>

					<!-- Shows & Live List Skeleton -->
					<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
						<div class="space-y-4">
							<div class="h-8 w-1.5 rounded-full bg-gray-300 dark:bg-zinc-600"></div>
							<div class="space-y-2">
								{#each [1, 2, 3] as _}
									<div
										class="flex items-center gap-3 p-3 rounded-xl bg-gray-50/30 dark:bg-zinc-800/20 border border-gray-100 dark:border-zinc-800/50"
									>
										<div class="w-10 h-10 rounded-xl bg-gray-200 dark:bg-zinc-700 shrink-0"></div>
										<div class="flex-1 space-y-2">
											<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-2/3"></div>
											<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-1/3"></div>
										</div>
									</div>
								{/each}
							</div>
						</div>
						<div class="space-y-4">
							<div class="h-8 w-1.5 rounded-full bg-gray-300 dark:bg-zinc-600"></div>
							<div class="space-y-2">
								{#each [1, 2, 3] as _}
									<div
										class="flex items-center gap-3 p-3 rounded-xl bg-gray-50/50 dark:bg-zinc-800/20 border border-gray-100 dark:border-zinc-800/50"
									>
										<div class="w-10 h-10 rounded-xl bg-gray-200 dark:bg-zinc-700 shrink-0"></div>
										<div class="flex-1 space-y-2">
											<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-2/3"></div>
											<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-1/2"></div>
										</div>
									</div>
								{/each}
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
