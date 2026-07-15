<script lang="ts">
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { apiKeys } from '$lib/apis/api_keys';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { authStore } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { Settings, MessageSquare, ArrowRight, LogOut, LoaderCircle } from 'lucide-svelte';

	// Components
	import SEO from '$lib/components/SEO.svelte';
	import { PageHeader } from '$lib/components';
	import {
		AccountSettings,
		PublicProfileSettings,
		ThemeSettings,
		LanguageSettings,
		DeveloperAccessSettings,
		ApiKeyModal,
		ConfirmApiKeyModal,
		ExportData
	} from '$lib/components/settings';
	import VersionDisplay from '$lib/components/common/VersionDisplay.svelte';

	const { t } = useTranslation();

	let generatingKey = $state(false);
	let newApiKey: string | null = $state(null);
	let showApiKeyModal = $state(false);
	let showConfirmModal = $state(false);

	let isLoggingOut = $derived(authStore.isLoggingOut);

	const logout = async () => {
		try {
			await authStore.logout();
			showToast(t('auth.logout.success'), 'success');
			goto('/login');
		} catch (e) {
			logger.error('Logout error', e, { context: 'SettingsPage' });
		}
	};

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
			showToast(t('settings.developer.generated'), 'success');
		} catch (e) {
			logger.error('Failed to generate API Key', e, { context: 'SettingsPage' });
			showToast(t('common.error'), 'error');
		} finally {
			generatingKey = false;
		}
	};

	const copyApiKey = () => {
		if (newApiKey) {
			navigator.clipboard.writeText(newApiKey);
			showToast(t('settings.developer.copied'), 'success');
		}
	};

	const closeApiKeyModal = () => {
		showApiKeyModal = false;
		newApiKey = null;
	};
</script>

<SEO title={t('settings.title')} path="/settings" description={t('seo.settings')} />

<div class="max-w-2xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 pb-32 space-y-4 sm:space-y-8">
	<!-- Header -->
	<div class="mb-0 sm:mb-8">
		<PageHeader
			title={t('settings.title')}
			subtitle={t('settings.subtitle')}
			icon={Settings}
			showBackButton={true}
			backUrl="/profile"
			theme="red"
		/>
	</div>

	<!-- Settings Content -->
	<div class="space-y-6">
		<!-- ACCOUNT SETTINGS -->
		<AccountSettings />

		<!-- PUBLIC PROFILE SETTINGS -->
		<PublicProfileSettings />

		<!-- THEME SETTINGS -->
		<ThemeSettings />

		<!-- LANGUAGE SETTINGS -->
		<LanguageSettings />

		<!-- EXPORT DATA -->
		<ExportData />

		<!-- DEVELOPER ACCESS -->
		<DeveloperAccessSettings {generatingKey} onopenConfirmModal={openConfirmModal} />

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
							{t('settings.feedback.title')}
						</h3>
						<p class="text-xs text-slate-500 dark:text-slate-400">
							{t('settings.feedback.subtitle')}
						</p>
					</div>
				</div>
				<ArrowRight
					class="w-5 h-5 text-slate-300 dark:text-slate-600 group-hover:text-red-500 group-hover:translate-x-1 transition-all"
				/>
			</div>
		</a>

		<!-- DIVIDER -->
		<div class="py-4">
			<div class="h-px w-full bg-slate-200 dark:bg-zinc-800"></div>
		</div>

		<!-- LOGOUT SECTION -->
		<div class="glass-panel p-6 rounded-3xl block border border-red-100 dark:border-red-900/30">
			<div
				class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 sm:gap-0"
			>
				<div class="flex items-center gap-3">
					<div
						class="p-2.5 rounded-xl bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 shrink-0"
					>
						<LogOut class="w-5 h-5" />
					</div>
					<div>
						<h3 class="text-lg font-bold text-red-600 dark:text-red-400 leading-tight">
							{t('settings.logout.title')}
						</h3>
						<p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
							{t('settings.logout.description')}
						</p>
					</div>
				</div>
				<button
					onclick={logout}
					disabled={isLoggingOut}
					class="w-full sm:w-auto px-4 py-2.5 sm:py-2 rounded-xl bg-red-500 hover:bg-red-600 text-white font-bold text-sm transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
				>
					{#if isLoggingOut}
						<LoaderCircle class="w-4 h-4 animate-spin" />
					{/if}
					{t('common.logout')}
				</button>
			</div>
		</div>

		<div class="pt-4 pb-8 text-center">
			<VersionDisplay />
		</div>
	</div>
</div>

<!-- API Key Modals -->
<ApiKeyModal
	show={showApiKeyModal}
	apiKey={newApiKey}
	onclose={closeApiKeyModal}
	oncopy={copyApiKey}
/>

<ConfirmApiKeyModal
	show={showConfirmModal}
	oncancel={closeConfirmModal}
	onconfirm={confirmGenerateApiKey}
/>
