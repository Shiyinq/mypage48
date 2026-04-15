<script lang="ts">
	import { Equal, RotateCcw, ArrowLeft, Heart } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import type { Member } from '$lib/apis/members';
	import { fade } from 'svelte/transition';
	import { getMemberFrame } from '$lib/constants';

	const { t } = useTranslation();

	interface Props {
		numQuestion: number;
		displayProgress: number;
		leftMember?: Member | null;
		rightMember?: Member | null;
		isAnimating?: boolean;
		lastSelectedSide?: 'left' | 'right' | 'tie' | null;
		hasHistory?: boolean;
		variant?: 'public' | 'theater';
		onselect?: (flag: number) => void;
		onundo?: () => void;
		onexit?: () => void;
	}

	let {
		numQuestion,
		displayProgress,
		leftMember = null,
		rightMember = null,
		isAnimating = false,
		lastSelectedSide = null,
		hasHistory = false,
		variant = 'public',
		onselect,
		onundo,
		onexit
	}: Props = $props();

	function handleImageError(e: Event) {
		const target = e.currentTarget as HTMLImageElement;
		target.src = 'https://placehold.co/640x960?text=JKT48';
	}

	function handleSelect(flag: number) {
		onselect?.(flag);
	}

	function undo() {
		onundo?.();
	}

	function restart() {
		onexit?.();
	}

	let isPublic = $derived(variant === 'public');
</script>

<div
	in:fade
	class="w-full max-w-2xl px-4 sm:px-4 space-y-6 flex flex-col items-center overflow-hidden"
>
	<div class="w-full space-y-2">
		<div class="flex justify-between items-end px-2">
			<div class="space-y-0.5">
				<h2
					class={`font-black text-lg uppercase tracking-tighter ${isPublic ? 'text-slate-900 dark:text-white' : 'text-themed'}`}
				>
					{t('theater.sorter.sorting')}
				</h2>
				<p
					class={`text-[8px] font-black uppercase tracking-widest ${isPublic ? 'text-slate-400' : 'text-themed-secondary'}`}
				>
					{t('theater.sorter.questionLabel', { num: numQuestion })}
				</p>
			</div>
			<div class="text-right">
				<span
					class={`font-black text-2xl italic tracking-tighter ${isPublic ? 'text-red-600' : 'text-rose-500'}`}
					>{displayProgress}%</span
				>
			</div>
		</div>
		<div
			class="h-3 w-full bg-slate-100 dark:bg-zinc-800 rounded-full overflow-hidden p-1 shadow-inner ring-1 ring-slate-100 dark:ring-zinc-700"
		>
			<div
				class={`h-full bg-gradient-to-r transition-all duration-500 ease-out rounded-full shadow-lg ${isPublic ? 'from-red-500 to-red-600 shadow-red-500/40' : 'from-rose-500 to-rose-600 shadow-rose-500/40'}`}
				style="width: {displayProgress}%"
			></div>
		</div>
	</div>

	<div
		class={`grid grid-cols-[1fr_auto_1fr] items-center gap-1.5 md:gap-8 w-full max-w-2xl ${isPublic ? '' : 'flex-none flex flex-col justify-center min-h-0 py-1'}`}
	>
		<button
			onclick={() => handleSelect(1)}
			disabled={isAnimating}
			class={`group relative aspect-[2/3] md:aspect-[3/4] rounded-xl md:rounded-2xl overflow-hidden border-2 md:border-4 border-transparent transition-all active:scale-95 bg-slate-100 dark:bg-zinc-800 cursor-pointer shadow-xl mx-auto w-full max-w-[135px] md:max-w-none ${
				isPublic
					? 'hover:border-red-600 hover:shadow-2xl hover:shadow-red-500/20'
					: 'hover:border-rose-500 hover:shadow-2xl hover:shadow-rose-500/20 h-full max-h-[47vh] min-h-[150px] md:min-h-[225px]'
			} ${
				lastSelectedSide === 'left' || lastSelectedSide === 'tie'
					? 'win-animation'
					: lastSelectedSide === 'right'
						? 'lose-animation'
						: ''
			}`}
		>
			<img
				src={getExternalMediaUrl(leftMember?.img)}
				alt={leftMember?.name}
				class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
				onerror={handleImageError}
			/>
			<img
				src={getMemberFrame(leftMember?.member_type)}
				alt="frame"
				class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
			/>
			<div
				class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
			></div>
			<div class="absolute bottom-3 left-3 right-3 text-left z-30">
				<span
					class={`px-1.5 py-0.5 text-white text-[7px] font-black rounded-md uppercase tracking-widest mb-1 block w-fit ${isPublic ? 'bg-red-600' : 'bg-rose-500'}`}
					>{t('theater.sorter.genLabel', { gen: leftMember?.generation ?? '' })}</span
				>
				<h3 class="text-white text-xs md:text-sm font-black leading-tight drop-shadow-md truncate">
					{leftMember?.name}
				</h3>
			</div>

			{#if lastSelectedSide === 'left' || lastSelectedSide === 'tie'}
				<div class="absolute inset-0 flex items-center justify-center z-50 pointer-events-none">
					<Heart
						class={`fill-current w-16 h-16 heart-float ${isPublic ? 'text-red-500' : 'text-rose-500'}`}
					/>
				</div>
			{:else if lastSelectedSide === 'right'}
				<div class="absolute inset-0 flex items-center justify-center z-50 pointer-events-none">
					<div class="w-16 h-16 heart-break flex items-center justify-center">
						<svg viewBox="0 0 24 24" class="w-full h-full drop-shadow-lg">
							<path
								d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
								fill="#94a3b8"
							/>
							<path
								d="M12 5l-2 3 4 3-3 4 3 3-2 3"
								stroke="white"
								stroke-width="2"
								fill="none"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
						</svg>
					</div>
				</div>
			{/if}
		</button>

		<div
			class={`z-10 w-6 h-6 md:w-10 md:h-10 flex items-center justify-center bg-white dark:bg-zinc-900 rounded-full shadow-2xl border md:border-4 font-black italic text-[6px] md:text-[10px] ${
				isPublic
					? 'border-red-600 text-red-600 animate-pulse'
					: 'border-rose-500 text-rose-500 animate-bounce-slow'
			} ${isAnimating ? 'vs-pulse' : ''}`}
		>
			VS
		</div>

		<button
			onclick={() => handleSelect(-1)}
			disabled={isAnimating}
			class={`group relative aspect-[2/3] md:aspect-[3/4] rounded-xl md:rounded-2xl overflow-hidden border-2 md:border-4 border-transparent transition-all active:scale-95 bg-slate-100 dark:bg-zinc-800 cursor-pointer shadow-xl mx-auto w-full max-w-[135px] md:max-w-none ${
				isPublic
					? 'hover:border-red-600 hover:shadow-2xl hover:shadow-red-500/20'
					: 'hover:border-rose-500 hover:shadow-2xl hover:shadow-rose-500/20 h-full max-h-[47vh] min-h-[150px] md:min-h-[225px]'
			} ${
				lastSelectedSide === 'right' || lastSelectedSide === 'tie'
					? 'win-animation'
					: lastSelectedSide === 'left'
						? 'lose-animation'
						: ''
			}`}
		>
			<img
				src={getExternalMediaUrl(rightMember?.img)}
				alt={rightMember?.name}
				class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
				onerror={handleImageError}
			/>
			<img
				src={getMemberFrame(rightMember?.member_type)}
				alt="frame"
				class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
			/>
			<div
				class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
			></div>
			<div class="absolute bottom-3 left-3 right-3 text-left z-30">
				<span
					class={`px-1.5 py-0.5 text-white text-[7px] font-black rounded-md uppercase tracking-widest mb-1 block w-fit ${isPublic ? 'bg-red-600' : 'bg-rose-500'}`}
					>{t('theater.sorter.genLabel', { gen: rightMember?.generation ?? '' })}</span
				>
				<h3 class="text-white text-xs md:text-sm font-black leading-tight drop-shadow-md truncate">
					{rightMember?.name}
				</h3>
			</div>

			{#if lastSelectedSide === 'right' || lastSelectedSide === 'tie'}
				<div class="absolute inset-0 flex items-center justify-center z-50 pointer-events-none">
					<Heart
						class={`fill-current w-16 h-16 heart-float ${isPublic ? 'text-red-500' : 'text-rose-500'}`}
					/>
				</div>
			{:else if lastSelectedSide === 'left'}
				<div class="absolute inset-0 flex items-center justify-center z-50 pointer-events-none">
					<div class="w-16 h-16 heart-break flex items-center justify-center">
						<svg viewBox="0 0 24 24" class="w-full h-full drop-shadow-lg">
							<path
								d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
								fill="#94a3b8"
							/>
							<path
								d="M12 5l-2 3 4 3-3 4 3 3-2 3"
								stroke="white"
								stroke-width="2"
								fill="none"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
						</svg>
					</div>
				</div>
			{/if}
		</button>
	</div>

	<div class="mt-4 md:mt-6 flex justify-center w-full">
		<div
			class="flex items-center gap-1 md:gap-2 p-1 bg-zinc-50/50 dark:bg-zinc-900/40 backdrop-blur-sm rounded-full shadow-inner border border-zinc-200/50 dark:border-zinc-800/40 w-fit max-w-full overflow-x-auto scrollbar-hide no-scrollbar"
		>
			<button
				onclick={() => handleSelect(0)}
				disabled={isAnimating}
				class="h-10 md:h-11 px-4 md:px-6 bg-white dark:bg-zinc-800 hover:bg-slate-50 dark:hover:bg-zinc-700 text-slate-900 dark:text-white font-black rounded-full transition-all text-xs md:text-sm cursor-pointer whitespace-nowrap flex items-center gap-1.5 shadow-sm border border-zinc-100 dark:border-zinc-700"
			>
				<Equal size={16} />
				{t('theater.sorter.tie')}
			</button>
			<button
				onclick={undo}
				disabled={!hasHistory || isAnimating}
				class="h-10 md:h-11 px-4 md:px-6 bg-amber-50 dark:bg-amber-950/20 text-amber-600 font-black rounded-full transition-all text-xs md:text-sm cursor-pointer disabled:opacity-30 whitespace-nowrap flex items-center gap-1.5 shadow-sm border border-amber-100/50 dark:border-amber-900/20"
			>
				<RotateCcw size={16} />
				{t('theater.sorter.undo')}
			</button>
			<button
				onclick={restart}
				class={`h-10 md:h-11 px-4 md:px-6 font-black rounded-full transition-all text-xs md:text-sm cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${isPublic ? 'text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20' : 'text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/20'}`}
			>
				<ArrowLeft size={16} />
				{t('theater.sorter.exit')}
			</button>
		</div>
	</div>
</div>

<style>
	:global(.animate-bounce-slow) {
		animation: bounce 3s infinite;
	}

	@keyframes bounce {
		0%,
		100% {
			transform: translateY(-3px);
			animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
		}
		50% {
			transform: translateY(3px);
			animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
		}
	}

	/* Selection Animations */
	.win-animation {
		animation: win 0.45s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
		z-index: 40;
		box-shadow: 0 0 30px rgba(244, 63, 94, 0.4);
	}

	.lose-animation {
		animation: lose 0.45s cubic-bezier(0.36, 0, 0.66, -0.56) forwards;
		opacity: 0.5;
		filter: grayscale(1);
	}

	@keyframes win {
		0% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.08);
		}
		100% {
			transform: scale(1);
		}
	}

	@keyframes lose {
		0% {
			transform: scale(1) translateY(0);
			opacity: 1;
		}
		100% {
			transform: scale(0.8) translateY(40px);
			opacity: 0;
		}
	}

	.vs-pulse {
		animation: vs-pulse 0.45s ease-in-out;
	}

	@keyframes vs-pulse {
		0% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.6) rotate(10deg);
		}
		100% {
			transform: scale(1);
		}
	}

	.heart-float {
		animation: heart-float 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
	}

	@keyframes heart-float {
		0% {
			transform: scale(0) translateY(20px);
			opacity: 0;
		}
		40% {
			transform: scale(1.2) translateY(-20px);
			opacity: 1;
		}
		100% {
			transform: scale(1) translateY(-60px);
			opacity: 0;
		}
	}

	.heart-break {
		animation: heart-break 0.45s ease-in forwards;
	}

	@keyframes heart-break {
		0% {
			transform: scale(1);
			opacity: 1;
		}
		100% {
			transform: scale(0.5);
			opacity: 0;
		}
	}
</style>
