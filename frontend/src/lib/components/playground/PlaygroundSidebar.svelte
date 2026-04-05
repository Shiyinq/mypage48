<script lang="ts">
	import { Search, ChevronRight, Hash, Eye, EyeOff, X, Lock } from 'lucide-svelte';
	import { playgroundStore } from '$lib/stores/playground';
	import { createEventDispatcher } from 'svelte';
	import { slide } from 'svelte/transition';
	import type { OpenAPIEndpoint } from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	export let groupedEndpoints: Record<string, OpenAPIEndpoint[]> = {};
	export let selectedId: string | null = null;

	const dispatch = createEventDispatcher<{ select: OpenAPIEndpoint }>();

	let searchQuery = '';
	let expandedTags: Record<string, boolean> = {};
	let showApiKey = false;
	let isConfigExpanded = !$playgroundStore.apiKey;

	$: filteredGroups = Object.entries(groupedEndpoints).reduce((acc: Record<string, OpenAPIEndpoint[]>, [tag, endpoints]) => {
		const filtered = endpoints.filter((e) => 
			e.path.toLowerCase().includes(searchQuery.toLowerCase()) || 
			e.details.summary?.toLowerCase().includes(searchQuery.toLowerCase()) ||
			tag.toLowerCase().includes(searchQuery.toLowerCase())
		);
		if (filtered.length > 0) acc[tag] = filtered;
		return acc;
	}, {});

	function toggleTag(tag: string) {
		expandedTags[tag] = !expandedTags[tag];
	}

	function handleSelect(endpoint: OpenAPIEndpoint) {
		dispatch('select', endpoint);
	}

	const methodColors: Record<string, string> = {
		get: 'text-blue-500 bg-blue-500/10',
		post: 'text-emerald-500 bg-emerald-500/10',
		put: 'text-amber-500 bg-amber-500/10',
		delete: 'text-rose-500 bg-rose-500/10',
		patch: 'text-purple-500 bg-purple-500/10'
	};
</script>

<div class="flex flex-col h-full bg-white dark:bg-zinc-900 border-r border-gray-100 dark:border-white/5 w-80 shrink-0">
	<!-- Global Configuration -->
	<div class="border-b border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-zinc-800/30">
		<button 
			on:click={() => isConfigExpanded = !isConfigExpanded}
			class="w-full p-4 flex items-center justify-between group cursor-pointer"
		>
			<div class="flex items-center gap-2">
				<Lock class="w-3.5 h-3.5 { $playgroundStore.apiKey ? 'text-emerald-500' : 'text-red-500' }" />
				<span class="text-[10px] font-black uppercase tracking-wider text-gray-500 dark:text-gray-400">
					{$t('playground.configTitle')}
				</span>
				{#if $playgroundStore.apiKey && !isConfigExpanded}
					<span class="text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
						(Active)
					</span>
				{/if}
			</div>
			<ChevronRight 
				class="w-3.5 h-3.5 text-gray-400 transition-transform duration-200" 
				style="transform: rotate({isConfigExpanded ? '90deg' : '0deg'})"
			/>
		</button>
		
		{#if isConfigExpanded}
			<div transition:slide={{ duration: 200 }} class="px-4 pb-4 space-y-1.5 border-t border-gray-100 dark:border-white/5 pt-3">
				<label for="global-api-key" class="text-[10px] font-bold text-gray-400 dark:text-gray-500 ml-1">
					{$t('playground.apiKeyLabel')}
				</label>
				<div class="relative group">
					<input
						id="global-api-key"
						type={showApiKey ? 'text' : 'password'}
						placeholder={$t('playground.apiKeyPlaceholder')}
						value={$playgroundStore.apiKey || ''}
						on:input={(e) => {
							playgroundStore.setApiKey(e.currentTarget.value);
							// Optional: Auto-hide if they finished typing? 
							// Better to let them collapse manually or after focus lost if it's valid.
						}}
						class="w-full pl-3 pr-16 py-2 bg-white dark:bg-zinc-800 border border-gray-200 dark:border-white/5 rounded-xl text-xs focus:ring-1 focus:ring-red-500 transition-all font-mono"
					/>
					<div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
						{#if $playgroundStore.apiKey}
							<button 
								on:click={() => playgroundStore.setApiKey(null)}
								class="p-1 hover:bg-gray-100 dark:hover:bg-white/10 rounded-md transition-colors text-gray-400 hover:text-red-500"
							>
								<X class="w-3.5 h-3.5" />
							</button>
						{/if}
						<button 
							on:click={() => showApiKey = !showApiKey}
							class="p-1 hover:bg-gray-100 dark:hover:bg-white/10 rounded-md transition-colors text-gray-400"
						>
							{#if showApiKey}
								<EyeOff class="w-3.5 h-3.5" />
							{:else}
								<Eye class="w-3.5 h-3.5" />
							{/if}
						</button>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="p-4 border-b border-gray-100 dark:border-white/5">
		<div class="relative">
			<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
			<input
				type="text"
				placeholder={$t('playground.searchPlaceholder')}
				bind:value={searchQuery}
				class="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-zinc-800 border-none rounded-xl text-sm focus:ring-1 focus:ring-red-500 transition-all"
			/>
		</div>
	</div>

	<div class="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
		{#each Object.entries(filteredGroups) as [tag, endpoints]}
			<div class="mb-2">
				<button
					on:click={() => toggleTag(tag)}
					class="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 transition-colors group cursor-pointer"
				>

					<div class="flex items-center gap-2">
						<Hash class="w-4 h-4 text-gray-400 group-hover:text-red-500 transition-colors" />
						<span class="text-sm font-bold text-gray-700 dark:text-gray-200">{tag}</span>
					</div>
					<ChevronRight 
						class="w-4 h-4 text-gray-400 transition-transform duration-200" 
						style="transform: rotate({expandedTags[tag] ? '90deg' : '0deg'})"
					/>
				</button>

				{#if expandedTags[tag] || searchQuery}
					<div transition:slide={{ duration: 200 }} class="mt-1 space-y-0.5 ml-2">
						{#each endpoints as endpoint}
							<button
								on:click={() => handleSelect(endpoint)}
								class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-all cursor-pointer {selectedId === endpoint.id ? 'bg-red-500/10 text-red-600' : 'hover:bg-gray-50 dark:hover:bg-white/5'}"
							>

								<span class="text-[10px] font-black uppercase px-1.5 py-0.5 rounded {methodColors[endpoint.method.toLowerCase()] || 'bg-gray-100' }">
									{endpoint.method}
								</span>
								<div class="flex-1 min-w-0">
									<p class="text-xs font-bold truncate dark:text-gray-300">
										{endpoint.details.summary || endpoint.path}
									</p>
									<p class="text-[10px] text-gray-400 truncate font-mono">
										{endpoint.path}
									</p>
								</div>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</div>
</div>

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(0, 0, 0, 0.1);
		border-radius: 10px;
	}
	:global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.1);
	}
</style>
