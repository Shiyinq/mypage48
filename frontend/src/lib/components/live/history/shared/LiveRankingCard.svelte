<script lang="ts">
	import { Tv, Clock, ChevronRight } from 'lucide-svelte';
	import { OptimizedImage } from '$lib/components/common';
	import { getExternalMediaUrl } from '$lib/utils/media';

	interface RankingItem {
		member_id: string;
		member_name?: string;
		total_watches?: number;
		total_lives?: number;
		total_duration?: number;
		total_viewers?: number;
	}

	interface Props {
		item: RankingItem;
		index: number;
		href: string;
		mode?: 'watched' | 'global';
		memberImage?: string;
		memberImageMedium?: string | null;
		memberImageSmall?: string | null;
		blurHash?: string | null;
		timesLabel: string;
	}

	let {
		item,
		index,
		href,
		memberImage = '',
		memberImageMedium,
		memberImageSmall,
		blurHash,
		timesLabel
	}: Props = $props();

	function formatDuration(seconds: number) {
		const h = Math.floor(seconds / 3600);
		const m = Math.floor((seconds % 3600) / 60);
		const s = Math.floor(seconds % 60);
		if (h > 0) return `${h}h ${m}m ${s}s`;
		if (m > 0) return `${m}m ${s}s`;
		return `${s}s`;
	}

	let rankColor = $derived(
		index === 0
			? 'text-yellow-500 drop-shadow-sm'
			: index === 1
				? 'text-gray-400 drop-shadow-sm'
				: index === 2
					? 'text-amber-700 drop-shadow-sm'
					: 'text-zinc-300 dark:text-zinc-700'
	);
</script>

<a
	{href}
	class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 flex items-center gap-4 hover:border-purple-500/50 hover:shadow-lg transition-all text-left w-full group overflow-hidden relative cursor-pointer"
>
	<!-- Rank Number -->
	<div class="flex-shrink-0 w-8 flex items-center justify-center font-black text-xl {rankColor}">
		#{index + 1}
	</div>

	<!-- Member Image -->
	<div
		class="w-16 h-20 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center shrink-0 overflow-hidden shadow-sm border border-zinc-200 dark:border-zinc-700 group-hover:border-purple-200 dark:group-hover:border-purple-800 transition-colors"
	>
		{#if memberImage}
			<OptimizedImage
				src={getExternalMediaUrl(memberImage)}
				srcMedium={memberImageMedium ? getExternalMediaUrl(memberImageMedium) : null}
				srcSmall={memberImageSmall ? getExternalMediaUrl(memberImageSmall) : null}
				{blurHash}
				alt={item.member_name || item.member_id}
				sizes="64px"
				class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
			/>
		{:else}
			<Tv size={24} class="text-zinc-400" />
		{/if}
	</div>

	<!-- Member Info -->
	<div class="flex-1 min-w-0 py-1">
		<h3
			class="font-black text-base text-slate-900 dark:text-white truncate group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors"
		>
			{item.member_name || item.member_id}
		</h3>

		<div class="flex flex-col gap-1 mt-1.5">
			<div class="flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400">
				<Tv size={12} class={index < 3 ? 'text-red-500' : ''} />
				<span class="font-bold {index < 3 ? 'text-red-600 dark:text-red-400' : ''}">
					{item.total_watches ?? item.total_lives ?? 0}
					{timesLabel}
				</span>
			</div>

			{#if item.total_duration}
				<div class="flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400">
					<Clock size={12} class={index < 3 ? 'text-amber-500' : ''} />
					<span class="font-medium">{formatDuration(item.total_duration)}</span>
				</div>
			{/if}
		</div>
	</div>

	<ChevronRight
		size={20}
		class="text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-2"
	/>
</a>
