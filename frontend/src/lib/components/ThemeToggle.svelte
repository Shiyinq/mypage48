<script lang="ts">
	import { theme, setTheme } from '$lib/stores/theme';
	import { Sun, Moon } from 'lucide-svelte';
	import { fly } from 'svelte/transition';

	function toggleTheme() {
		if ($theme === 'dark') {
			setTheme('light');
		} else {
			setTheme('dark');
		}
	}
</script>

<button
	on:click={toggleTheme}
	class="relative w-10 h-10 rounded-full flex items-center justify-center bg-white/50 dark:bg-zinc-800/50 backdrop-blur-md border border-gray-200/50 dark:border-zinc-700/50 shadow-sm hover:bg-white dark:hover:bg-zinc-700 transition-all active:scale-95 group cursor-pointer"
	aria-label="Toggle theme"
>
	{#if $theme === 'dark'}
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
