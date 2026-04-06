<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { fade } from 'svelte/transition';
	import { PlaygroundSidebar, PlaygroundEndpoint, PlaygroundResponse } from '$lib/components/playground';
	import { LoaderCircle, AlertTriangle, PanelLeft } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { playgroundStore, groupedEndpoints, selectedEndpoint, selectedResult } from '$lib/stores/playground';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	let innerWidth = 0;

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

	$: ({ schema, executing, error, isSidebarVisible, responseWidth } = $playgroundStore);
	$: loading = !schema && !error;

	let isResizing = false;

	function startResizing(e: MouseEvent) {
		isResizing = true;
		window.addEventListener('mousemove', handleMouseMove);
		window.addEventListener('mouseup', stopResizing);
		document.body.style.cursor = 'col-resize';
		document.body.style.userSelect = 'none';
	}

	function handleMouseMove(e: MouseEvent) {
		if (!isResizing) return;
		const newWidth = window.innerWidth - e.clientX;
		
		// Map sidebar width for adaptive clamping
		const sidebarWidth = isSidebarVisible ? (innerWidth >= 768 ? 320 : 0) : 0;
		const minMiddleSpace = 100; // Preserve some space for endpoint title/content

		// Clamp width between 300px and available space
		const minWidth = 300;
		const maxWidth = Math.max(minWidth, innerWidth - sidebarWidth - minMiddleSpace);
		const clampedWidth = Math.max(minWidth, Math.min(newWidth, maxWidth));
		
		playgroundStore.setResponseWidth(clampedWidth);
	}

	function stopResizing() {
		isResizing = false;
		window.removeEventListener('mousemove', handleMouseMove);
		window.removeEventListener('mouseup', stopResizing);
		document.body.style.cursor = 'default';
		document.body.style.userSelect = 'auto';
	}
</script>

<svelte:window bind:innerWidth />

<SEO title={$t('playground.title')} description={$t('playground.description')} />

<div class="h-[calc(100vh-64px)] flex flex-col bg-slate-50/50 dark:bg-zinc-900 overflow-hidden relative">
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
		<div class="flex-1 flex flex-col md:flex-row overflow-hidden relative" in:fade>
			<!-- Mobile Sidebar Backdrop -->
			{#if isSidebarVisible && innerWidth < 768}
				<button 
					on:click={() => playgroundStore.toggleSidebar()}
					class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[55] md:hidden transition-opacity"
					aria-label="Close Sidebar"
					transition:fade={{ duration: 200 }}
				></button>
			{/if}

			<!-- Desktop Content Spacer: Handles the 'Push' layout shift on desktop -->
			{#if innerWidth >= 768}
				<div 
					class="hidden md:block transition-all duration-300 ease-in-out shrink-0 overflow-hidden" 
					style="width: {isSidebarVisible ? '320px' : '0px'}; opacity: {isSidebarVisible ? '1' : '0'};"
				></div>
			{/if}

			<!-- Sidebar Drawer: Consistent translateX animation for all devices -->
			<div 
				class="h-full overflow-hidden border-r border-gray-100 dark:border-white/5 shrink-0
					   absolute inset-y-0 left-0 z-[60] bg-white dark:bg-zinc-900
					   transition-transform duration-300 ease-in-out w-80 shadow-2xl md:shadow-none
					   {isSidebarVisible ? 'translate-x-0' : '-translate-x-full'}"
			>
				<!-- Fixed width inner container to prevent layout shifts during animation -->
				<div class="w-80 h-full"> 
					<PlaygroundSidebar 
						groupedEndpoints={$groupedEndpoints} 
						selectedId={$playgroundStore.selectedEndpointId} 
						on:select={(e) => {
							handleSelect(e);
							if (innerWidth < 768) playgroundStore.toggleSidebar();
						}} 
					/>
				</div>
			</div>
			
			<!-- Main Content Area: Stacked on Mobile, Flex on Desktop -->
			<div class="flex-1 flex flex-col md:flex-row overflow-y-auto md:overflow-hidden relative custom-scrollbar">
				<!-- Floating Toggle Button (Sleek Edge Tab) -->
				{#if !isSidebarVisible}
					<div 
						class="absolute top-3 left-0 z-[20] md:z-0"
						transition:fade={{ duration: 200 }}
					>
						<button 
							on:click={() => playgroundStore.toggleSidebar()}
							class="flex items-center justify-center w-8 h-10 bg-white dark:bg-zinc-900 border-y border-r border-gray-200 dark:border-white/10 rounded-r-xl shadow-lg text-gray-400 hover:text-red-500 transition-all hover:w-10 active:scale-95 cursor-pointer group"
							title={$t('playground.showSidebar')}
						>
							<PanelLeft class="w-4 h-4 ml-1" />
						</button>
					</div>
				{/if}

				<div class="flex-1 min-h-[500px] md:min-h-0 min-w-0 overflow-hidden">
					<PlaygroundEndpoint 
						openapi={schema}
						endpoint={$selectedEndpoint} 
						{executing} 
						on:execute={handleExecute} 
					/>
				</div>

				<!-- Resize Handle (Desktop Only) -->
				<button 
					on:mousedown={startResizing}
					class="hidden md:block absolute top-0 bottom-0 right-0 w-1.5 cursor-col-resize z-10 group"
					style="right: {responseWidth}px; transform: translateX(50%);"
					aria-label="Resize response panel"
				>
					<div class="absolute inset-y-0 left-1/2 w-px bg-gray-100 dark:bg-white/5 group-hover:bg-red-400 group-active:bg-red-500 transition-colors duration-200"></div>
				</button>

				<div 
					class="h-[600px] md:h-full shrink-0 border-t md:border-t-0 border-gray-100 dark:border-white/5"
					style="width: {innerWidth < 768 ? '100%' : responseWidth + 'px'}"
				>
					<PlaygroundResponse 
						response={$selectedResult} 
						error={$selectedResult && $selectedResult.status >= 400 ? $selectedResult : null} 
						duration={$selectedResult?.duration} 
						width={innerWidth < 768 ? innerWidth : responseWidth}
					/>
				</div>
			</div>
		</div>
	{/if}
</div>


