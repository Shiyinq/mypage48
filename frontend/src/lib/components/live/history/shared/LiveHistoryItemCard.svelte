<script lang="ts">
	import { Tv, Clock, ChevronRight, Calendar, History } from 'lucide-svelte';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import { OptimizedImage } from '$lib/components/common';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatLiveStartEnd } from '$lib/utils/time';

	const { t, locale } = useTranslation();

	interface Props {
		href: string;
		memberImage?: string;
		memberName: string;
		liveTitle?: string;
		platform: string;
		dateStr: string; // formatted date (e.g. Sep 12, 2024)
		timeStr?: string; // formatted time (e.g. 14:00 PM)
		duration?: number;
		peakViewers?: number;
		mode?: 'watched' | 'global';
		isLive?: boolean;
		startAt?: string;
		endAt?: string;
	}

	let {
		href,
		memberImage = '',
		memberName,
		liveTitle,
		platform,
		dateStr,
		timeStr,
		duration,
		peakViewers,
		mode = 'watched',
		isLive = false,
		startAt,
		endAt
	}: Props = $props();

	function formatDuration(seconds: number) {
		const h = Math.floor(seconds / 3600);
		const m = Math.floor((seconds % 3600) / 60);
		const s = Math.floor(seconds % 60);
		if (h > 0) return `${h}h ${m}m ${s}s`;
		if (m > 0) return `${m}m ${s}s`;
		return `${s}s`;
	}
</script>

<a
	{href}
	class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 flex flex-col gap-3 hover:border-red-500/50 hover:shadow-lg transition-all text-left w-full group relative overflow-hidden block"
>
	{#if mode === 'global'}
		<!-- Subtle background logo for aesthetic -->
		<div
			class="absolute -right-4 -bottom-4 opacity-[0.03] dark:opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none"
		>
			<History size={100} />
		</div>
	{/if}

	<div class="flex items-center justify-between z-10">
		<div class="flex items-center gap-2 flex-wrap">
			{#if isLive}
				<div
					class="flex items-center gap-1 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 px-2 py-0.5 rounded-md text-[10px] font-bold"
				>
					<div class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></div>
					<span>LIVE</span>
				</div>
			{:else}
				<span class="text-xs font-medium text-zinc-500 dark:text-zinc-400">
					{#if mode === 'global' && timeStr}
						<div class="flex items-center gap-1.5">
							<History size={12} />
							<span>{timeStr}</span>
						</div>
					{:else}
						{dateStr}
					{/if}
				</span>
			{/if}
		</div>

		<div class="flex items-center gap-2">
			{#if mode === 'global' && peakViewers}
				<div class="flex items-center gap-1 text-xs font-bold text-slate-700 dark:text-zinc-300">
					<span>{peakViewers.toLocaleString()}</span>
					<span class="text-[10px] text-zinc-400 font-medium uppercase tracking-wider"
						>{t('liveHistory.views')}</span
					>
				</div>
			{/if}
			<PlatformLogo {platform} size="sm" />
		</div>
	</div>

	{#if mode === 'watched'}
		<div class="flex items-center justify-between mt-2 z-10">
			<div class="flex items-center gap-3">
				<div
					class="w-12 h-16 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center shrink-0 overflow-hidden shadow-sm"
				>
					{#if memberImage}
						<OptimizedImage
							src={getExternalMediaUrl(memberImage)}
							alt={memberName}
							class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
						/>
					{:else}
						<Tv size={20} class="text-red-500" />
					{/if}
				</div>
				<div class="flex flex-col">
					<span class="text-lg font-black text-slate-900 dark:text-white">{memberName}</span>
					{#if liveTitle}
						<span class="text-sm font-medium text-zinc-600 dark:text-zinc-300 line-clamp-1"
							>{liveTitle}</span
						>
					{/if}
				</div>
			</div>
			<ChevronRight
				size={20}
				class="text-zinc-400 shrink-0 ml-2 group-hover:text-red-500 transition-colors"
			/>
		</div>
	{:else}
		<!-- Global Mode Layout -->
		<div class="flex items-start gap-4 mt-2 z-10">
			<div
				class="w-16 h-16 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center shrink-0 overflow-hidden shadow-sm"
			>
				{#if memberImage}
					<OptimizedImage
						src={getExternalMediaUrl(memberImage)}
						alt={memberName}
						class="w-full h-full object-cover"
					/>
				{:else}
					<Tv size={20} class="text-zinc-400" />
				{/if}
			</div>
			<div class="flex flex-col min-w-0 flex-1">
				<div
					class="flex items-center gap-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400 mb-0.5"
				>
					<Calendar size={12} />
					<span>{startAt ? formatLiveStartEnd(startAt, endAt, locale.value) : dateStr}</span>
				</div>
				<span
					class="text-lg font-black text-slate-900 dark:text-white truncate leading-tight"
					title={memberName}>{memberName}</span
				>
				{#if liveTitle}
					<span
						class="text-sm font-medium text-zinc-600 dark:text-zinc-300 line-clamp-1 mt-0.5"
						title={liveTitle}>{liveTitle}</span
					>
				{/if}
				{#if !isLive}
					<div
						class="flex items-center gap-1.5 mt-1.5 text-xs font-bold text-zinc-500 dark:text-zinc-400"
					>
						<Clock size={12} />
						<span>{duration ? formatDuration(duration) : 'Ended'}</span>
					</div>
				{/if}
			</div>
		</div>
	{/if}

	{#if mode === 'watched'}
		<div
			class="mt-auto pt-2 flex items-center justify-between border-t border-gray-100 dark:border-zinc-800 z-10"
		>
			<div
				class="flex items-center gap-1.5 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 px-2 py-1 rounded-md"
			>
				<Clock size={14} />
				<div class="flex items-center gap-1 text-xs">
					<span class="font-medium opacity-70">{t('liveHistory.watchedFor')}</span>
					<span class="font-bold">{duration ? formatDuration(duration) : '0s'}</span>
				</div>
			</div>

			<span class="text-[10px] font-medium text-zinc-500 dark:text-zinc-400">
				{timeStr}
			</span>
		</div>
	{/if}
</a>
