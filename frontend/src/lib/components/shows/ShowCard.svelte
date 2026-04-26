<script lang="ts">
	import { Trophy, ChevronLeft, Music } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { OptimizedImage } from '$lib/components/common';

	interface ShowInfo {
		title: string;
		image: string;
		imageMedium?: string;
		imageSmall?: string;
		blurHash?: string;
	}

	interface Props {
		show: ShowInfo;
		count?: number;
		maxAttendance?: number;
		onClick: () => void;
	}

	let { show, count = 0, maxAttendance = 1, onClick }: Props = $props();

	const { t } = useTranslation();

	let percentage = $derived((count / maxAttendance) * 100);
	let isMostWatched = $derived(count === maxAttendance && count > 0);
</script>

<div
	onclick={onClick}
	onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && onClick()}
	class="relative overflow-hidden rounded-[20px] sm:rounded-2xl cursor-pointer group shadow-sm hover:shadow-xl transition-all duration-300 bg-white dark:bg-zinc-900/50 dark:backdrop-blur-xl border border-gray-100 dark:border-white/5 flex flex-row sm:flex-col h-[8.5rem] sm:h-auto sm:aspect-[2/3]"
	role="button"
	tabindex="0"
>
	<!-- Background Image (Mobile: Left side, Desktop: Full bg) -->
	<div class="relative w-[38%] sm:w-full sm:h-full sm:absolute sm:inset-0 shrink-0 overflow-hidden">
		{#if show.image}
			<OptimizedImage
				src={show.image}
				srcMedium={show.imageMedium}
				srcSmall={show.imageSmall}
				blurHash={show.blurHash}
				alt={show.title}
				sizes="(max-width: 640px) 38vw, (max-width: 1024px) 50vw, 25vw"
				class="w-full h-full transition-transform duration-700 group-hover:scale-105"
			/>
		{:else}
			<div class="w-full h-full bg-zinc-900 flex items-center justify-center">
				<div
					class="w-full h-full idol-gradient opacity-40 absolute inset-0 transition-opacity group-hover:opacity-60"
				></div>
				<Music
					class="w-12 h-12 text-white/20 relative z-10 transform group-hover:scale-110 transition-transform duration-500"
				/>
			</div>
		{/if}
		<!-- Mobile Gradient Overlay (Right to Left) -->
		<div
			class="absolute inset-0 sm:hidden bg-gradient-to-r from-black/20 via-transparent to-black/10"
		></div>

		<!-- Desktop Gradient Overlay (Bottom to Top) -->
		<div
			class="absolute inset-0 hidden sm:block bg-gradient-to-t from-black/95 via-black/40 to-transparent opacity-90 transition-opacity duration-300 group-hover:opacity-100"
		></div>
	</div>

	<!-- Content -->
	<div
		class="relative z-10 flex flex-col justify-between p-3.5 sm:p-5 w-full sm:h-full bg-white dark:bg-transparent sm:bg-transparent"
	>
		<div class="flex flex-col gap-1">
			<!-- Top Tags -->
			<div class="flex items-center gap-2">
				{#if isMostWatched}
					<span
						class="bg-gradient-to-r from-yellow-500 to-amber-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm flex items-center gap-1 self-start border border-white/20"
					>
						<Trophy class="w-2.5 h-2.5" />
						<span class="uppercase tracking-wider">{t('shows.top')}</span>
					</span>
				{/if}
			</div>

			<!-- Title -->
			<h3
				class="text-[15px] sm:text-xl font-bold leading-tight line-clamp-2 sm:line-clamp-3 text-gray-900 dark:text-gray-100 sm:text-white sm:drop-shadow-lg"
			>
				{show.title}
			</h3>
		</div>

		<div class="space-y-3 sm:space-y-4">
			<!-- Stats Row -->
			<div class="flex items-end justify-between">
				<div class="flex items-center gap-2">
					<div
						class={`inline-flex items-center px-2.5 py-0.5 rounded-md text-[10px] sm:text-xs font-bold uppercase tracking-wide border transition-all ${
							count > 0
								? 'bg-red-50 text-red-600 border-red-100 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20'
								: 'bg-gray-50 text-gray-500 border-gray-100 dark:bg-zinc-800 dark:text-zinc-500 dark:border-zinc-700'
						} sm:bg-white/10 sm:text-white/90 sm:border-white/20 sm:backdrop-blur-md`}
					>
						{count > 0
							? t('theater.setlists.attendedCount', { count })
							: t('theater.setlists.notAttended')}
					</div>
				</div>

				{#if count > 0}
					<span
						class="text-[10px] sm:text-xs text-red-500 dark:text-red-400 sm:text-white/90 font-medium hidden sm:flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-all translate-x-2 group-hover:translate-x-0"
					>
						{t('shows.viewHistory')}
						<ChevronLeft class="w-3 h-3 rotate-180" />
					</span>
				{/if}
			</div>

			<!-- Progress Bar Visual -->
			<div>
				<div class="flex justify-end mb-1">
					<span class="text-[10px] font-medium text-gray-400 dark:text-zinc-500 sm:text-gray-300">
						{count > 0 ? `${percentage.toFixed(0)}% ${t('shows.toTop')}` : t('shows.notSeen')}
					</span>
				</div>
				<div
					class="w-full bg-gray-100 dark:bg-zinc-800 sm:bg-white/20 rounded-full h-1 sm:h-1.5 overflow-hidden"
				>
					<div
						class={`h-full rounded-full transition-all duration-1000 ease-out ${
							count > 0
								? 'bg-gradient-to-r from-red-500 to-pink-600 shadow-[0_0_10px_rgba(236,72,153,0.4)]'
								: 'bg-transparent'
						}`}
						style={`width: ${count > 0 ? percentage : 0}%`}
					></div>
				</div>
			</div>
		</div>
	</div>
</div>
