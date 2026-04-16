<script lang="ts">
	import type { ComponentType } from 'svelte';
	import { Eye, EyeOff, Crown } from 'lucide-svelte';
	import { OptimizedImage } from '$lib/components/common';

	interface Props {
		title: string;
		value: string | number;
		sub?: string;
		icon?: ComponentType | null;
		theme?: 'red' | 'emerald' | 'amber' | 'purple' | 'pink' | 'blue' | 'gray';
		image?: string | undefined;
		loading?: boolean;
		hideable?: boolean;
		showCrown?: boolean;
		detail?: string | undefined;
	}

	let {
		title,
		value,
		sub = '',
		icon = null,
		theme = 'gray',
		image = undefined,
		loading = false,
		hideable = false,
		showCrown = false,
		detail = undefined
	}: Props = $props();

	// Map themes to classes
	const themes = {
		red: {
			card: 'bg-red-50/20 dark:bg-transparent border-red-100 dark:border-red-500/20',
			icon: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
			text: 'text-red-500' // Darker red for title
		},
		emerald: {
			card: 'bg-emerald-50/20 dark:bg-transparent border-emerald-100 dark:border-emerald-500/20',
			icon: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400',
			text: 'text-emerald-500'
		},
		amber: {
			card: 'bg-amber-50/20 dark:bg-transparent border-amber-100 dark:border-amber-500/20',
			icon: 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400',
			text: 'text-amber-500'
		},
		purple: {
			card: 'bg-purple-50/20 dark:bg-transparent border-purple-100 dark:border-purple-500/20',
			icon: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
			text: 'text-purple-500'
		},
		pink: {
			card: 'bg-pink-50/20 dark:bg-transparent border-pink-100 dark:border-pink-500/20',
			icon: 'bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400',
			text: 'text-pink-500'
		},
		blue: {
			card: 'bg-blue-50/20 dark:bg-transparent border-blue-100 dark:border-blue-500/20',
			icon: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
			text: 'text-blue-500'
		},
		gray: {
			card: 'bg-gray-50/20 dark:bg-transparent border-gray-100 dark:border-gray-500/20',
			icon: 'bg-gray-100 dark:bg-gray-900/30 text-gray-600 dark:text-gray-400',
			text: 'text-gray-500'
		}
	};

	let selectedTheme = $derived(themes[theme] || themes.gray);

	// When hideable is true, start with value hidden
	let isHidden = $state(false);
	$effect(() => {
		isHidden = hideable;
	});

	const toggleVisibility = () => {
		isHidden = !isHidden;
	};

	let valueStr = $derived(String(value));
	let isSuperLong = $derived(valueStr.length > 12);
	let isVeryLong = $derived(valueStr.length > 8 && valueStr.length <= 12);
	let isMediumLong = $derived(valueStr.length > 4 && valueStr.length <= 8);
</script>

<div
	class={`glass-card p-6 rounded-3xl relative overflow-hidden group hover:shadow-lg transition-all duration-300 flex flex-col justify-between h-full border ${selectedTheme.card}`}
>
	<div class="relative z-10 flex flex-col h-full">
		<div class="flex items-center gap-3 mb-3">
			{#if image}
				<div
					class="w-10 h-10 -ml-1 rounded-full overflow-hidden border-2 border-white dark:border-gray-700 shadow-md flex-shrink-0 bg-gray-100 dark:bg-gray-800"
				>
					<OptimizedImage src={image} alt={title} class="w-full h-full object-cover" />
				</div>
			{:else if icon}
				{@const SvelteComponent = icon}
				<div class={`p-2 rounded-xl ${selectedTheme.icon}`}>
					<SvelteComponent class="w-5 h-5" />
				</div>
			{/if}
			<p
				class={`text-xs font-bold uppercase tracking-wider flex-1 ${selectedTheme.text || 'text-themed-secondary'}`}
			>
				{title}
			</p>
			{#if showCrown}
				<Crown class="w-5 h-5 text-yellow-400 fill-current" />
			{/if}
			{#if hideable}
				<button
					onclick={toggleVisibility}
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
		{:else if isSuperLong}
			<!-- Vertical layout for super long values (like very long currency) -->
			<div class="flex-1 flex flex-col justify-center mt-2">
				<h3
					class={`font-black text-themed leading-none text-3xl tracking-tighter ${hideable && isHidden ? 'blur-md select-none' : ''}`}
					title={valueStr}
				>
					{value}
				</h3>
				{#if sub}
					<p
						class="text-xs font-bold text-gray-400 mt-1.5 uppercase tracking-wider"
						title={typeof sub === 'string' ? sub : ''}
					>
						{sub}
					</p>
				{/if}
			</div>
		{:else if isVeryLong}
			<!-- Vertical layout for very long values (like currency) -->
			<div class="flex-1 flex flex-col justify-center mt-2">
				<h3
					class={`font-black text-themed leading-none text-3xl sm:text-4xl ${hideable && isHidden ? 'blur-md select-none' : ''}`}
					title={valueStr}
				>
					{value}
				</h3>
				{#if sub}
					<p
						class="text-xs font-bold text-gray-400 mt-1.5 uppercase tracking-wider"
						title={typeof sub === 'string' ? sub : ''}
					>
						{sub}
					</p>
				{/if}
			</div>
		{:else}
			<!-- Horizontal layout for short values -->
			<div class="flex-1 flex items-center gap-4 mt-2">
				<!-- Left: Value (Big Char like 'B') -->
				<h3
					class={`font-black text-themed leading-none ${isMediumLong ? 'text-2xl' : 'text-5xl'} ${hideable && isHidden ? 'blur-md select-none' : ''}`}
					title={valueStr}
				>
					{value}
				</h3>

				<!-- Right: Sub & Detail -->
				<div class="flex flex-col justify-center min-w-0 flex-1">
					{#if sub}
						<p
							class="text-[10px] sm:text-xs font-bold text-gray-400 uppercase tracking-wider mb-0.5 truncate"
							title={typeof sub === 'string' ? sub : ''}
						>
							{sub}
						</p>
					{/if}
					{#if detail}
						<p
							class={`text-sm sm:text-base font-bold leading-tight ${selectedTheme.text || 'text-themed-secondary'}`}
						>
							{detail}
						</p>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>
