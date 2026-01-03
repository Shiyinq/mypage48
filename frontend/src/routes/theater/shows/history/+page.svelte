<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { History, Sparkles } from 'lucide-svelte';
	import { EmptyState } from '$lib/components';

	const { t } = useTranslation();
</script>

<SEO
	title={$t('theater.showHistory.title')}
	path="/theater/shows/history"
	description={$t('theater.showHistory.subtitle')}
/>

<EmptyState
	icon={History}
	title={$t('theater.showHistory.title')}
	description={$t('theater.showHistory.empty')}
/>
