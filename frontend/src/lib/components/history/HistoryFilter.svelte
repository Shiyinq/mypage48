<script lang="ts">
	import { LayoutGrid, List, Search } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let searchQuery = '';
	export let viewMode: 'GRID' | 'TABLE' = 'GRID';

	const { t } = useTranslation();
</script>

<div class="flex items-center gap-3">
	<!-- Search Bar -->
	<div class="relative w-full md:w-64 group">
		<Search
			class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-blue-500 transition-colors"
		/>
		<input
			type="text"
			placeholder={$t('common.search')}
			bind:value={searchQuery}
			class="w-full pl-10 pr-4 py-2 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-full text-sm font-medium text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm transition-all"
		/>
	</div>

	<!-- View Toggle -->
	<div
		class="flex bg-white dark:bg-zinc-900 p-1 rounded-full border border-gray-200 dark:border-zinc-700 shadow-sm"
	>
		<button
			on:click={() => (viewMode = 'GRID')}
			class={`p-2 rounded-full transition-all cursor-pointer ${viewMode === 'GRID' ? 'bg-blue-50 dark:bg-blue-500/20 text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
			title="Grid View"
		>
			<LayoutGrid class="w-4 h-4" />
		</button>
		<button
			on:click={() => (viewMode = 'TABLE')}
			class={`p-2 rounded-full transition-all cursor-pointer ${viewMode === 'TABLE' ? 'bg-blue-50 dark:bg-blue-500/20 text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
			title="Table View"
		>
			<List class="w-4 h-4" />
		</button>
	</div>
</div>
