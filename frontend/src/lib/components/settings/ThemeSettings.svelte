<script lang="ts">
	import { showToast } from '$lib/stores';
	import { theme, setTheme } from '$lib/stores/theme';
	import type { Theme } from '$lib/stores/theme';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Sun, Moon, Monitor, Check } from 'lucide-svelte';

	const { t } = useTranslation();

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
</script>

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
