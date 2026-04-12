<script lang="ts">
	import { ImagePlus } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	import { dragDrop } from '$lib/actions/dragDrop';

	interface Props {
		image?: string | null;
		onChangePhoto: () => void;
		ondrop?: (file: File) => void;
	}

	let { image = null, onChangePhoto, ondrop }: Props = $props();

	const { t } = useTranslation();

	let isDragging = $state(false);
</script>

<div
	class="sticky top-24"
	role="region"
	aria-label="Image Upload Dropzone"
	use:dragDrop={{
		onDrop: (file) => ondrop?.(file),
		onDragChange: (state) => (isDragging = state)
	}}
>
	{#if image}
		<div
			class="relative rounded-3xl overflow-hidden border shadow-lg aspect-[4/5] lg:aspect-auto lg:h-[calc(100vh-200px)] group transition-all duration-200
			{isDragging
				? 'border-red-500 bg-red-50 dark:bg-red-900/10 ring-4 ring-red-500/20 scale-[1.02]'
				: 'border-gray-200 dark:border-zinc-700 bg-gray-100 dark:bg-zinc-800'}"
		>
			<img src={image} alt="Preview" class="w-full h-full object-contain p-4" />
			<div
				class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
			>
				<button
					onclick={onChangePhoto}
					class="bg-white text-gray-800 px-4 py-2 rounded-full font-bold text-sm flex items-center gap-2 shadow-lg hover:scale-105 transition-transform"
					><ImagePlus class="w-4 h-4" /> {$t('forms.changePhoto')}</button
				>
			</div>
		</div>
	{:else}
		<button
			type="button"
			onclick={onChangePhoto}
			class="w-full rounded-3xl border-3 border-dashed transition-all cursor-pointer flex flex-col items-center justify-center aspect-[4/5] lg:aspect-auto lg:h-[calc(100vh-200px)]
			{isDragging
				? 'border-red-500 bg-red-50 dark:bg-red-900/10 text-red-500 scale-[1.02] ring-4 ring-red-500/20'
				: 'border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 hover:bg-red-50 dark:hover:bg-red-900/20 hover:border-red-200 dark:hover:border-red-500/50 text-gray-400 dark:text-gray-500 hover:text-red-500'}"
		>
			<div
				class="p-4 rounded-full shadow-sm mb-4 {isDragging
					? 'bg-red-100 dark:bg-red-900/20 text-red-500'
					: 'bg-white dark:bg-zinc-700'}"
			>
				<ImagePlus class="w-8 h-8" />
			</div>
			<p class="font-bold text-lg">{$t('forms.uploadTicketPhoto')}</p>
			<p class="{isDragging ? 'text-red-400' : 'text-gray-400 dark:text-gray-500'} text-xs mt-1">
				{$t('forms.optional')}
			</p>
		</button>
	{/if}
</div>
