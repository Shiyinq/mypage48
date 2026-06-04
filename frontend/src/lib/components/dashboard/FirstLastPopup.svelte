<script lang="ts">
	import { Calendar, X, Star, Camera } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { fade, scale } from 'svelte/transition';
	import { OptimizedImage } from '$lib/components/common';

	const { t } = useTranslation();

	interface Props {
		show?: boolean;
		onClose: () => void;
		title: string;
		type: 'theater' | 'twoShot';
		first: {
			image?: string | null;
			image_medium?: string | null;
			image_small?: string | null;
			blurHash?: string | null;
			title: string;
			date: string;
			detail?: string;
		} | null;
		last: {
			image?: string | null;
			image_medium?: string | null;
			image_small?: string | null;
			blurHash?: string | null;
			title: string;
			date: string;
			detail?: string;
		} | null;
	}

	let { show = false, onClose, title, type, first, last }: Props = $props();

	let theme = $derived(type === 'theater' ? 'purple' : 'pink');
	let PlaceholderIcon = $derived(type === 'theater' ? Star : Camera);

	let themeClasses = $derived(
		theme === 'purple'
			? {
					bg: 'bg-purple-50 dark:bg-zinc-900',
					border: 'border-purple-100 dark:border-purple-500/20',
					headerBg: 'bg-purple-50/30 dark:bg-transparent',
					iconBg: 'bg-purple-100 dark:bg-purple-800/40',
					text: 'text-purple-500',
					closeBtnBg: 'bg-purple-100 dark:bg-purple-800/40',
					closeBtnHover: 'hover:bg-purple-200 dark:hover:bg-purple-700/50',
					closeBtnIcon: 'text-purple-500 dark:text-purple-400',
					divider: 'bg-purple-200 dark:bg-purple-800/30',
					labelBg: 'bg-purple-100 dark:bg-purple-800/40',
					secondaryBg: 'bg-purple-50 dark:bg-purple-900/20',
					date: 'text-purple-600 dark:text-purple-400',
					placeholderText: 'text-purple-300',
					placeholderEmptyText: 'text-purple-200'
				}
			: {
					bg: 'bg-pink-50 dark:bg-zinc-900',
					border: 'border-pink-100 dark:border-pink-500/20',
					headerBg: 'bg-pink-50/20 dark:bg-transparent',
					iconBg: 'bg-pink-50 dark:bg-pink-800/40',
					text: 'text-pink-400',
					closeBtnBg: 'bg-pink-50 dark:bg-pink-800/40',
					closeBtnHover: 'hover:bg-pink-100 dark:hover:bg-pink-700/50',
					closeBtnIcon: 'text-pink-400 dark:text-pink-400',
					divider: 'bg-pink-200 dark:bg-pink-800/30',
					labelBg: 'bg-pink-50 dark:bg-pink-800/40',
					secondaryBg: 'bg-pink-50 dark:bg-pink-800/40',
					date: 'text-pink-400 dark:text-pink-400',
					placeholderText: 'text-pink-300',
					placeholderEmptyText: 'text-pink-300'
				}
	);

	let labels = $derived(
		type === 'theater'
			? { first: t('dashboard.theater.first'), last: t('dashboard.theater.last') }
			: { first: t('dashboard.twoShot.first'), last: t('dashboard.twoShot.last') }
	);
</script>

{#if show}
	<div
		class="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
		onclick={(e) => {
			if (e.target === e.currentTarget) onClose();
		}}
		onkeydown={(e) => e.key === 'Escape' && onClose()}
		role="dialog"
		aria-modal="true"
		tabindex="-1"
		transition:fade={{ duration: 200 }}
	>
		<div
			class={`w-full max-w-4xl max-h-[95vh] sm:max-h-[90vh] flex flex-col rounded-3xl shadow-2xl overflow-hidden border ${themeClasses.bg} ${themeClasses.border}`}
			transition:scale={{ duration: 200, start: 0.95 }}
		>
			<!-- Header -->
			<div
				class={`p-4 md:p-6 border-b shrink-0 ${themeClasses.border} flex items-center justify-between ${themeClasses.headerBg} gap-2`}
			>
				<div class={`flex items-center gap-2 sm:gap-3 ${themeClasses.text}`}>
					<div class={`p-1.5 sm:p-2 rounded-xl shrink-0 ${themeClasses.iconBg}`}>
						<Calendar class="w-5 h-5 sm:w-6 sm:h-6" />
					</div>
					<h3 class="font-bold text-base sm:text-xl leading-tight text-gray-800 dark:text-gray-100">
						{title}
					</h3>
				</div>
				<button
					onclick={onClose}
					class={`p-2 rounded-full transition-colors cursor-pointer ${themeClasses.closeBtnBg} ${themeClasses.closeBtnHover}`}
				>
					<X class={`w-6 h-6 ${themeClasses.closeBtnIcon}`} />
				</button>
			</div>

			<!-- Content -->
			<div
				class="p-4 sm:p-6 md:p-10 grid grid-cols-2 gap-4 sm:gap-8 md:gap-12 relative overflow-y-auto"
			>
				<div class={`absolute left-1/2 top-8 bottom-8 w-px ${themeClasses.divider}`}></div>

				<!-- First -->
				<div class="flex flex-col items-center text-center">
					<span
						class={`text-[10px] sm:text-xs font-black tracking-[0.1em] sm:tracking-[0.2em] ${themeClasses.text} uppercase mb-3 sm:mb-6 px-2 sm:px-3 py-1 rounded-full ${themeClasses.labelBg}`}
						>{labels.first}</span
					>
					{#if first}
						<div
							class={`w-32 h-44 sm:w-48 sm:h-64 md:w-64 md:h-80 rounded-xl sm:rounded-2xl bg-gray-200 dark:bg-gray-800 shadow-xl mb-3 sm:mb-6 overflow-hidden relative group border ${themeClasses.border}`}
						>
							{#if first.image}
								<OptimizedImage
									src={first.image}
									srcMedium={first.image_medium}
									srcSmall={first.image_small}
									blurHash={first.blurHash}
									alt={first.title}
									class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
									sizes="(max-width: 640px) 128px, (max-width: 768px) 192px, 256px"
								/>
								<div
									class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60"
								></div>
							{:else}
								<div
									class={`w-full h-full flex items-center justify-center ${themeClasses.placeholderText}`}
								>
									<PlaceholderIcon class="w-16 h-16" />
								</div>
							{/if}
						</div>
						<h4 class="text-base sm:text-2xl font-black text-themed mb-1 sm:mb-2 leading-tight">
							{first.title}
						</h4>
						<p class={`text-xs sm:text-lg font-bold mb-1 ${themeClasses.date}`}>
							{first.date}
						</p>
						{#if first.detail}
							<p class="text-[10px] sm:text-sm font-bold text-gray-400">
								{first.detail}
							</p>
						{/if}
					{:else}
						<p class="text-gray-400 italic">No data</p>
					{/if}
				</div>

				<!-- Last -->
				<div class="flex flex-col items-center text-center">
					<span
						class={`text-[10px] sm:text-xs font-black tracking-[0.1em] sm:tracking-[0.2em] ${themeClasses.text} uppercase mb-3 sm:mb-6 px-2 sm:px-3 py-1 rounded-full ${themeClasses.secondaryBg}`}
						>{labels.last}</span
					>
					{#if last}
						<div
							class={`w-32 h-44 sm:w-48 sm:h-64 md:w-64 md:h-80 rounded-xl sm:rounded-2xl bg-gray-200 dark:bg-gray-800 shadow-xl mb-3 sm:mb-6 overflow-hidden relative group border ${themeClasses.border}`}
						>
							{#if last.image}
								<OptimizedImage
									src={last.image}
									srcMedium={last.image_medium}
									srcSmall={last.image_small}
									blurHash={last.blurHash}
									alt={last.title}
									class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
									sizes="(max-width: 640px) 128px, (max-width: 768px) 192px, 256px"
								/>
								<div
									class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60"
								></div>
							{:else}
								<div
									class={`w-full h-full flex items-center justify-center ${themeClasses.placeholderEmptyText}`}
								>
									<PlaceholderIcon class="w-16 h-16" />
								</div>
							{/if}
						</div>
						<h4 class="text-base sm:text-2xl font-black text-themed mb-1 sm:mb-2 leading-tight">
							{last.title}
						</h4>
						<p class={`text-xs sm:text-lg font-bold mb-1 ${themeClasses.date}`}>
							{last.date}
						</p>
						{#if last.detail}
							<p class="text-[10px] sm:text-sm font-bold text-gray-400">
								{last.detail}
							</p>
						{/if}
					{:else}
						<p class="text-gray-400 italic">No data</p>
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if}
