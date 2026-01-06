<script lang="ts">
	export let params: Record<string, string> | undefined = undefined;
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { Calendar } from 'lucide-svelte';
	import { EmptyState } from '$lib/components';

	const { t } = useTranslation();
</script>

<SEO
	title={$t('theater.upcomingShows.title')}
	path="/theater/shows"
	description={$t('theater.upcomingShows.subtitle')}
/>

<EmptyState
	icon={Calendar}
	title={$t('theater.upcomingShows.title')}
	description={$t('theater.upcomingShows.empty')}
/>
