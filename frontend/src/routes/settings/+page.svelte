<script lang="ts">
	import { goto } from '$app/navigation';
	import { showToast } from '$lib/stores';
	import { apiKeys } from '$lib/apis/api_keys';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { Locale } from '$lib/i18n/useTranslation';
	import {
		Settings,
		ArrowLeft,
		Key,
		Plus,
		Loader2,
		Copy,
		AlertTriangle,
		Globe,
		Check
	} from 'lucide-svelte';

	// i18n
	const { t, locale, changeLocale, availableLocales } = useTranslation();

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
			newApiKey = res.api_key;
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

	const handleLanguageChange = (newLocale: Locale) => {
		changeLocale(newLocale);
		showToast($t('common.success'), 'success');
	};
</script>

<div class="max-w-2xl mx-auto p-4 animate-fade-in pb-24">
	<!-- Page Header -->
	<div class="flex items-center justify-between mb-8">
		<div class="flex items-center gap-3">
			<button
				on:click={() => goto('/profile')}
				class="p-2 rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700 transition-colors cursor-pointer"
				title={$t('common.back')}
			>
				<ArrowLeft class="w-5 h-5" />
			</button>
			<div>
				<h2 class="text-2xl font-black idol-text-gradient leading-none relative w-fit">
					{$t('settings.title')}
					<span
						class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 -z-10 transform -skew-x-12 rounded-sm"
					></span>
				</h2>
				<p class="text-sm text-gray-500 mt-1">{$t('settings.subtitle')}</p>
			</div>
		</div>
	</div>

	<!-- Settings Content -->
	<div class="space-y-6">
		<!-- LANGUAGE SETTINGS -->
		<div class="glass-panel p-6 rounded-3xl relative">
			<div class="flex items-center gap-3 mb-4">
				<div
					class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg"
				>
					<Globe class="w-5 h-5 text-white" />
				</div>
				<div>
					<h3 class="text-lg font-bold text-gray-900">{$t('settings.language.title')}</h3>
					<p class="text-xs text-gray-500">{$t('settings.language.subtitle')}</p>
				</div>
			</div>

			<div class="space-y-3">
				{#each availableLocales as localeOption}
					<button
						on:click={() => handleLanguageChange(localeOption.code)}
						class="w-full p-4 rounded-2xl border-2 transition-all flex items-center justify-between cursor-pointer {$locale ===
						localeOption.code
							? 'border-red-500 bg-red-50/50 shadow-sm'
							: 'border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50'}"
					>
						<div class="flex items-center gap-3">
							<span class="text-2xl">{localeOption.flag}</span>
							<div class="text-left">
								<p class="font-bold text-gray-800">{localeOption.nativeName}</p>
								<p class="text-xs text-gray-500">{localeOption.name}</p>
							</div>
						</div>
						<div
							class="w-5 h-5 rounded-full border-2 flex items-center justify-center {$locale ===
							localeOption.code
								? 'border-red-500 bg-red-500'
								: 'border-gray-300'}"
						>
							{#if $locale === localeOption.code}
								<Check class="w-3 h-3 text-white" />
							{/if}
						</div>
					</button>
				{/each}
			</div>
		</div>

		<!-- DEVELOPER ACCESS -->
		<div class="glass-panel p-6 rounded-3xl relative">
			<div class="flex items-center gap-3 mb-4">
				<div class="w-10 h-10 rounded-xl bg-gray-900 flex items-center justify-center shadow-lg">
					<Key class="w-5 h-5 text-white" />
				</div>
				<div>
					<h3 class="text-lg font-bold text-gray-900">{$t('settings.developer.title')}</h3>
					<p class="text-xs text-gray-500">{$t('settings.developer.subtitle')}</p>
				</div>
			</div>

			<div class="bg-gray-50 rounded-2xl p-4 border border-gray-100 mb-4">
				<p class="text-sm text-gray-600 leading-relaxed">
					{$t('settings.developer.description')}
				</p>
				<div class="mt-3 flex items-start gap-2 bg-amber-50 p-3 rounded-xl border border-amber-100">
					<AlertTriangle class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
					<p class="text-xs text-amber-700">
						{$t('settings.developer.warning')}
					</p>
				</div>
			</div>

			<button
				class="w-full py-3 rounded-xl bg-gray-900 text-white font-bold hover:bg-black transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-gray-300"
				on:click={openConfirmModal}
				disabled={generatingKey}
			>
				{#if generatingKey}
					<Loader2 class="w-4 h-4 animate-spin" />
					{$t('settings.developer.generating')}
				{:else}
					<Plus class="w-4 h-4" />
					{$t('settings.developer.generateButton')}
				{/if}
			</button>
		</div>

		<!-- More Settings Coming Soon -->
		<div class="glass-panel p-6 rounded-3xl opacity-60">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3">
					<div class="p-2.5 rounded-xl bg-gray-100 text-gray-400">
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

<!-- API Key Modal -->
{#if showApiKeyModal}
	<div
		class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
	>
		<div
			class="bg-white rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-scale-in p-6"
		>
			<div class="text-center mb-6">
				<div
					class="w-14 h-14 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-green-200"
				>
					<Key class="w-7 h-7 text-white" />
				</div>
				<h3 class="text-xl font-bold text-gray-900">{$t('settings.developer.generated')}</h3>
				<p class="text-sm text-gray-500 mt-2">
					{$t('settings.developer.copyInfo')}
				</p>
			</div>

			<div class="bg-gray-50 p-4 rounded-xl border border-gray-200 mb-6 relative group">
				<code class="text-sm font-mono text-gray-800 break-all pr-10">{newApiKey}</code>
				<button
					class="absolute top-3 right-3 p-2 bg-white rounded-lg border border-gray-200 text-gray-500 hover:text-gray-900 hover:border-gray-300 transition-all shadow-sm cursor-pointer"
					on:click={copyApiKey}
					title={$t('settings.developer.copied')}
				>
					<Copy class="w-4 h-4" />
				</button>
			</div>

			<button
				class="w-full py-3 bg-gray-900 text-white rounded-xl font-bold hover:bg-black transition-colors cursor-pointer"
				on:click={closeApiKeyModal}
			>
				{$t('settings.developer.savedKey')}
			</button>
		</div>
	</div>
{/if}

<!-- Confirm Generate API Key Modal -->
{#if showConfirmModal}
	<div
		class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
	>
		<div
			class="bg-white rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl animate-scale-in p-6"
		>
			<div class="text-center mb-6">
				<div
					class="w-14 h-14 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-amber-200"
				>
					<AlertTriangle class="w-7 h-7 text-white" />
				</div>
				<h3 class="text-xl font-bold text-gray-900">{$t('settings.developer.confirmTitle')}</h3>
				<p class="text-sm text-gray-500 mt-2">
					{$t('settings.developer.confirmDescription')}
				</p>
			</div>

			<div class="flex gap-3">
				<button
					class="flex-1 py-3 bg-gray-100 text-gray-700 rounded-xl font-bold hover:bg-gray-200 transition-colors cursor-pointer"
					on:click={closeConfirmModal}
				>
					{$t('common.cancel')}
				</button>
				<button
					class="flex-1 py-3 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 transition-colors cursor-pointer"
					on:click={confirmGenerateApiKey}
				>
					{$t('common.confirm')}
				</button>
			</div>
		</div>
	</div>
{/if}
