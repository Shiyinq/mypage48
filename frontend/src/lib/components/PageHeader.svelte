<script lang="ts">
	import { goto } from '$app/navigation';
	import { ArrowLeft } from 'lucide-svelte';
	import { createEventDispatcher, type ComponentType } from 'svelte';

	const dispatch = createEventDispatcher();

	/**
	 * Reusable page header component with icon, title, subtitle, and optional back button
	 */
	export let icon: ComponentType | undefined = undefined;
	export let title: string;
	export let subtitle: string = '';
	export let rotation: number = -6;
	export let theme: 'red' | 'blue' | 'green' | 'purple' | 'pink' | 'amber' | 'yellow' = 'red';
	export let showBackButton = false;
	export let backUrl: string | undefined = undefined;

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
		}
	};

	$: colors = themeClasses[theme];

	const handleBack = () => {
		if (backUrl) {
			goto(backUrl);
		} else {
			dispatch('back');
		}
	};
</script>

<div class="flex flex-row items-center justify-between w-full">
	<div class="flex items-center gap-3">
		{#if showBackButton}
			<button
				on:click={handleBack}
				class="p-2 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-700 dark:hover:text-gray-200 transition-colors cursor-pointer"
			>
				<ArrowLeft class="w-5 h-5" />
			</button>
		{/if}

		{#if icon}
			<div
				class="p-3 rounded-2xl {colors.bg} {colors.text} shadow-lg {colors.shadow} border-2 border-white dark:border-gray-800"
				style="transform: rotate({rotation}deg)"
			>
				<svelte:component this={icon} class="w-6 h-6" />
			</div>
		{/if}

		<div>
			<h2 class="text-2xl font-bold text-themed leading-none relative w-fit">
				{title}
				<span
					class="absolute -bottom-1 left-0 w-full h-2 {colors.underline} -z-10 transform -skew-x-12 rounded-sm"
				></span>
			</h2>
			{#if subtitle}
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
			{/if}
		</div>
	</div>

	<div class="flex items-center gap-2">
		<slot name="actions" />
	</div>
</div>
