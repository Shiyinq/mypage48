<script lang="ts">
	import { liveList, liveLoading } from '$lib/stores/live.svelte';
	import { liveNavbarStore } from '$lib/stores/liveNavbar.svelte';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import { fade } from 'svelte/transition';

	let idnCount = $derived(liveList.value.filter((l) => l.platform?.toLowerCase() === 'idn').length);
	let showroomCount = $derived(
		liveList.value.filter((l) => l.platform?.toLowerCase() === 'showroom').length
	);
	let totalCount = $derived(liveList.value.length);
	let isLoading = $derived(liveLoading.value && totalCount === 0);

	$effect(() => {
		liveNavbarStore.rightSnippet = rightActions;
		return () => {
			if (liveNavbarStore.rightSnippet === rightActions) {
				liveNavbarStore.rightSnippet = undefined;
			}
		};
	});
</script>

{#snippet rightActions()}
	<div
		in:fade={{ duration: 200 }}
		class="flex items-center gap-2 sm:gap-3 bg-white/50 dark:bg-zinc-900/50 px-2 sm:px-3 py-1.5 rounded-full border border-black/5 dark:border-white/5 shadow-sm min-h-[32px] min-w-[64px] justify-center"
	>
		{#if isLoading}
			<div class="flex items-center gap-1.5 px-1">
				<div class="w-4 h-4 rounded-full bg-slate-200 dark:bg-zinc-800 animate-pulse"></div>
				<div class="w-6 h-3 rounded-full bg-slate-200 dark:bg-zinc-800 animate-pulse"></div>
			</div>
		{:else}
			{#if totalCount > 0}
				<div class="flex items-center justify-center relative ml-0.5 sm:ml-1">
					<div class="absolute w-2 h-2 bg-red-500 rounded-full animate-ping opacity-75"></div>
					<div class="relative w-1.5 h-1.5 bg-red-600 dark:bg-red-500 rounded-full"></div>
				</div>
				<div class="w-px h-3 bg-black/10 dark:bg-white/10"></div>
			{/if}

			{#if idnCount > 0}
				<div class="flex items-center gap-1.5">
					<span class="text-xs font-bold text-slate-700 dark:text-zinc-300">{idnCount}</span>
					<PlatformLogo platform="idn" size="xs" />
				</div>
			{/if}

			{#if showroomCount > 0}
				{#if idnCount > 0}
					<div class="w-px h-3 bg-black/10 dark:bg-white/10"></div>
				{/if}
				<div class="flex items-center gap-1.5">
					<span class="text-xs font-bold text-slate-700 dark:text-zinc-300">{showroomCount}</span>
					<PlatformLogo platform="showroom" size="xs" />
				</div>
			{/if}

			{#if totalCount === 0}
				<span class="text-xs font-medium text-slate-400 dark:text-zinc-500 italic px-1"
					>Offline</span
				>
			{/if}
		{/if}
	</div>
{/snippet}
