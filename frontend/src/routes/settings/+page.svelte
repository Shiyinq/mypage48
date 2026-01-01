<script lang="ts">
	import { showToast } from '$lib/stores';
	import { apiKeys } from '$lib/apis/api_keys';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Settings } from 'lucide-svelte';

	// Components
	import SEO from '$lib/components/SEO.svelte';
	import { PageHeader } from '$lib/components';
	import {
		PublicProfileSettings,
		ThemeSettings,
		LanguageSettings,
		DeveloperAccessSettings,
		ApiKeyModal,
		ConfirmApiKeyModal
	} from '$lib/components/settings';

	const { t } = useTranslation();

	let generatingKey = false;
	let newApiKey: string | null = null;
	let showApiKeyModal = false;
	let showConfirmModal = false;

	const openConfirmModal = () => {
		showConfirmModal = true;
	};

	const closeConfirmModal = () => {
		showConfirmModal = false;
	};

	const confirmGenerateApiKey = async () => {
		showConfirmModal = false;
		generatingKey = true;
		try {
			const res = await apiKeys.create();
			newApiKey = res.apiKey;
			showApiKeyModal = true;
			showToast($t('settings.developer.generated'), 'success');
		} catch (e) {
			console.error('Failed to generate API Key', e);
			showToast($t('common.error'), 'error');
		} finally {
			generatingKey = false;
		}
	};

	const copyApiKey = () => {
		if (newApiKey) {
			navigator.clipboard.writeText(newApiKey);
			showToast($t('settings.developer.copied'), 'success');
		}
	};

	const closeApiKeyModal = () => {
		showApiKeyModal = false;
		newApiKey = null;
	};
</script>

<SEO title={$t('settings.title')} path="/settings" description={$t('seo.settings')} />

<div class="max-w-2xl mx-auto p-4 animate-fade-in pb-24">
	<!-- Page Header -->
	<div class="mb-6">
		<PageHeader
			title={$t('settings.title')}
			subtitle={$t('settings.subtitle')}
			showBackButton={true}
			backUrl="/profile"
			theme="red"
		/>
	</div>

	<!-- Settings Content -->
	<div class="space-y-6">
		<!-- PUBLIC PROFILE SETTINGS -->
		<PublicProfileSettings />

		<!-- THEME SETTINGS -->
		<ThemeSettings />

		<!-- LANGUAGE SETTINGS -->
		<LanguageSettings />

		<!-- DEVELOPER ACCESS -->
		<DeveloperAccessSettings {generatingKey} on:openConfirmModal={openConfirmModal} />

		<!-- More Settings Coming Soon -->
		<div class="glass-panel p-6 rounded-3xl opacity-60">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3">
					<div class="p-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 text-gray-400">
						<Settings class="w-5 h-5" />
					</div>
					<div>
						<h3 class="text-lg font-bold text-gray-400">{$t('settings.moreSettings.title')}</h3>
						<p class="text-xs text-gray-400">{$t('settings.moreSettings.subtitle')}</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>

<!-- API Key Modals -->
<ApiKeyModal
	show={showApiKeyModal}
	apiKey={newApiKey}
	on:close={closeApiKeyModal}
	on:copy={copyApiKey}
/>

<ConfirmApiKeyModal
	show={showConfirmModal}
	on:cancel={closeConfirmModal}
	on:confirm={confirmGenerateApiKey}
/>
