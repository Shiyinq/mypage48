<script module lang="ts">
	export type FilterType = 'ALL' | 'TICKET' | '2SHOT';
</script>

<script lang="ts">
	import { Grid, Ticket as TicketIcon, Camera } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		filter?: FilterType;
		onchange?: (newFilter: FilterType) => void;
	}

	let { filter = $bindable('ALL'), onchange }: Props = $props();

	const { t } = useTranslation();

	function setFilter(newFilter: FilterType) {
		filter = newFilter;
		onchange?.(newFilter);
	}
</script>

<div
	class="bg-white dark:bg-zinc-900 p-1.5 rounded-xl border border-gray-200 dark:border-zinc-700 shadow-sm flex items-center gap-1 overflow-x-auto no-scrollbar max-w-[calc(100vw-3rem)] sm:max-w-none"
>
	<button
		onclick={() => setFilter('ALL')}
		class={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all whitespace-nowrap cursor-pointer ${filter === 'ALL' ? 'bg-pink-500 text-white shadow-md shadow-pink-200 dark:shadow-pink-900/30' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-zinc-800'}`}
	>
		<Grid class="w-3.5 h-3.5" />
		{t('memories.allPhotos')}
	</button>
	<button
		onclick={() => setFilter('TICKET')}
		class={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all whitespace-nowrap cursor-pointer ${filter === 'TICKET' ? 'bg-red-500 text-white shadow-md shadow-red-200 dark:shadow-red-900/30' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-zinc-800'}`}
	>
		<TicketIcon class="w-3.5 h-3.5" />
		{t('memories.tickets')}
	</button>
	<button
		onclick={() => setFilter('2SHOT')}
		class={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all whitespace-nowrap cursor-pointer ${filter === '2SHOT' ? 'bg-purple-500 text-white shadow-md shadow-purple-200 dark:shadow-purple-900/30' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-zinc-800'}`}
	>
		<Camera class="w-3.5 h-3.5" />
		{t('memories.twoShots')}
	</button>
</div>
