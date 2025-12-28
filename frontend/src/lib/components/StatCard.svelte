<script lang="ts">
	import type { ComponentType } from 'svelte';
	import { Eye, EyeOff } from 'lucide-svelte';

	export let title: string;
	export let value: string | number;
	export let sub: string = '';
	export let icon: ComponentType | null = null;
	export let colorClass: string = 'bg-gray-500';
	export let image: string | undefined = undefined;
	export let loading: boolean = false;
	export let hideable: boolean = false;

	// When hideable is true, start with value hidden
	let isHidden = hideable;

	const toggleVisibility = () => {
		isHidden = !isHidden;
	};

	$: isLongText = typeof value === 'string' && value.length > 13;
	// Simple replace for text color
	$: textClass = colorClass.replace('bg-', 'text-');
</script>

<div
	class="glass-card p-6 rounded-3xl relative overflow-hidden group hover:shadow-lg transition-all duration-300 flex flex-col justify-between h-full"
>
	<div
		class={`absolute -top-4 -right-4 w-24 h-24 rounded-full opacity-10 group-hover:scale-110 transition-transform duration-500 ${colorClass}`}
	></div>
	<div class="relative z-10 flex flex-col h-full">
		<div class="flex items-center gap-3 mb-3">
			{#if image}
				<div
					class="w-10 h-10 -ml-1 rounded-full overflow-hidden border-2 border-white dark:border-gray-700 shadow-md flex-shrink-0 bg-gray-100 dark:bg-gray-800"
				>
					<img src={image} alt={title} class="w-full h-full object-cover" />
				</div>
			{:else if icon}
				<div class={`p-2 rounded-xl ${colorClass} bg-opacity-10 text-opacity-100`}>
					<svelte:component this={icon} class={`w-5 h-5 ${textClass}`} />
				</div>
			{/if}
			<p class="text-themed-secondary text-xs font-bold uppercase tracking-wider flex-1">
				{title}
			</p>
			{#if hideable}
				<button
					on:click={toggleVisibility}
					class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer"
					title={isHidden ? 'Show value' : 'Hide value'}
				>
					{#if isHidden}
						<EyeOff class="w-4 h-4" />
					{:else}
						<Eye class="w-4 h-4" />
					{/if}
				</button>
			{/if}
		</div>

		{#if loading}
			<!-- Skeleton Loading State for Value & Sub -->
			<div class="flex-1 flex flex-col justify-center">
				<div class="h-8 w-24 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
			</div>
			<div class="h-3 w-32 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse mt-1.5"></div>
		{:else}
			<div class="flex-1 flex flex-col justify-center">
				<h3
					class={`font-extrabold text-themed ${isLongText ? 'text-lg leading-tight line-clamp-2' : 'text-3xl'} ${hideable && isHidden ? 'blur-md select-none' : ''}`}
				>
					{value}
				</h3>
			</div>

			{#if sub}
				<p
					class="text-xs text-gray-400 mt-1.5 font-medium truncate"
					title={typeof sub === 'string' ? sub : ''}
				>
					{sub}
				</p>
			{/if}
		{/if}
	</div>
</div>
