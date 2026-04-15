<script lang="ts">
	import type { SetlistDetailResponse } from '$lib/apis/setlists';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Trophy } from 'lucide-svelte';

	interface Props {
		detail: SetlistDetailResponse;
	}

	let { detail }: Props = $props();

	const { t } = useTranslation();
</script>

<div
	class="relative w-full min-h-[400px] rounded-[2.5rem] overflow-hidden shadow-2xl mb-8 group flex flex-col justify-end"
>
	<!-- Background Image with Parallax-like effect -->
	<div class="absolute inset-0">
		<img
			src={detail.imageUrl}
			alt={detail.title}
			class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-105"
		/>
		<!-- Gradient Mesh Overlay -->
		<div
			class="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/60 to-transparent opacity-90"
		></div>
		<div
			class="absolute inset-0 bg-gradient-to-r from-gray-900/80 via-transparent to-transparent"
		></div>
	</div>

	<!-- Content Container -->
	<div class="relative z-10 p-6 md:p-12 w-full">
		<div class="flex items-start justify-between gap-6 mb-6 md:mb-12">
			<div class="space-y-3 md:space-y-4 max-w-full md:max-w-2xl">
				<!-- Badges -->
				<div class="flex flex-wrap gap-2 animate-slide-up" style="animation-delay: 100ms;">
					{#if detail.watched.isMostWatched}
						<span
							class="px-2.5 py-1 bg-yellow-400/20 backdrop-blur-md border border-yellow-400/30 text-yellow-300 text-[10px] md:text-xs font-bold rounded-full flex items-center gap-1 md:gap-1.5 shadow-lg shadow-yellow-900/20"
						>
							<Trophy class="w-3 h-3 md:w-3.5 md:h-3.5" />
							{t('shows.top')}
						</span>
					{/if}
					<span
						class="px-2.5 py-1 bg-white/10 backdrop-blur-md border border-white/20 text-white/90 text-[10px] md:text-xs font-medium rounded-full"
					>
						{detail.type === 'setlist'
							? t('theater.setlists.section')
							: t('theater.setlists.events')}
					</span>
				</div>

				<!-- Title -->
				<div class="animate-slide-up" style="animation-delay: 200ms;">
					<h1
						class="text-3xl md:text-5xl lg:text-6xl font-black text-white tracking-tight leading-[1.15] mb-2 drop-shadow-lg"
					>
						{detail.title}
					</h1>
					{#if detail.titleJapanese}
						<p class="text-base md:text-xl text-white/50 font-medium tracking-wide">
							{detail.titleJapanese}
						</p>
					{/if}
				</div>

				<!-- Description -->
				<p
					class="text-gray-300 text-xs md:text-base leading-relaxed max-w-xl animate-slide-up line-clamp-3 md:line-clamp-none"
					style="animation-delay: 300ms;"
				>
					{detail.description}
				</p>
			</div>

			<!-- Hero Stats (Attendance) -->
			<div class="hidden md:block animate-slide-up" style="animation-delay: 400ms;">
				<div
					class="bg-white/10 backdrop-blur-xl border border-white/20 p-6 rounded-2xl flex flex-col items-center min-w-[140px]"
				>
					<span class="text-5xl font-black text-white tracking-tighter mb-1">
						{detail.watched.count}
					</span>
					<span class="text-xs font-bold text-white/60 uppercase tracking-widest text-center">
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
