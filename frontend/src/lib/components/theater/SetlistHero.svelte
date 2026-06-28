<script lang="ts">
	import type { SetlistDetailResponse } from '$lib/apis/setlists';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Trophy } from 'lucide-svelte';
	import { OptimizedImage } from '$lib/components/common';

	interface Props {
		detail: SetlistDetailResponse;
	}

	let { detail }: Props = $props();

	const { t } = useTranslation();
</script>

<div class="relative w-full flex flex-col bg-white dark:bg-zinc-900">
	<div class="relative w-full min-h-[280px] sm:min-h-[350px] flex flex-col justify-end">
		<!-- Background Image -->
		<div class="absolute inset-0 w-full h-full overflow-hidden bg-gray-100 dark:bg-zinc-800">
			<OptimizedImage
				src={detail.imageUrl}
				srcMedium={detail.imageUrl_medium}
				srcSmall={detail.imageUrl_small}
				blurHash={detail.blurHash}
				alt={detail.title}
				sizes="100vw"
				class="w-full h-full object-cover transition-transform duration-700 hover:scale-105"
			/>
		</div>

		<!-- Hero Content Overlay with seamless fade to background color -->
		<div
			class="relative z-20 px-6 sm:px-10 pt-[150px] sm:pt-[200px] pb-6 sm:pb-10 flex flex-col justify-end w-full bg-gradient-to-t from-white via-white/95 to-transparent dark:from-zinc-900 dark:via-zinc-900/95 pointer-events-none"
		>
			<div
				class="pointer-events-auto w-full flex items-end justify-between gap-6 max-w-5xl mx-auto"
			>
				<div class="space-y-3 max-w-full md:max-w-2xl">
					<!-- Badges -->
					<div class="flex flex-wrap gap-2 animate-slide-up" style="animation-delay: 100ms;">
						{#if detail.watched.isMostWatched}
							<span
								class="px-2.5 py-1 bg-yellow-400/20 backdrop-blur-md border border-yellow-400/30 text-yellow-700 dark:text-yellow-400 text-[10px] md:text-xs font-bold rounded-full flex items-center gap-1 md:gap-1.5 shadow-sm"
							>
								<Trophy class="w-3 h-3 md:w-3.5 md:h-3.5" />
								{t('shows.top')}
							</span>
						{/if}
						<span
							class="px-2.5 py-1 bg-gray-100 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-gray-800 dark:text-gray-200 text-[10px] md:text-xs font-medium rounded-full"
						>
							{detail.type === 'setlist'
								? t('theater.setlists.section')
								: t('theater.setlists.events')}
						</span>
					</div>

					<!-- Title -->
					<div class="animate-slide-up" style="animation-delay: 200ms;">
						<h1
							class="text-3xl md:text-5xl lg:text-6xl font-black text-gray-900 dark:text-white tracking-tight leading-[1.15] mb-2"
						>
							{detail.title}
						</h1>
						{#if detail.titleJapanese}
							<p
								class="text-base md:text-xl text-gray-500 dark:text-gray-400 font-medium tracking-wide"
							>
								{detail.titleJapanese}
							</p>
						{/if}
					</div>

					<!-- Description -->
					<p
						class="text-gray-700 dark:text-gray-300 text-sm md:text-base leading-relaxed max-w-xl animate-slide-up line-clamp-3 md:line-clamp-none"
						style="animation-delay: 300ms;"
					>
						{detail.description}
					</p>
				</div>

				<!-- Hero Stats (Attendance) -->
				<div
					class="hidden md:flex flex-col items-center min-w-[140px] px-6 py-4 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md border border-gray-200 dark:border-white/10 rounded-2xl shadow-sm animate-slide-up"
					style="animation-delay: 400ms;"
				>
					<span class="text-5xl font-black text-gray-900 dark:text-white tracking-tighter mb-1">
						{detail.watched.count}
					</span>
					<span
						class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest text-center"
					>
						{#each t('shows.performancesAttended').split(' ') as word, i}
							{word}{#if i < t('shows.performancesAttended').split(' ').length - 1}<br />{/if}
						{/each}
					</span>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	@keyframes slide-up {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.animate-slide-up {
		animation: slide-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
		opacity: 0;
	}
</style>
