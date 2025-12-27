<script lang="ts">
	import { goto } from '$app/navigation';
	import { showToast } from '$lib/stores';
	import { theme, setTheme } from '$lib/stores/theme';
	import type { Theme } from '$lib/stores/theme';
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
		Check,
		Sun,
		Moon,
		Monitor
	} from 'lucide-svelte';

	// i18n
	const { t, locale, changeLocale, availableLocales } = useTranslation();

	let generatingKey = false;
	let newApiKey: string | null = null;
	let showApiKeyModal = false;
	let showConfirmModal = false;

	// Theme options
	// Theme options
	const themeOptions: { value: Theme; icon: typeof Sun; bgClass: string; textClass: string }[] = [
		{
			value: 'light',
			icon: Sun,
			bgClass: 'bg-orange-100 dark:bg-orange-900/20',
			textClass: 'text-orange-600 dark:text-orange-400'
		},
		{
			value: 'dark',
			icon: Moon,
			bgClass: 'bg-indigo-100 dark:bg-indigo-900/20',
			textClass: 'text-indigo-600 dark:text-indigo-400'
		},
		{
			value: 'auto',
			icon: Monitor,
			bgClass: 'bg-gray-100 dark:bg-zinc-800',
			textClass: 'text-gray-600 dark:text-gray-400'
		}
	];

	const handleThemeChange = (newTheme: Theme) => {
		setTheme(newTheme);
		showToast($t('common.success'), 'success');
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

<svelte:head>
	<title>{$t('settings.title')} | MyPage48</title>
</svelte:head>

<div class="max-w-2xl mx-auto p-4 animate-fade-in pb-24">
	<!-- Page Header -->
	<div class="flex items-center justify-between mb-8">
		<div class="flex items-center gap-3">
			<button
				on:click={() => goto('/profile')}
				class="p-2 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-700 dark:hover:text-gray-200 transition-colors cursor-pointer"
				title={$t('common.back')}
			>
				<ArrowLeft class="w-5 h-5" />
			</button>
			<div>
				<h2 class="text-2xl font-black idol-text-gradient leading-none relative w-fit">
					{$t('settings.title')}
					<span
						class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 dark:bg-red-500/30 -z-10 transform -skew-x-12 rounded-sm"
					></span>
				</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{$t('settings.subtitle')}</p>
			</div>
		</div>
	</div>

	<!-- Settings Content -->
	<div class="space-y-6">
		<!-- THEME SETTINGS -->
		<div class="glass-panel p-6 rounded-3xl relative">
			<div class="flex items-center gap-3 mb-4">
				<div
					class="w-10 h-10 rounded-xl bg-pink-100 dark:bg-pink-900/20 flex items-center justify-center shadow-sm"
				>
					<Sun class="w-5 h-5 text-pink-600 dark:text-pink-400" />
				</div>
				<div>
					<h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">
						{$t('settings.theme.title')}
					</h3>
					<p class="text-xs text-gray-500 dark:text-gray-400">{$t('settings.theme.subtitle')}</p>
				</div>
			</div>

			<div class="grid grid-cols-3 gap-3">
				{#each themeOptions as option}
					<button
						on:click={() => handleThemeChange(option.value)}
						class="p-4 rounded-2xl border-2 transition-all flex flex-col items-center justify-center gap-2 cursor-pointer {$theme ===
						option.value
							? 'border-red-500 bg-red-50/50 dark:bg-red-900/20 shadow-sm'
							: 'border-gray-100 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:border-gray-200 dark:hover:border-zinc-600 hover:bg-gray-50 dark:hover:bg-zinc-800'}"
					>
						<div
							class="w-10 h-10 rounded-xl {option.bgClass} flex items-center justify-center shadow-sm"
						>
							<svelte:component this={option.icon} class="w-5 h-5 {option.textClass}" />
						</div>
						<div class="text-center">
							<p class="font-bold text-sm text-gray-800 dark:text-gray-200">
								{$t(`settings.theme.${option.value}`)}
							</p>
							<p class="text-[10px] text-gray-500 dark:text-gray-400 leading-tight mt-0.5">
								{$t(`settings.theme.${option.value}Description`)}
							</p>
						</div>
						{#if $theme === option.value}
							<div class="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
								<Check class="w-3 h-3 text-white" />
							</div>
						{:else}
							<div class="w-5 h-5 rounded-full border-2 border-gray-300 dark:border-gray-600"></div>
						{/if}
					</button>
				{/each}
			</div>
		</div>

		<!-- LANGUAGE SETTINGS -->
		<div class="glass-panel p-6 rounded-3xl relative">
			<div class="flex items-center gap-3 mb-4">
				<div
					class="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center shadow-sm"
				>
					<Globe class="w-5 h-5 text-blue-600 dark:text-blue-400" />
				</div>
				<div>
					<h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">
						{$t('settings.language.title')}
					</h3>
					<p class="text-xs text-gray-500 dark:text-gray-400">{$t('settings.language.subtitle')}</p>
				</div>
			</div>

			<div class="grid grid-cols-3 gap-3">
				{#each availableLocales as localeOption}
					<button
						on:click={() => handleLanguageChange(localeOption.code)}
						class="p-4 rounded-2xl border-2 transition-all flex flex-col items-center justify-center gap-3 cursor-pointer h-full {$locale ===
						localeOption.code
							? 'border-red-500 bg-red-50/50 dark:bg-red-900/20 shadow-sm'
							: 'border-gray-100 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:border-gray-200 dark:hover:border-zinc-600 hover:bg-gray-50 dark:hover:bg-zinc-800'}"
					>
						<span class="text-3xl drop-shadow-sm filter">{localeOption.flag}</span>
						<div class="text-center">
							<p class="font-bold text-sm text-gray-800 dark:text-gray-200 leading-tight">
								{localeOption.nativeName}
							</p>
							<p class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">{localeOption.name}</p>
						</div>
						<div
							class="w-5 h-5 rounded-full border-2 flex items-center justify-center {$locale ===
							localeOption.code
								? 'border-red-500 bg-red-500'
								: 'border-gray-300 dark:border-gray-600'}"
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
				<div
					class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-900/20 flex items-center justify-center shadow-sm"
				>
					<Key class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
				</div>
				<div>
					<h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">
						{$t('settings.developer.title')}
					</h3>
					<p class="text-xs text-gray-500 dark:text-gray-400">
						{$t('settings.developer.subtitle')}
					</p>
				</div>
			</div>

			<div
				class="bg-gray-50 dark:bg-gray-800/50 rounded-2xl p-4 border border-gray-100 dark:border-gray-700 mb-4"
			>
				<p class="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
					{$t('settings.developer.description')}
				</p>
				<div
					class="mt-3 flex items-start gap-2 bg-amber-50 dark:bg-amber-900/30 p-3 rounded-xl border border-amber-100 dark:border-amber-800"
				>
					<AlertTriangle class="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
					<p class="text-xs text-amber-700 dark:text-amber-300">
						{$t('settings.developer.warning')}
					</p>
				</div>
			</div>

			<button
				class="w-full py-3 rounded-xl bg-gray-900 dark:bg-zinc-800 text-white dark:text-gray-100 font-bold hover:bg-black dark:hover:bg-zinc-700 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-gray-300 dark:shadow-zinc-900/50"
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

<!-- API Key Modal -->
{#if showApiKeyModal}
	<div
		class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
	>
		<div
			class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-scale-in p-6"
		>
			<div class="text-center mb-6">
				<div
					class="w-14 h-14 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-green-200 dark:shadow-green-900/50"
				>
					<Key class="w-7 h-7 text-white" />
				</div>
				<h3 class="text-xl font-bold text-gray-900 dark:text-gray-100">
					{$t('settings.developer.generated')}
				</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-2">
					{$t('settings.developer.copyInfo')}
				</p>
			</div>

			<div
				class="bg-gray-50 dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700 mb-6 relative group"
			>
				<code class="text-sm font-mono text-gray-800 dark:text-gray-200 break-all pr-10"
					>{newApiKey}</code
				>
				<button
					class="absolute top-3 right-3 p-2 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:border-gray-300 dark:hover:border-gray-500 transition-all shadow-sm cursor-pointer"
					on:click={copyApiKey}
					title={$t('settings.developer.copied')}
				>
					<Copy class="w-4 h-4" />
				</button>
			</div>

			<button
				class="w-full py-3 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-xl font-bold hover:bg-black dark:hover:bg-white transition-colors cursor-pointer"
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
			class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl animate-scale-in p-6"
		>
			<div class="text-center mb-6">
				<div
					class="w-14 h-14 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-amber-200 dark:shadow-amber-900/50"
				>
					<AlertTriangle class="w-7 h-7 text-white" />
				</div>
				<h3 class="text-xl font-bold text-gray-900 dark:text-gray-100">
					{$t('settings.developer.confirmTitle')}
				</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-2">
					{$t('settings.developer.confirmDescription')}
				</p>
			</div>

			<div class="flex gap-3">
				<button
					class="flex-1 py-3 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 rounded-xl font-bold hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors cursor-pointer"
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
