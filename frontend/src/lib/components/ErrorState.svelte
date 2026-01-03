<script lang="ts">
	import { Ticket } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	export let title: string = 'Failed to load data';
	export let description: string = 'Something went wrong while fetching the information.';
	export let onRetry: (() => void) | undefined = undefined;
	export let icon: any = Ticket;
</script>

<div class="min-h-[50vh] flex flex-col items-center justify-center p-8 text-center animate-fade-in">
	<div class="bg-red-50 dark:bg-red-900/20 p-4 rounded-full mb-4">
		<svelte:component this={icon} class="w-8 h-8 text-red-500" />
	</div>
	<h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">{title}</h3>
	<p class="text-gray-500 dark:text-gray-400 mb-6">
		{description}
	</p>
	{#if onRetry}
		<button
			on:click={onRetry}
			class="px-6 py-2.5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl font-medium hover:scale-105 transition-transform cursor-pointer"
		>
			{$t('errors.tryAgain') || 'Try Again'}
		</button>
	{/if}
</div>
