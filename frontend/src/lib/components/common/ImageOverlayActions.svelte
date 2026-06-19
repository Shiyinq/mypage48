<script lang="ts">
	import { ImagePlus, Crop, Trash2 } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		onSelect: () => void;
		onEdit?: () => void;
		onDelete?: () => void;
		variant?: 'ticket' | 'twoshot';
	}

	let { onSelect, onEdit, onDelete, variant = 'ticket' }: Props = $props();
	const { t } = useTranslation();
</script>

<div
	class="absolute inset-0 bg-black/40 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity flex items-center justify-center
    {variant === 'ticket' ? 'gap-1.5 sm:gap-3 flex-row flex-wrap px-2' : 'gap-2 flex-col'}"
>
	<button
		type="button"
		onclick={onSelect}
		class="font-bold transition cursor-pointer flex items-center gap-1.5 sm:gap-2
        {variant === 'ticket'
			? 'bg-white text-gray-800 px-2.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm shadow-lg hover:scale-105 transition-transform'
			: 'bg-white/20 hover:bg-white/30 text-white px-3 py-1 rounded text-xs'}"
	>
		{#if variant === 'ticket'}
			<ImagePlus class="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0" />
		{/if}
		{t('forms.changePhoto')}
	</button>

	{#if onEdit}
		<button
			type="button"
			onclick={(e) => {
				e.stopPropagation();
				onEdit();
			}}
			class="font-bold transition cursor-pointer flex items-center gap-1.5 sm:gap-2
            {variant === 'ticket'
				? 'bg-white text-gray-800 px-2.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm shadow-lg hover:scale-105 transition-transform'
				: 'bg-white/20 hover:bg-white/30 text-white px-3 py-1 rounded text-xs'}"
		>
			<Crop
				class={variant === 'ticket' ? 'w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0' : 'w-3 h-3 shrink-0'}
			/>
			Crop
		</button>
	{/if}

	{#if onDelete}
		<button
			type="button"
			onclick={(e) => {
				e.stopPropagation();
				onDelete();
			}}
			class="font-bold transition cursor-pointer flex items-center gap-1.5 sm:gap-2 bg-red-500/80 hover:bg-red-600 text-white
            {variant === 'ticket'
				? 'px-2.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm shadow-lg hover:scale-105 transition-transform'
				: 'px-3 py-1 rounded text-xs'}"
		>
			<Trash2
				class={variant === 'ticket' ? 'w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0' : 'w-3 h-3 shrink-0'}
			/>
			{t('common.delete')}
		</button>
	{/if}
</div>
