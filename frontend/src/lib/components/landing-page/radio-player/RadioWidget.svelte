<script lang="ts">
	import { fly } from 'svelte/transition';
	import { radioStore } from '$lib/stores/radio';
	import RadioPlayer from './RadioPlayer.svelte';
	import { Radio as RadioIcon } from 'lucide-svelte';

	let isRadioOpen = $state(false);
</script>

<!-- Radio Player Toggle -->
<div class="relative z-[110] hidden lg:block">
	<button
		class="p-2.5 rounded-full bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 text-slate-900 dark:text-white shadow-sm transition-all active:scale-95 cursor-pointer relative group"
		onclick={() => (isRadioOpen = !isRadioOpen)}
		aria-label="Toggle Radio"
	>
		<RadioIcon
			size={20}
			class="transition-colors {isRadioOpen || $radioStore.isPlaying
				? 'text-red-600 dark:text-red-400'
				: 'text-slate-600 dark:text-slate-400 group-hover:text-red-500'}"
		/>
		{#if $radioStore.isPlaying}
			<span class="absolute top-1.5 right-1.5 flex h-2 w-2">
				<span
					class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"
				></span>
				<span class="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
			</span>
		{/if}
	</button>

	{#if isRadioOpen}
		<!-- Radio Popover -->
		<div
			class="absolute right-0 sm:right-0 top-full mt-4 z-[110]"
			transition:fly={{ y: 10, duration: 300 }}
		>
			<!-- Backdrop for closing -->
			<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
			<div
				class="fixed inset-0 -z-10"
				onclick={() => (isRadioOpen = false)}
				onkeydown={(e) => e.key === 'Escape' && (isRadioOpen = false)}
				role="button"
				tabindex="-1"
				aria-label="Close Radio"
			></div>
			<RadioPlayer />
		</div>
	{/if}
</div>
