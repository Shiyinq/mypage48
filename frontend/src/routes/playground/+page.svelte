<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { fade } from 'svelte/transition';
	import { PlaygroundSidebar, PlaygroundEndpoint, PlaygroundResponse } from '$lib/components/playground';
	import { LoaderCircle, AlertTriangle } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { playgroundStore, groupedEndpoints, selectedEndpoint, selectedResult } from '$lib/stores/playground';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	onMount(async () => {
		await playgroundStore.init();
	});

	onDestroy(() => {
		playgroundStore.reset();
	});

	async function handleExecute(event: CustomEvent) {
		const { method, path, body, headers } = event.detail;
		
		// The path from the playground may already include /api depending on the openapi.json
		const cleanPath = path.startsWith('/api') ? path.substring(4) : path;
		
		await playgroundStore.execute({
			method: method.toUpperCase(),
			path: cleanPath,
			params: {}, // Already included in path for now
			headers,
			body
		});
	}

	function handleSelect(event: CustomEvent) {
		playgroundStore.selectEndpoint(event.detail.id);
	}

	$: ({ schema, executing, error } = $playgroundStore);
	$: loading = !schema && !error;
</script>

<SEO title={$t('playground.title')} description={$t('playground.description')} />

<div class="h-[calc(100vh-64px)] flex flex-col bg-slate-50/50 dark:bg-zinc-900 overflow-hidden">
	{#if loading}
		<div class="flex-1 flex flex-col items-center justify-center space-y-4" in:fade>
			<LoaderCircle class="w-10 h-10 animate-spin text-red-500" />
			<p class="text-sm font-bold text-gray-500 uppercase tracking-widest">{$t('common.loading')}</p>
		</div>
	{:else if error}
		<div class="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-6" in:fade>
			<div class="w-20 h-20 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
				<AlertTriangle class="w-10 h-10 text-red-600" />
			</div>
			<div class="max-w-md">
				<h2 class="text-2xl font-black text-gray-900 dark:text-white mb-2">{$t('common.error')}</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400 mb-6">{error}</p>
				<button 
					on:click={() => window.location.reload()}
					class="px-6 py-3 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 transition-colors shadow-lg shadow-red-500/20"
				>
					{$t('errors.tryAgain')}
				</button>
			</div>
		</div>
	{:else}
		<div class="flex-1 flex overflow-hidden" in:fade>
			<PlaygroundSidebar 
				groupedEndpoints={$groupedEndpoints} 
				selectedId={$playgroundStore.selectedEndpointId} 
				on:select={handleSelect} 
			/>
			
			<div class="flex-1 flex overflow-hidden">
				<PlaygroundEndpoint 
					openapi={schema}
					endpoint={$selectedEndpoint} 
					{executing} 
					on:execute={handleExecute} 
				/>

				<PlaygroundResponse 
					response={$selectedResult} 
					error={$selectedResult && $selectedResult.status >= 400 ? $selectedResult : null} 
					duration={$selectedResult?.duration} 
				/>
			</div>
		</div>
	{/if}
</div>

<style>
	:global(main) {
		padding: 0 !important;
		max-width: 100% !important;
	}
</style>
