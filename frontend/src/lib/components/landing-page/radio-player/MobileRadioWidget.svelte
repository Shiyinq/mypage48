<script lang="ts">
	import { fly } from 'svelte/transition';
	import { radioStore } from '$lib/stores/radio';
	import RadioPlayer from './RadioPlayer.svelte';
	import { Radio as RadioIcon } from 'lucide-svelte';

	let isRadioOpen = $state(false);
</script>

<button
	class="p-2.5 rounded-full bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 text-slate-900 dark:text-white shadow-sm transition-all active:scale-95 cursor-pointer relative group"
	onclick={() => (isRadioOpen = !isRadioOpen)}
	aria-label="Toggle Radio Mobile"
>
	<RadioIcon
		size={20}
		class={$radioStore.isPlaying || isRadioOpen ? 'text-red-600' : 'text-slate-500'}
	/>
	{#if $radioStore.isPlaying}
		<span class="absolute top-2 right-2 flex h-2 w-2">
			<span
				class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"
			></span>
			<span class="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
		</span>
	{/if}
</button>

{#if isRadioOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[95] lg:hidden"
		onclick={() => (isRadioOpen = false)}
		onkeydown={(e) => e.key === 'Escape' && (isRadioOpen = false)}
		role="button"
		tabindex="-1"
		aria-label="Close Radio"
	></div>

	<div
		class="fixed inset-x-6 bottom-32 z-[100] lg:hidden flex justify-center pointer-events-none"
		transition:fly={{ y: 20, duration: 300 }}
	>
		<div class="pointer-events-auto">
			<RadioPlayer />
		</div>
	</div>
{/if}
