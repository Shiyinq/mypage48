<script lang="ts">
	import type { ComponentType } from 'svelte';

	interface Props {
		/**
		 * Reusable empty state component for pages with no data
		 */
		icon: ComponentType;
		title: string;
		description?: string;
		className?: string;
		children?: import('svelte').Snippet;
	}

	let { icon, title, description = '', className = '', children }: Props = $props();

	const SvelteComponent = $derived(icon);
</script>

<div class="flex flex-col items-center justify-center min-h-[400px] p-8 text-center {className}">
	<div
		class="w-20 h-20 rounded-full bg-gray-100 dark:bg-zinc-800 flex items-center justify-center mb-6 text-gray-300 dark:text-zinc-600"
	>
		<SvelteComponent class="w-10 h-10" />
	</div>
	<h3 class="text-xl font-bold text-gray-800 dark:text-white mb-2">
		{title}
	</h3>
	{#if description}
		<p class="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
			{description}
		</p>
	{/if}
	{@render children?.()}
</div>
