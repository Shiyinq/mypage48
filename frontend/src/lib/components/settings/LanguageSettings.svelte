<script lang="ts">
	import { showToast } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { Locale } from '$lib/i18n/useTranslation';
	import { Globe, Check } from 'lucide-svelte';

	const { t, locale, changeLocale, availableLocales } = useTranslation();

	const handleLanguageChange = (newLocale: Locale) => {
		changeLocale(newLocale);
		showToast($t('common.success'), 'success');
	};
</script>

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

	<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
		{#each availableLocales as localeOption}
			<button
				on:click={() => handleLanguageChange(localeOption.code)}
				class="p-4 rounded-2xl border-2 transition-all flex md:flex-col items-center justify-between md:justify-center gap-4 cursor-pointer h-full {$locale ===
				localeOption.code
					? 'border-red-500 bg-red-50/50 dark:bg-red-900/20 shadow-sm'
					: 'border-gray-100 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:border-gray-200 dark:hover:border-zinc-600 hover:bg-gray-50 dark:hover:bg-zinc-800'}"
			>
				<div class="flex items-center md:flex-col gap-4 md:gap-3">
					<span class="text-3xl drop-shadow-sm filter flex-shrink-0">{localeOption.flag}</span>
					<div class="text-left md:text-center">
						<p
							class="font-bold text-base md:text-sm text-gray-800 dark:text-gray-200 leading-tight"
						>
							{localeOption.nativeName}
						</p>
						<p class="text-xs md:text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
							{localeOption.name}
						</p>
					</div>
				</div>

				<div class="flex-shrink-0 pl-2">
					<div
						class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors shadow-sm {$locale ===
						localeOption.code
							? 'border-red-500 bg-red-500'
							: 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-zinc-800'}"
					>
						{#if $locale === localeOption.code}
							<Check class="w-3.5 h-3.5 text-white" />
						{/if}
					</div>
				</div>
			</button>
		{/each}
	</div>
</div>
