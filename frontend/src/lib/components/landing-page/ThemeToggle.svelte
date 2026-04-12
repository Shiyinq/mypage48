<script lang="ts">
	import { theme, setTheme } from '$lib/stores/theme';
	import { Sun, Moon } from 'lucide-svelte';
	import { fly } from 'svelte/transition';
	import { onMount } from 'svelte';

	let mounted = $state(false);
	onMount(() => {
		mounted = true;
	});

	let effectiveTheme = $derived(
		$theme === 'auto'
			? mounted && window.matchMedia('(prefers-color-scheme: dark)').matches
				? 'dark'
				: 'light'
			: $theme
	);

	function toggleTheme() {
		// If auto, toggle to the opposite of current effective theme
		if (effectiveTheme === 'dark') {
			setTheme('light');
		} else {
			setTheme('dark');
		}
	}
</script>

<button
	onclick={toggleTheme}
	class="relative w-10 h-10 rounded-full flex items-center justify-center bg-white/50 dark:bg-zinc-800/50 backdrop-blur-md border border-gray-200/50 dark:border-zinc-700/50 shadow-sm hover:bg-white dark:hover:bg-zinc-700 transition-all active:scale-95 group cursor-pointer"
	aria-label="Toggle theme"
>
	{#if effectiveTheme === 'dark'}
		<div in:fly={{ y: 10, duration: 200 }} out:fly={{ y: -10, duration: 200 }} class="absolute">
			<Moon
				class="w-5 h-5 text-indigo-400 group-hover:-rotate-12 transition-transform duration-500"
			/>
		</div>
	{:else}
		<div in:fly={{ y: 10, duration: 200 }} out:fly={{ y: -10, duration: 200 }} class="absolute">
			<Sun
				class="w-5 h-5 text-orange-500 group-hover:rotate-45 transition-transform duration-500"
			/>
		</div>
	{/if}
</button>
