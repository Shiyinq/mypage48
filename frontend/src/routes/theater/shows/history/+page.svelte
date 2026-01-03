<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { History, Sparkles } from 'lucide-svelte';

	const { t } = useTranslation();
</script>

<SEO
	title={$t('theater.showHistory.title')}
	path="/theater/shows/history"
	description={$t('theater.showHistory.subtitle')}
/>

<div class="flex flex-col items-center justify-center py-16 text-center">
	<div
		class="p-6 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 dark:from-amber-900/30 dark:to-orange-900/30 mb-6"
	>
		<History class="w-12 h-12 text-amber-600 dark:text-amber-400" />
	</div>

	<h3 class="text-xl font-bold text-themed mb-2 flex items-center gap-2">
		{$t('theater.showHistory.title')}
		<Sparkles class="w-5 h-5 text-yellow-500" />
	</h3>
	<p class="text-themed-secondary text-sm max-w-md mb-4">{$t('theater.showHistory.subtitle')}</p>

	<div
		class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-2xl px-6 py-4 max-w-sm"
	>
		<p class="text-amber-600 dark:text-amber-400 font-semibold">
			{$t('theater.showHistory.comingSoon')}
		</p>
	</div>
</div>
