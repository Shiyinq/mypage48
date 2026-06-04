<script lang="ts">
	import type { ComponentType } from 'svelte';
	import type { Icon } from 'lucide-svelte';
	import { ChevronRight } from 'lucide-svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		value?: string | number;
		icon: ComponentType<Icon>;
		color?: 'red' | 'amber' | 'emerald' | 'blue' | 'purple' | 'pink' | 'indigo' | 'orange' | 'zinc';
		href?: string;
		class?: string;
		children?: Snippet; // For custom value content
		subtitle?: Snippet; // For subtitles/sub-values under the main value
	}

	let {
		title,
		value,
		icon: IconComponent,
		color = 'red',
		href,
		class: className = '',
		children,
		subtitle
	}: Props = $props();

	// Map colors to classes to avoid dynamic tailwind class issues
	const colorClasses = {
		red: {
			icon: 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400',
			hoverText: 'group-hover:text-red-600 dark:group-hover:text-red-400',
			hoverBorder: 'hover:border-red-500/50'
		},
		amber: {
			icon: 'bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400',
			hoverText: 'group-hover:text-amber-600 dark:group-hover:text-amber-400',
			hoverBorder: 'hover:border-amber-500/50'
		},
		emerald: {
			icon: 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400',
			hoverText: 'group-hover:text-emerald-600 dark:group-hover:text-emerald-400',
			hoverBorder: 'hover:border-emerald-500/50'
		},
		blue: {
			icon: 'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400',
			hoverText: 'group-hover:text-blue-600 dark:group-hover:text-blue-400',
			hoverBorder: 'hover:border-blue-500/50'
		},
		purple: {
			icon: 'bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400',
			hoverText: 'group-hover:text-purple-600 dark:group-hover:text-purple-400',
			hoverBorder: 'hover:border-purple-500/50'
		},
		pink: {
			icon: 'bg-pink-100 dark:bg-pink-500/20 text-pink-600 dark:text-pink-400',
			hoverText: 'group-hover:text-pink-600 dark:group-hover:text-pink-400',
			hoverBorder: 'hover:border-pink-500/50'
		},
		indigo: {
			icon: 'bg-indigo-100 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400',
			hoverText: 'group-hover:text-indigo-600 dark:group-hover:text-indigo-400',
			hoverBorder: 'hover:border-indigo-500/50'
		},
		orange: {
			icon: 'bg-orange-100 dark:bg-orange-500/20 text-orange-600 dark:text-orange-400',
			hoverText: 'group-hover:text-orange-600 dark:group-hover:text-orange-400',
			hoverBorder: 'hover:border-orange-500/50'
		},
		zinc: {
			icon: 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400',
			hoverText: 'group-hover:text-zinc-900 dark:group-hover:text-white',
			hoverBorder: 'hover:border-zinc-500/50'
		}
	};
</script>

{#if href}
	<a
		{href}
		class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 flex items-center gap-4 transition-all duration-300 min-w-0 hover:shadow-lg hover:-translate-y-1 group {colorClasses[
			color
		].hoverBorder} {className}"
	>
		<div
			class="w-11 h-11 {colorClasses[color]
				.icon} rounded-full flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform"
		>
			<IconComponent size={22} />
		</div>
		<div class="min-w-0 flex-1">
			<p
				class="text-xs text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider truncate"
			>
				{title}
			</p>
			{#if children}
				{@render children()}
			{:else}
				<div class="flex items-baseline gap-1.5 truncate">
					<p class="text-xl font-black truncate transition-colors {colorClasses[color].hoverText}">
						{value}
					</p>
				</div>
			{/if}
			{#if subtitle}
				<div class="mt-0.5 min-w-0">
					{@render subtitle()}
				</div>
			{/if}
		</div>
		<ChevronRight
			size={20}
			class="text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-2"
		/>
	</a>
{:else}
	<div
		class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 min-w-0 {className}"
	>
		<div
			class="w-11 h-11 {colorClasses[color]
				.icon} rounded-full flex items-center justify-center shrink-0"
		>
			<IconComponent size={22} />
		</div>
		<div class="min-w-0">
			<p
				class="text-xs text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider truncate"
			>
				{title}
			</p>
			{#if children}
				{@render children()}
			{:else}
				<p class="text-xl font-black truncate">
					{value}
				</p>
			{/if}
			{#if subtitle}
				<div class="mt-0.5 min-w-0">
					{@render subtitle()}
				</div>
			{/if}
		</div>
	</div>
{/if}
