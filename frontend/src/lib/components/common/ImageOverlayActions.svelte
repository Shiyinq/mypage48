<script lang="ts">
	import { ImagePlus, Crop } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		onSelect: () => void;
		onEdit?: () => void;
		variant?: 'ticket' | 'twoshot';
	}

	let { onSelect, onEdit, variant = 'ticket' }: Props = $props();
	const { t } = useTranslation();
</script>

<div
	class="absolute inset-0 bg-black/40 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity flex items-center justify-center
    {variant === 'ticket' ? 'gap-3 flex-row' : 'gap-2 flex-col'}"
>
	<button
		type="button"
		onclick={onSelect}
		class="font-bold transition cursor-pointer flex items-center gap-2
        {variant === 'ticket'
			? 'bg-white text-gray-800 px-4 py-2 rounded-full text-sm shadow-lg hover:scale-105 transition-transform'
			: 'bg-white/20 hover:bg-white/30 text-white px-3 py-1 rounded text-xs'}"
	>
		{#if variant === 'ticket'}
			<ImagePlus class="w-4 h-4" />
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
			class="font-bold transition cursor-pointer flex items-center gap-2
            {variant === 'ticket'
				? 'bg-white text-gray-800 px-4 py-2 rounded-full text-sm shadow-lg hover:scale-105 transition-transform'
				: 'bg-white/20 hover:bg-white/30 text-white px-3 py-1 rounded text-xs'}"
		>
			<Crop class={variant === 'ticket' ? 'w-4 h-4' : 'w-3 h-3'} />
			Crop
		</button>
	{/if}
</div>
