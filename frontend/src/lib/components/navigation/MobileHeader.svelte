<script lang="ts">
	import { ChevronLeft } from 'lucide-svelte';
	import NavLogo from '$lib/components/navigation/NavLogo.svelte';
	import { pageHeaderStore, isImmersive } from '$lib/stores';

	let headerInfo = $derived(pageHeaderStore.value);

	const themeClasses = {
		red: 'bg-red-50 dark:bg-red-500/20 text-red-600 dark:text-red-400',
		blue: 'bg-blue-50 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400',
		green: 'bg-emerald-50 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400',
		purple: 'bg-purple-50 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400',
		pink: 'bg-pink-50 dark:bg-pink-500/20 text-pink-600 dark:text-pink-400',
		amber: 'bg-amber-50 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400',
		yellow: 'bg-yellow-50 dark:bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
		orange: 'bg-orange-50 dark:bg-orange-500/20 text-orange-600 dark:text-orange-400',
		rose: 'bg-rose-50 dark:bg-rose-500/20 text-rose-600 dark:text-rose-400',
		indigo: 'bg-indigo-50 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400'
	};
</script>

{#if !isImmersive.value}
	<div class="h-16 md:hidden"></div>
	<header
		class="md:hidden bg-white/95 dark:bg-zinc-950/95 backdrop-blur-xl border-b border-gray-200 dark:border-zinc-800 fixed top-0 left-0 right-0 z-[50] transition-all duration-300 ease-in-out"
	>
		<div class="h-16 px-4 flex items-center justify-between gap-4">
			<!-- Left: Title & Icon -->
			<div class="flex items-center min-w-0 flex-1 gap-2">
				{#if headerInfo}
					{@const activeTheme =
						themeClasses[(headerInfo.theme as keyof typeof themeClasses) || 'red']}
					<div class="flex items-center gap-1 min-w-0 flex-1">
						{#if headerInfo.showBackButton}
							<button
								onclick={headerInfo.handleBack}
								class="p-1 -ml-1 hover:bg-gray-100 dark:hover:bg-zinc-800 text-zinc-950 dark:text-white flex-shrink-0 cursor-pointer transition-colors"
							>
								<ChevronLeft class="w-5 h-5" />
							</button>
						{/if}
						{#if headerInfo.icon && !headerInfo.showBackButton}
							<div class="p-1 rounded-md {activeTheme} flex-shrink-0">
								<headerInfo.icon class="w-4 h-4" />
							</div>
						{/if}
						<div class="flex items-center gap-1 min-w-0 flex-1">
							<h1
								class="font-black text-lg tracking-tighter text-zinc-950 dark:text-white truncate leading-none pt-0.5"
							>
								{headerInfo.title}
							</h1>
							{#if headerInfo.badge}
								<div
									class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-zinc-400 leading-none whitespace-nowrap shrink-0 ml-auto flex items-center gap-1.5"
								>
									{#if headerInfo.loading}
										<div
											class="w-2 h-2 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin"
										></div>
									{/if}
									{headerInfo.badge}
								</div>
							{/if}
						</div>
					</div>

					<!-- Mobile Actions -->
					{#if headerInfo.actions && headerInfo.actions.length > 0}
						<div class="flex items-center gap-1.5 ml-auto mr-1 flex-shrink-0">
							{#each headerInfo.actions as action}
								<button
									onclick={action.onClick}
									data-filter-toggle="true"
									class={`rounded-full transition-colors cursor-pointer flex items-center justify-center ${
										action.theme === 'red'
											? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border border-red-100 dark:border-red-800'
											: 'bg-gray-50 dark:bg-zinc-800 text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-700'
									} ${action.icon ? 'p-1.5' : 'px-3 py-1.5'}`}
									title={action.label}
								>
									{#if action.icon}
										<action.icon class="w-4 h-4" />
									{:else if action.label}
										<span class="text-[10px] font-bold whitespace-nowrap">{action.label}</span>
									{/if}
								</button>
							{/each}
						</div>
					{/if}
				{:else}
					<a href="/" class="flex items-center gap-3 cursor-pointer">
						<NavLogo />
					</a>
				{/if}
			</div>
		</div>
	</header>
{/if}
