<script lang="ts">
	import { RotateCcw, AlertTriangle } from 'lucide-svelte';

	export let onRetry: () => void;
	export let error: Error | null = null;
</script>

<div class="fixed inset-0 z-[9999] flex items-center justify-center bg-gray-50 dark:bg-black p-4">
	<div class="text-center max-w-md w-full">
		<div
			class="w-20 h-20 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-6"
		>
			<AlertTriangle class="w-10 h-10 text-red-600 dark:text-red-400" />
		</div>

		<h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">Something went wrong</h1>

		<p class="text-gray-600 dark:text-gray-400 mb-8">
			We encountered an unexpected error. Please try reloading the page.
		</p>

		{#if error && import.meta.env.DEV}
			<div
				class="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg text-left mb-8 overflow-auto max-h-40 text-xs font-mono"
			>
				<p class="text-red-800 dark:text-red-200 font-bold mb-1">{error.name}: {error.message}</p>
			</div>
		{/if}

		<button
			on:click={onRetry}
			class="inline-flex items-center gap-2 px-6 py-3 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl font-bold hover:bg-black dark:hover:bg-gray-100 transition-colors cursor-pointer"
		>
			<RotateCcw class="w-4 h-4" />
			Reload Application
		</button>
	</div>
</div>
