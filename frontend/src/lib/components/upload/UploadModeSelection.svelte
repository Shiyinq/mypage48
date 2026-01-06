<script lang="ts">
	import { ScanLine, Keyboard, X } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let onScanClick: () => void;
	export let onManualClick: () => void;
	export let onCancel: () => void;

	const { t } = useTranslation();
</script>

<div
	class="min-h-[80vh] flex flex-col items-center justify-center p-4 animate-fade-in max-w-4xl mx-auto"
>
	<div class="text-center mb-10">
		<h2 class="text-3xl font-black text-gray-800 dark:text-white mb-2">{$t('upload.title')}</h2>
		<p class="text-gray-500 dark:text-gray-400">{$t('upload.subtitle')}</p>
	</div>
	<div class="grid md:grid-cols-2 gap-6 w-full">
		<button
			on:click={onScanClick}
			class="group relative overflow-hidden bg-white dark:bg-zinc-800 p-8 rounded-3xl border-2 border-red-100 dark:border-red-900/30 hover:border-red-500 dark:hover:border-red-500 shadow-lg hover:shadow-xl transition-all duration-300 text-left flex flex-col h-64 justify-between cursor-pointer"
		>
			<div
				class="absolute top-0 right-0 w-32 h-32 bg-red-50 dark:bg-red-900/10 rounded-bl-full -mr-10 -mt-10 transition-transform group-hover:scale-110"
			></div>
			<div
				class="p-4 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-2xl w-fit z-10"
			>
				<ScanLine class="w-8 h-8" />
			</div>
			<div class="z-10">
				<h3
					class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1 group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors"
				>
					{$t('upload.scanTicket')}
				</h3>
				<p class="text-sm font-medium text-gray-600 dark:text-gray-400 leading-relaxed">
					{$t('upload.scanDescription')}
				</p>
			</div>
		</button>
		<button
			on:click={onManualClick}
			class="group relative overflow-hidden bg-white dark:bg-zinc-800 p-8 rounded-3xl border-2 border-gray-100 dark:border-zinc-700 hover:border-gray-400 dark:hover:border-zinc-500 shadow-lg hover:shadow-xl transition-all duration-300 text-left flex flex-col h-64 justify-between cursor-pointer"
		>
			<div
				class="absolute top-0 right-0 w-32 h-32 bg-gray-50 dark:bg-zinc-700/50 rounded-bl-full -mr-10 -mt-10 transition-transform group-hover:scale-110"
			></div>
			<div
				class="p-4 bg-gray-100 dark:bg-zinc-700 text-gray-600 dark:text-gray-300 rounded-2xl w-fit z-10"
			>
				<Keyboard class="w-8 h-8" />
			</div>
			<div class="z-10">
				<h3
					class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors"
				>
					{$t('upload.manualEntry')}
				</h3>
				<p class="text-sm font-medium text-gray-600 dark:text-gray-400">
					{$t('upload.manualDescription')}
				</p>
			</div>
		</button>
	</div>
	<button
		on:click={onCancel}
		class="mt-12 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 font-medium text-sm flex items-center gap-2 px-4 py-2 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
	>
		<X class="w-4 h-4" />
		{$t('common.cancel')}
	</button>
</div>
