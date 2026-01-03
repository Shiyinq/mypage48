<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { Calendar, Sparkles } from 'lucide-svelte';

	const { t } = useTranslation();
</script>

<SEO
	title={$t('theater.upcomingShows.title')}
	path="/theater/shows"
	description={$t('theater.upcomingShows.subtitle')}
/>

<div class="flex flex-col items-center justify-center py-16 text-center">
	<div
		class="p-6 rounded-full bg-gradient-to-br from-blue-100 to-cyan-100 dark:from-blue-900/30 dark:to-cyan-900/30 mb-6"
	>
		<Calendar class="w-12 h-12 text-blue-600 dark:text-blue-400" />
	</div>

	<h3 class="text-xl font-bold text-themed mb-2 flex items-center gap-2">
		{$t('theater.upcomingShows.title')}
		<Sparkles class="w-5 h-5 text-yellow-500" />
	</h3>
	<p class="text-themed-secondary text-sm max-w-md mb-4">{$t('theater.upcomingShows.subtitle')}</p>

	<div
		class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-2xl px-6 py-4 max-w-sm"
	>
		<p class="text-blue-600 dark:text-blue-400 font-semibold">
			{$t('theater.upcomingShows.comingSoon')}
		</p>
	</div>
</div>
