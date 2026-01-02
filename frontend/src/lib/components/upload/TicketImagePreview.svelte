<script lang="ts">
	import { ImagePlus, AlertCircle } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let image: string | null = null;
	export let onChangePhoto: () => void;

	const { t } = useTranslation();
</script>

<div class="sticky top-24">
	{#if image}
		<div
			class="relative rounded-3xl overflow-hidden border border-gray-200 dark:border-zinc-700 bg-gray-100 dark:bg-zinc-800 shadow-lg aspect-[4/5] lg:aspect-auto lg:h-[calc(100vh-200px)] group"
		>
			<img src={image} alt="Preview" class="w-full h-full object-contain p-4" />
			<div
				class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
			>
				<button
					on:click={onChangePhoto}
					class="bg-white text-gray-800 px-4 py-2 rounded-full font-bold text-sm flex items-center gap-2 shadow-lg hover:scale-105 transition-transform"
					><ImagePlus class="w-4 h-4" /> {$t('forms.changePhoto')}</button
				>
			</div>
		</div>
	{:else}
		<button
			type="button"
			on:click={onChangePhoto}
			class="w-full rounded-3xl border-3 border-dashed border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 hover:bg-red-50 dark:hover:bg-red-900/20 hover:border-red-200 dark:hover:border-red-500/50 transition-all cursor-pointer flex flex-col items-center justify-center aspect-[4/5] lg:aspect-auto lg:h-[calc(100vh-200px)] text-gray-400 dark:text-gray-500 hover:text-red-500"
		>
			<div class="p-4 rounded-full bg-white dark:bg-zinc-700 shadow-sm mb-4">
				<ImagePlus class="w-8 h-8" />
			</div>
			<p class="font-bold text-lg">{$t('forms.uploadTicketPhoto')}</p>
			<p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{$t('forms.optional')}</p>
		</button>
	{/if}
</div>
