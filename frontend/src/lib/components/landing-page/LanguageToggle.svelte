<script lang="ts">
	import { useTranslation, type Locale } from '$lib/i18n/useTranslation';
	import { fade, scale } from 'svelte/transition';
	import { Globe, Check } from 'lucide-svelte';

	const { locale, changeLocale } = useTranslation();

	let isOpen = false;

	const locales: { code: Locale; label: string; flag: string }[] = [
		{ code: 'id', label: 'Indonesia', flag: '🇮🇩' },
		{ code: 'en', label: 'English', flag: '🇺🇸' },
		{ code: 'ja', label: '日本語', flag: '🇯🇵' }
	];

	function toggleDropdown() {
		isOpen = !isOpen;
	}

	function selectLanguage(newLocale: Locale) {
		changeLocale(newLocale);
		isOpen = false;
	}

	function clickOutside(node: HTMLElement) {
		const handleClick = (event: MouseEvent) => {
			if (!node.contains(event.target as Node)) {
				isOpen = false;
			}
		};

		document.addEventListener('click', handleClick, true);

		return {
			destroy() {
				document.removeEventListener('click', handleClick, true);
			}
		};
	}
</script>

<div class="relative" use:clickOutside>
	<button
		on:click={toggleDropdown}
		class="w-10 h-10 rounded-full flex items-center justify-center bg-white/50 dark:bg-zinc-800/50 backdrop-blur-md border border-gray-200/50 dark:border-zinc-700/50 shadow-sm hover:bg-white dark:hover:bg-zinc-700 hover:scale-105 transition-all active:scale-95 group cursor-pointer text-slate-600 dark:text-slate-300"
		aria-label="Change language"
	>
		<Globe size={20} />
	</button>

	{#if isOpen}
		<div
			in:scale={{ duration: 150, start: 0.95 }}
			out:fade={{ duration: 100 }}
			class="absolute right-0 top-full mt-2 w-40 bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 rounded-2xl shadow-xl backdrop-blur-xl z-50 overflow-hidden"
		>
			<div class="p-1">
				{#each locales as l}
					<button
						on:click={() => selectLanguage(l.code)}
						class="w-full flex items-center justify-between px-3 py-2 text-sm rounded-xl hover:bg-slate-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer {$locale ===
						l.code
							? 'text-red-600 font-bold bg-red-50 dark:bg-red-900/10'
							: 'text-slate-600 dark:text-slate-300'}"
					>
						<span class="flex items-center gap-2">
							<span>{l.flag}</span>
							<span>{l.label}</span>
						</span>
						{#if $locale === l.code}
							<Check size={14} class="text-red-500" />
						{/if}
					</button>
				{/each}
			</div>
		</div>
	{/if}
</div>
