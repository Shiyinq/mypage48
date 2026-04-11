<script lang="ts">
	import { page } from '$app/stores';
	import { ArrowLeft } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';
	import NavLogo from '$lib/components/navigation/NavLogo.svelte';
	import { pageHeaderStore } from '$lib/stores/ui';

	const { t } = useTranslation();

	$: headerInfo = $pageHeaderStore;
	
	let lastScrollY = 0;
	let isHidden = false;
	const threshold = 10;

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

	function handleScroll() {
		const currentScrollY = window.scrollY;
		const delta = Math.abs(currentScrollY - lastScrollY);

		if (delta < threshold) return;

		if (currentScrollY > lastScrollY && currentScrollY > 80) {
			isHidden = true;
		} else {
			isHidden = false;
		}
		lastScrollY = currentScrollY;
	}
</script>

<svelte:window on:scroll={handleScroll} />

<header
	class="md:hidden bg-white/95 dark:bg-zinc-950/95 backdrop-blur-xl border-b border-gray-200 dark:border-zinc-800 sticky top-0 z-50 transition-transform duration-300 ease-in-out {isHidden ? '-translate-y-full' : 'translate-y-0'}"
>
	<div class="h-16 px-4 flex items-center justify-between gap-4">
		<!-- Left: Title & Icon -->
		<div class="flex items-center min-w-0 flex-1 gap-2">
			{#if headerInfo}
				{@const activeTheme = themeClasses[headerInfo.theme || 'red']}
				<div class="flex items-center gap-2 min-w-0 flex-shrink">
					{#if headerInfo.showBackButton}
						<button
							on:click={headerInfo.handleBack}
							class="p-1.5 rounded-full bg-gray-100 dark:bg-zinc-800 text-gray-500 dark:text-gray-400 flex-shrink-0 cursor-pointer"
						>
							<ArrowLeft class="w-4 h-4" />
						</button>
					{/if}
					{#if headerInfo.icon}
						<div class="p-1.5 rounded-md {activeTheme} flex-shrink-0">
							<svelte:component this={headerInfo.icon} class="w-4 h-4" />
						</div>
					{/if}
					<h1 class="font-black text-sm uppercase tracking-tight text-themed truncate leading-none pt-0.5">
						{headerInfo.title}
					</h1>
				</div>

				<!-- Mobile Actions -->
				{#if headerInfo.actions && headerInfo.actions.length > 0}
					<div class="flex items-center gap-1.5 ml-auto mr-1 flex-shrink-0">
						{#each headerInfo.actions as action}
							<button
								on:click={action.onClick}
								class={`p-1.5 rounded-full transition-colors cursor-pointer ${
									action.theme === 'red'
										? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border border-red-100 dark:border-red-800'
										: 'bg-gray-50 dark:bg-zinc-800 text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-700'
								}`}
								title={action.label}
							>
								<svelte:component this={action.icon} class="w-4 h-4" />
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
