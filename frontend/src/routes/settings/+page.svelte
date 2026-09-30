<script lang="ts">
	import { Settings } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { PageHeader } from '$lib/components';
	import { SettingsSections } from '$lib/components/settings';

	const { t } = useTranslation();
</script>

<SEO title={t('settings.title')} path="/settings" description={t('seo.settings')} />

<div class="max-w-2xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 pb-32 space-y-4 sm:space-y-8">
	<!-- Header -->
	<div class="mb-0 sm:mb-8">
		<PageHeader
			title={t('settings.title')}
			subtitle={t('settings.subtitle')}
			icon={Settings}
			showBackButton={false}
			theme="red"
		/>
	</div>

	<!-- Settings Content -->
	<SettingsSections />
</div>
