<script lang="ts">
	import { goto } from '$app/navigation';
	import { ArrowLeft } from 'lucide-svelte';
	import { type ComponentType } from 'svelte';
	import { pageHeaderStore } from '$lib/stores';
	import { onDestroy } from 'svelte';

	/**
	 * Reusable page header component with icon, title, subtitle, and optional back button
	 */
	interface Props {
		icon?: ComponentType;
		title: string;
		subtitle?: string;
		badge?: string;
		actionItems?: Array<{
			icon?: ComponentType;
			label?: string;
			onClick: () => void;
			theme?: string;
		}>;
		rotation?: number;
		theme?:
			| 'red'
			| 'blue'
			| 'green'
			| 'purple'
			| 'pink'
			| 'amber'
			| 'yellow'
			| 'orange'
			| 'rose'
			| 'indigo';
		showBackButton?: boolean;
		backUrl?: string;
		loading?: boolean;
		hidden?: boolean;
		actions?: import('svelte').Snippet;
		onback?: () => void;
	}

	let {
		icon,
		title,
		subtitle = '',
		badge,
		actionItems,
		rotation = -6,
		theme = 'red',
		showBackButton = false,
		backUrl,
		loading = false,
		hidden = false,
		actions,
		onback
	}: Props = $props();

	const themeClasses = {
		red: {
			bg: 'bg-red-50 dark:bg-red-500/20',
			text: 'text-red-600 dark:text-red-400',
			shadow: 'shadow-red-100 dark:shadow-red-900/30',
			underline: 'bg-red-200/60 dark:bg-red-500/30'
		},
		blue: {
			bg: 'bg-blue-50 dark:bg-blue-500/20',
			text: 'text-blue-600 dark:text-blue-400',
			shadow: 'shadow-blue-100 dark:shadow-blue-900/30',
			underline: 'bg-blue-200/60 dark:bg-blue-500/30'
		},
		green: {
			bg: 'bg-emerald-50 dark:bg-emerald-500/20',
			text: 'text-emerald-600 dark:text-emerald-400',
			shadow: 'shadow-emerald-100 dark:shadow-emerald-900/30',
			underline: 'bg-emerald-200/60 dark:bg-emerald-500/30'
		},
		purple: {
			bg: 'bg-purple-50 dark:bg-purple-500/20',
			text: 'text-purple-600 dark:text-purple-400',
			shadow: 'shadow-purple-100 dark:shadow-purple-900/30',
			underline: 'bg-purple-200/60 dark:bg-purple-500/30'
		},
		pink: {
			bg: 'bg-pink-50 dark:bg-pink-500/20',
			text: 'text-pink-600 dark:text-pink-400',
			shadow: 'shadow-pink-100 dark:shadow-pink-900/30',
			underline: 'bg-pink-200/60 dark:bg-pink-500/30'
		},
		amber: {
			bg: 'bg-amber-50 dark:bg-amber-500/20',
			text: 'text-amber-600 dark:text-amber-400',
			shadow: 'shadow-amber-100 dark:shadow-amber-900/30',
			underline: 'bg-amber-200/60 dark:bg-amber-500/30'
		},
		yellow: {
			bg: 'bg-yellow-50 dark:bg-yellow-500/20',
			text: 'text-yellow-600 dark:text-yellow-400',
			shadow: 'shadow-yellow-100 dark:shadow-yellow-900/30',
			underline: 'bg-yellow-200/60 dark:bg-yellow-500/30'
		},
		orange: {
			bg: 'bg-orange-50 dark:bg-orange-500/20',
			text: 'text-orange-600 dark:text-orange-400',
			shadow: 'shadow-orange-100 dark:shadow-orange-900/30',
			underline: 'bg-orange-200/60 dark:bg-orange-500/30'
		},
		rose: {
			bg: 'bg-rose-50 dark:bg-rose-500/20',
			text: 'text-rose-600 dark:text-rose-400',
			shadow: 'shadow-rose-100 dark:shadow-rose-900/30',
			underline: 'bg-rose-200/60 dark:bg-rose-500/30'
		},
		indigo: {
			bg: 'bg-indigo-50 dark:bg-indigo-500/20',
			text: 'text-indigo-600 dark:text-indigo-400',
			shadow: 'shadow-indigo-100 dark:shadow-indigo-900/30',
			underline: 'bg-indigo-200/60 dark:bg-indigo-500/30'
		}
	};

	let colors = $derived(themeClasses[theme]);

	const handleBack = () => {
		if (backUrl) {
			goto(backUrl);
		} else {
			onback?.();
		}
	};

	$effect(() => {
		if (title) {
			pageHeaderStore.set({
				title,
				subtitle,
				badge,
				loading,
				icon,
				theme,
				showBackButton,
				handleBack,
				actions: actionItems
			});
		}
	});

	onDestroy(() => {
		pageHeaderStore.reset();
	});
</script>

{#if !hidden}
	<div
		class="flex flex-row flex-wrap items-center justify-between w-full gap-y-3 gap-x-2 sm:gap-x-4 md:gap-x-6 px-0"
	>
		<div class="hidden sm:flex items-center gap-2 sm:gap-4 min-w-0">
			{#if showBackButton}
				<button
					onclick={handleBack}
					class="p-2 sm:p-2.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-700 dark:hover:text-gray-200 transition-colors cursor-pointer flex-shrink-0"
				>
					<ArrowLeft class="w-4 h-4 sm:w-5 sm:h-5" />
				</button>
			{/if}

			{#if icon}
				{@const IconComponent = icon}
				<div
					class="p-1.5 rounded-lg sm:p-3 sm:rounded-2xl {colors.bg} {colors.text} shadow-lg {colors.shadow} border-2 border-white dark:border-gray-800 flex-shrink-0"
					style="transform: rotate({rotation}deg)"
				>
					<IconComponent class="w-4 h-4 sm:w-6 sm:h-6" />
				</div>
			{/if}

			<div class="min-w-0">
				<h2
					class="text-xl sm:text-2xl lg:text-3xl font-black text-themed tracking-tighter sm:tracking-tight leading-none relative w-fit truncate max-w-full"
				>
					{title}
					<span
						class={`absolute -bottom-1 left-0 w-full h-1.5 sm:h-2.5 ${colors.underline} -z-10 transform -skew-x-12 rounded-sm`}
					></span>
				</h2>
				{#if subtitle}
					<p
						class="text-[11px] sm:text-xs md:text-sm text-gray-500 dark:text-gray-400 mt-1 sm:mt-1.5 font-medium line-clamp-1"
					>
						{subtitle}
					</p>
				{/if}
			</div>
		</div>

		{#if actions}
			<div
				class={`flex items-center gap-1.5 sm:gap-3 justify-end ml-auto sm:ml-0 py-2 overflow-visible max-w-full ${actionItems ? 'hidden sm:flex' : ''}`}
			>
				{@render actions()}
			</div>
		{/if}
	</div>
{/if}
