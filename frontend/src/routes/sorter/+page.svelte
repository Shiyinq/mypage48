<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import SorterGenerationSelect from '$lib/components/sorter/SorterGenerationSelect.svelte';
	import { theaterSorter } from '$lib/stores/sorter.svelte';
	import { sorterNavbarStore } from '$lib/stores/sorterNavbar.svelte';

	const { t } = useTranslation();
	const sorter = theaterSorter;

	onMount(() => {
		sorter.fetchMembers();
		// If we land here (e.g. browser back) while sorter is active, reset it
		if (sorter.currentState !== 'landing') {
			sorter.restart();
		}
	});

	$effect(() => {
		if (sorter.currentState === 'sorting') {
			goto('/sorter/sorting');
		}
	});

	$effect(() => {
		sorterNavbarStore.update({
			pageType: 'sorter',
			layoutMode: 'card',
			sorterState: sorter.currentState as 'landing' | 'sorting' | 'results',
			numQuestion: sorter.numQuestion
		});
		return () => {
			sorterNavbarStore.reset();
		};
	});
</script>

<SEO title={t('theater.sorter.title')} path="/sorter" description={t('theater.sorter.subtitle')} />

<div
	class="w-full flex flex-col items-center justify-start min-h-[calc(100svh-64px)] pt-4 md:pt-8 pb-12"
>
	<SorterGenerationSelect {sorter} />
</div>
