<script lang="ts">
	export let params: Record<string, string> | undefined = undefined;
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { apiKeys } from '$lib/apis/api_keys';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Settings, MessageSquare, ArrowRight } from 'lucide-svelte';

	// Components
	import SEO from '$lib/components/SEO.svelte';
	import { PageHeader } from '$lib/components';
	import {
		PublicProfileSettings,
		ThemeSettings,
		LanguageSettings,
		DeveloperAccessSettings,
		ApiKeyModal,
		ConfirmApiKeyModal,
		ExportData
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
			logger.error('Failed to generate API Key', e, { context: 'SettingsPage' });
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

		<!-- EXPORT DATA -->
		<ExportData />

		<!-- DEVELOPER ACCESS -->
		<DeveloperAccessSettings {generatingKey} on:openConfirmModal={openConfirmModal} />

		<!-- More Settings Coming Soon -->
		<a
			href="/feedback"
			class="glass-panel p-6 rounded-3xl block hover:bg-slate-50 dark:hover:bg-zinc-800/50 transition-colors cursor-pointer group"
		>
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3">
					<div
						class="p-2.5 rounded-xl bg-orange-100 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400 group-hover:scale-110 transition-transform"
					>
						<MessageSquare class="w-5 h-5" />
					</div>
					<div>
						<h3 class="text-lg font-bold text-slate-900 dark:text-white">
							{$t('settings.feedback.title')}
						</h3>
						<p class="text-xs text-slate-500 dark:text-slate-400">
							{$t('settings.feedback.subtitle')}
						</p>
					</div>
				</div>
				<ArrowRight
					class="w-5 h-5 text-slate-300 dark:text-slate-600 group-hover:text-red-500 group-hover:translate-x-1 transition-all"
				/>
			</div>
		</a>
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
