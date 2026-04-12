<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Key, Plus, LoaderCircle, TriangleAlert, Terminal, ChevronRight } from 'lucide-svelte';

	const { t } = useTranslation();
	const dispatch = createEventDispatcher<{ openConfirmModal: void }>();

	interface Props {
		generatingKey?: boolean;
	}

	let { generatingKey = false }: Props = $props();

	const handleGenerateClick = () => {
		dispatch('openConfirmModal');
	};
</script>

<div class="glass-panel p-6 rounded-3xl relative">
	<div class="flex items-center gap-3 mb-4">
		<div
			class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-900/20 flex items-center justify-center shadow-sm"
		>
			<Key class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
		</div>
		<div>
			<h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">
				{$t('settings.developer.title')}
			</h3>
			<p class="text-xs text-gray-500 dark:text-gray-400">
				{$t('settings.developer.subtitle')}
			</p>
		</div>
	</div>

	<div
		class="bg-gray-50 dark:bg-gray-800/50 rounded-2xl p-4 border border-gray-100 dark:border-gray-700 mb-4"
	>
		<p class="text-sm text-gray-600 dark:text-gray-300 leading-relaxed pl-1">
			{$t('settings.developer.description')}
		</p>
		<div
			class="mt-4 flex items-start gap-3 bg-amber-50 dark:bg-amber-900/10 p-4 rounded-xl border border-amber-100 dark:border-amber-800/30"
		>
			<TriangleAlert class="w-4 h-4 text-amber-600 dark:text-amber-500 flex-shrink-0 mt-0.5" />
			<p class="text-xs text-amber-700 dark:text-amber-400 font-medium leading-tight">
				{$t('settings.developer.warning')}
			</p>
		</div>
	</div>

	<button
		class="w-full py-3.5 rounded-xl bg-gray-900 dark:bg-zinc-800 text-white dark:text-gray-100 font-black uppercase text-xs tracking-widest hover:bg-black dark:hover:bg-zinc-700 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-gray-300 dark:shadow-zinc-900/50 mb-6"
		onclick={handleGenerateClick}
		disabled={generatingKey}
	>
		{#if generatingKey}
			<LoaderCircle class="w-4 h-4 animate-spin" />
			{$t('settings.developer.generating')}
		{:else}
			<Plus class="w-4 h-4" />
			{$t('settings.developer.generateButton')}
		{/if}
	</button>

	<a href="/playground" class="block w-full group">
		<div
			class="p-4 rounded-2xl bg-gradient-to-br from-red-500/5 to-orange-500/5 border border-red-100/50 dark:border-red-900/20 hover:border-red-200 dark:hover:border-red-800/40 transition-all flex items-center justify-between group-hover:shadow-md"
		>
			<div class="flex items-center gap-3">
				<div
					class="w-8 h-8 rounded-lg bg-red-500 text-white flex items-center justify-center shadow-lg shadow-red-500/20"
				>
					<Terminal class="w-4 h-4" />
				</div>
				<div>
					<p class="text-sm font-bold text-gray-900 dark:text-gray-100">{$t('playground.title')}</p>
					<p class="text-[10px] text-gray-500 dark:text-gray-400">{$t('playground.subtitle')}</p>
				</div>
			</div>
			<ChevronRight
				class="w-4 h-4 text-gray-400 group-hover:text-red-500 group-hover:translate-x-1 transition-all"
			/>
		</div>
	</a>
</div>
