<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { sorterNavbarStore } from '$lib/stores/sorterNavbar.svelte';
	import { PromoBanner } from '$lib/components/common';
	import { History } from 'lucide-svelte';

	const { t } = useTranslation();

	$effect(() => {
		sorterNavbarStore.update({
			pageType: 'history-list'
		});
		return () => {
			sorterNavbarStore.reset();
		};
	});
</script>

<SEO
	title={`${t('theater.sorter.history') || 'Riwayat Sorter'} - Oshi Sorter`}
	path="/jkt48/sorter/history"
	description={t('theater.sorter.subtitle')}
/>

<div class="w-full flex flex-col items-center justify-center min-h-[calc(100svh-64px)] p-4">
	<PromoBanner
		title={t('theater.sorter.historyFeatures')}
		desc={t('theater.sorter.landingPromo')}
		actionText={t('theater.sorter.loginNow')}
		class="max-w-xl w-full"
		hideCloseIcon={true}
		icon={History}
	/>
</div>
