<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Key, Plus, LoaderCircle, TriangleAlert } from 'lucide-svelte';

	const { t } = useTranslation();
	const dispatch = createEventDispatcher<{ openConfirmModal: void }>();

	export let generatingKey = false;

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
		<p class="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
			{$t('settings.developer.description')}
		</p>
		<div
			class="mt-3 flex items-start gap-2 bg-amber-50 dark:bg-amber-900/30 p-3 rounded-xl border border-amber-100 dark:border-amber-800"
		>
			<TriangleAlert class="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
			<p class="text-xs text-amber-700 dark:text-amber-300">
				{$t('settings.developer.warning')}
			</p>
		</div>
	</div>

	<button
		class="w-full py-3 rounded-xl bg-gray-900 dark:bg-zinc-800 text-white dark:text-gray-100 font-bold hover:bg-black dark:hover:bg-zinc-700 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-gray-300 dark:shadow-zinc-900/50"
		on:click={handleGenerateClick}
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
</div>
