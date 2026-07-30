<script lang="ts">
	import { Users, Clock } from 'lucide-svelte';
	import { now } from '$lib/stores/live.svelte';
	import { formatDuration } from '$lib/utils/time';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		view_num?: number | undefined;
		start_at?: string | undefined | null;
		variant?: 'overlay' | 'compact' | 'detailed';
		showSeconds?: boolean;
		showLabel?: boolean;
		className?: string;
	}

	let {
		view_num = 0,
		start_at = null,
		variant = 'overlay',
		showSeconds = true,
		showLabel = false,
		className = ''
	}: Props = $props();

	let hasViewers = $derived((view_num ?? 0) > 0);
	let hasStartAt = $derived(!!start_at);

	const variants = {
		overlay: {
			container:
				'flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md border border-white/10 shadow-lg',
			icon: 10,
			text: 'text-[9px] font-black text-white px-0.5',
			viewerIconColor: 'text-sky-400',
			durationIconColor: 'text-red-400',
			durationTextColor: 'text-white/90 font-bold',
			dot: 'w-1 h-1 rounded-full bg-white/30 mx-0.5'
		},
		compact: {
			container: 'flex items-center gap-1.5',
			icon: 10,
			text: 'text-[10px] font-bold text-gray-500',
			viewerIconColor: 'text-sky-500',
			durationIconColor: 'text-red-400',
			durationTextColor: 'text-red-500',
			dot: 'w-0.5 h-0.5 rounded-full bg-slate-300'
		},
		detailed: {
			container:
				'flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/80 dark:bg-black/60 backdrop-blur-md border border-gray-200 dark:border-white/10 shadow-sm dark:shadow-xl',
			icon: 14,
			text: 'text-[11px] font-black text-slate-900 dark:text-white',
			viewerIconColor: 'text-sky-600 dark:text-sky-400',
			durationIconColor: 'text-red-500 dark:text-red-400',
			durationTextColor: 'text-slate-900 dark:text-white',
			dot: 'w-px h-3 bg-gray-200 dark:bg-white/20 mx-1'
		}
	};

	let v = $derived(variants[variant]);
</script>

<div class="{v.container} {className} max-w-full">
	{#if hasViewers}
		<div class="flex items-center gap-1 shrink-0 min-w-0">
			<Users size={v.icon} class="{v.viewerIconColor} shrink-0" />
			<span class="{v.text} tabular-nums truncate">
				{view_num?.toLocaleString() ?? 0}
			</span>
		</div>
	{/if}

	{#if hasViewers && hasStartAt}
		{#if variant === 'detailed'}
			<div class="{v.dot} shrink-0"></div>
		{:else}
			<div class="{v.dot} shrink-0"></div>
		{/if}
	{/if}

	{#if hasStartAt}
		<div class="flex items-center gap-1 min-w-0">
			<Clock size={v.icon} class="{v.durationIconColor} shrink-0" />
			<span class="{v.text} {v.durationTextColor} tabular-nums truncate">
				{#if showLabel}
					<span class="opacity-60 text-[9px] mr-1 truncate">{t('theater.live.liveDuration')}</span>
				{/if}
				{formatDuration(start_at, $now, showSeconds)}
			</span>
		</div>
	{/if}
</div>
