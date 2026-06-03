<script lang="ts">
	import { ChevronLeft } from 'lucide-svelte';
	import type { ComponentType } from 'svelte';

	interface Props {
		title: string;
		subtitle?: string;
		icon: ComponentType;
		iconColor?: string;
		total?: number;
		totalLabel?: string;
		onBack?: () => void;
	}

	let {
		title,
		subtitle = '',
		icon: Icon,
		iconColor = 'text-red-500',
		total = 0,
		totalLabel = '',
		onBack
	}: Props = $props();

	function handleBack() {
		if (onBack) {
			onBack();
		} else {
			history.back();
		}
	}
</script>

<div
	class="h-14 border-b border-gray-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md flex items-center justify-between px-4 z-[10000] shrink-0"
>
	<button onclick={handleBack} class="flex items-center gap-3 cursor-pointer group text-left">
		<div
			class="flex items-center justify-center w-8 h-8 rounded-full group-hover:bg-gray-100 dark:group-hover:bg-zinc-800 text-slate-600 dark:text-zinc-400 transition-colors shrink-0"
		>
			<ChevronLeft size={20} />
		</div>
		<div class="flex flex-col min-w-0">
			<h1
				class="text-sm font-bold text-slate-900 dark:text-white truncate flex items-center gap-1.5"
			>
				<Icon size={14} class={iconColor} />
				{title}
			</h1>
			{#if subtitle || (total > 0 && totalLabel)}
				<p class="text-[10px] text-slate-500 dark:text-zinc-400 truncate font-medium">
					{#if subtitle}
						{subtitle}
						{#if total > 0 && totalLabel}
							{' · '}
						{/if}
					{/if}
					{#if total > 0 && totalLabel}
						{total} {totalLabel}
					{/if}
				</p>
			{/if}
		</div>
	</button>
</div>
