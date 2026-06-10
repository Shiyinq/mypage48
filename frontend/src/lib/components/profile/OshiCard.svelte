<script lang="ts">
	import {
		Dices,
		Cake,
		Plus,
		Heart,
		Info,
		Instagram,
		Smartphone,
		Tv,
		X,
		ChevronLeft,
		ChevronRight
	} from 'lucide-svelte';
	import Button from '$lib/components/Button.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { OptimizedImage } from '$lib/components/common';
	import { getOshiBanner } from '$lib/constants';
	import type { UserOshi, OshiTwoShotCounts } from '$lib/types';

	interface Props {
		oshis?: UserOshi[];
		oshiTwoShotsList?: OshiTwoShotCounts[];
		oshiMeetingsList?: number[];
		loading?: boolean;
		currentIndex?: number;
		onOpenOshiModal: () => void;
		onOpenMemberDetail: (memberName: string) => void;
		onRemoveOshi?: (oshiId: string) => void;
	}

	let {
		oshis = [],
		oshiTwoShotsList = [],
		oshiMeetingsList = [],
		loading = true,
		currentIndex = $bindable(0),
		onOpenOshiModal,
		onOpenMemberDetail,
		onRemoveOshi
	}: Props = $props();

	const { t } = useTranslation();

	let isHovering = $state(false);
	let isDesktop = $state(false);
	let autoRotateInterval: ReturnType<typeof setInterval> | undefined;
	let cardEl: HTMLElement | undefined = $state();
	let mobileHideTimer: ReturnType<typeof setTimeout> | undefined;

	let currentOshi = $derived(oshis[currentIndex] || null);
	let rouletteCount = $derived(oshiTwoShotsList[currentIndex]?.roulette || 0);
	let birthdayCount = $derived(oshiTwoShotsList[currentIndex]?.birthday || 0);
	let oshiMeetings = $derived(oshiMeetingsList[currentIndex] || 0);

	function startAutoRotate() {
		stopAutoRotate();
		if (oshis.length > 1) {
			autoRotateInterval = setInterval(() => {
				currentIndex = (currentIndex + 1) % oshis.length;
			}, 3000);
		}
	}

	function stopAutoRotate() {
		if (autoRotateInterval) {
			clearInterval(autoRotateInterval);
			autoRotateInterval = undefined;
		}
	}

	function goNext() {
		if (oshis.length > 1) {
			currentIndex = (currentIndex + 1) % oshis.length;
			resetAutoRotate();
		}
	}

	function goPrev() {
		if (oshis.length > 1) {
			currentIndex = (currentIndex - 1 + oshis.length) % oshis.length;
			resetAutoRotate();
		}
	}

	function resetAutoRotate() {
		stopAutoRotate();
		startAutoRotate();
	}

	function clearMobileTimer() {
		if (mobileHideTimer) {
			clearTimeout(mobileHideTimer);
			mobileHideTimer = undefined;
		}
	}

	function handleCardPointerDown() {
		if (isDesktop) return;
		clearMobileTimer();
		isHovering = true;
		stopAutoRotate();
		mobileHideTimer = setTimeout(() => {
			isHovering = false;
			startAutoRotate();
		}, 3000);
	}

	function handleOutsideClick(e: Event) {
		if (isDesktop) return;
		if (cardEl && !cardEl.contains(e.target as Node)) {
			clearMobileTimer();
			isHovering = false;
			startAutoRotate();
		}
	}

	$effect(() => {
		if (typeof window !== 'undefined') {
			const mql = window.matchMedia('(min-width: 768px)');
			isDesktop = mql.matches;
			const handler = (e: MediaQueryListEvent) => {
				isDesktop = e.matches;
			};
			mql.addEventListener('change', handler);
			document.addEventListener('mousedown', handleOutsideClick);
			return () => {
				mql.removeEventListener('change', handler);
				document.removeEventListener('mousedown', handleOutsideClick);
				clearMobileTimer();
			};
		}
	});

	$effect(() => {
		startAutoRotate();
		return () => stopAutoRotate();
	});

	$effect(() => {
		if (oshis.length <= 1) {
			stopAutoRotate();
		}
	});
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
	bind:this={cardEl}
	class="glass-panel p-0 rounded-3xl relative"
	onmouseenter={() => {
		isHovering = true;
		stopAutoRotate();
	}}
	onmouseleave={() => {
		isHovering = false;
		startAutoRotate();
	}}
	onmousedown={handleCardPointerDown}
	role="region"
	aria-label="Oshi card"
>
	<!-- Banner -->
	<div
		class="h-32 w-full rounded-t-3xl overflow-hidden bg-cover bg-[center_30%] relative transition-all duration-500 ease-in-out"
		style="background-image: url('{currentOshi ? getOshiBanner(currentOshi.memberType) : ''}')"
	>
		<div
			class="absolute inset-0 bg-gradient-to-t from-white via-white/50 to-transparent dark:from-zinc-900 dark:via-zinc-900/50"
		></div>
	</div>

	<div class="px-6 md:px-8 pb-6 relative">
		{#if loading}
			<!-- Oshi Skeleton Loading -->
			<div class="flex flex-col md:flex-row items-center gap-6 -mt-16">
				<div
					class="w-28 h-28 rounded-full bg-gray-200 dark:bg-zinc-700 border-4 border-white dark:border-zinc-900 shadow-xl animate-pulse relative z-10 md:self-start"
				></div>
				<div class="text-center md:text-left flex-1 w-full max-w-sm">
					<div class="flex flex-col md:flex-row items-center gap-2 mb-2">
						<div class="h-8 w-48 bg-gray-200 dark:bg-zinc-700 rounded-lg animate-pulse"></div>
						<div class="h-5 w-24 bg-gray-200 dark:bg-zinc-700 rounded-md animate-pulse"></div>
					</div>
					<div class="h-16 w-full bg-gray-100 dark:bg-zinc-800 rounded-xl animate-pulse mt-2"></div>
					<div class="flex gap-2 mt-3 justify-center md:justify-start">
						<div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
						<div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
						<div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
					</div>
				</div>
			</div>
		{:else if currentOshi}
			<div class="flex flex-col md:flex-row items-center gap-6 -mt-16">
				<!-- Avatar with Glow -->
				<div class="relative md:self-start">
					<button
						class="relative w-28 h-28 rounded-full border-4 border-white shadow-xl overflow-hidden flex-shrink-0 cursor-pointer transition-transform hover:scale-105 active:scale-95"
						onclick={() => onOpenMemberDetail(currentOshi.name)}
					>
						<OptimizedImage
							src={getExternalMediaUrl(currentOshi.profilePicture) || '/placeholder-user.jpg'}
							srcMedium={currentOshi.profilePicture_medium}
							srcSmall={currentOshi.profilePicture_small}
							alt={currentOshi.name}
							blurHash={currentOshi.blurHash}
							class="w-full h-full object-cover"
							sizes="112px"
						/>
						<div
							class="absolute inset-0 bg-black/0 hover:bg-black/10 transition-colors flex items-center justify-center opacity-0 hover:opacity-100"
						>
							<Info class="w-8 h-8 text-white drop-shadow-md" />
						</div>
					</button>
					<div
						class="absolute -bottom-3 left-1/2 transform -translate-x-1/2 z-20 pointer-events-none"
					>
						<div
							class="bg-pink-500 text-white pl-2 pr-3 py-1 rounded-full text-[10px] font-bold shadow-lg flex items-center gap-1 whitespace-nowrap border-2 border-white dark:border-gray-800"
						>
							<Heart class="w-3 h-3 fill-current animate-pulse" />
							<span>My Oshi</span>
						</div>
					</div>
					<!-- Remove Oshi Button -->
					{#if onRemoveOshi}
						<button
							onclick={() => onRemoveOshi(currentOshi.id)}
							class="absolute -top-2 -right-2 z-30 w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center shadow-lg transition-all duration-200 cursor-pointer {!isHovering
								? 'opacity-0'
								: 'opacity-100'}"
							title={t('profile.oshi.removeOshi')}
						>
							<X class="w-3 h-3" />
						</button>
					{/if}
				</div>

				<!-- Info -->
				<div class="text-center md:text-left flex-1 min-w-0">
					<div class="flex flex-col items-center md:items-start gap-1 mb-2">
						<div class="flex items-center gap-2">
							<h3
								class="text-2xl font-black text-gray-800 dark:text-gray-100 leading-tight drop-shadow-md dark:drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]"
							>
								{currentOshi.name}
							</h3>
						</div>
						<div class="flex items-center gap-2">
							<span
								class="px-2 py-0.5 bg-red-100 text-red-600 text-[10px] font-bold rounded-md uppercase tracking-wide border border-red-200 whitespace-nowrap"
							>
								{t('profile.oshi.generationPattern', { gen: currentOshi.generation })}
							</span>
							<button
								type="button"
								class="group relative px-2 py-0.5 bg-blue-100 text-blue-600 rounded-md border border-blue-200 cursor-help flex items-center gap-1 focus:outline-none"
							>
								<span class="text-[10px] font-bold uppercase tracking-wide whitespace-nowrap">
									{t('profile.oshi.totalShowsPattern', { count: currentOshi.totalShows || 0 })}
								</span>
								<Info class="w-3 h-3" />
								<div
									class="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-48 p-2 bg-gray-800 text-white text-[10px] rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible group-focus:opacity-100 group-focus:visible transition-all z-50 text-center pointer-events-none"
								>
									{t('profile.oshi.showsTooltip')}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-gray-800"
									></div>
								</div>
							</button>
						</div>
					</div>

					<!-- Catchphrase Bubble -->
					<div
						class="relative bg-gray-50 dark:bg-zinc-900 p-3 rounded-xl rounded-tl-none border border-gray-100 dark:border-zinc-800 shadow-sm mt-2 inline-block"
					>
						<p class="text-xs text-gray-600 dark:text-gray-400 italic font-medium">
							"{currentOshi.catchphrase}"
						</p>
					</div>

					<!-- Socials -->
					{#if currentOshi.socials}
						<div class="flex flex-wrap justify-center md:justify-start gap-2 mt-3">
							{#if currentOshi.socials.twitter}
								<a
									href={currentOshi.socials.twitter}
									target="_blank"
									rel="noopener noreferrer"
									class="p-1.5 bg-gray-100 dark:bg-white/5 rounded-full text-gray-500 dark:text-gray-300 hover:bg-black hover:text-white transition-colors cursor-pointer"
									title="Twitter / X"
								>
									<svg
										class="w-3.5 h-3.5"
										viewBox="0 0 24 24"
										fill="currentColor"
										xmlns="http://www.w3.org/2000/svg"
									>
										<path
											d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
										/>
									</svg>
								</a>
							{/if}
							{#if currentOshi.socials.instagram}
								<a
									href={currentOshi.socials.instagram}
									target="_blank"
									rel="noopener noreferrer"
									class="p-1.5 bg-gray-100 dark:bg-white/5 rounded-full text-gray-500 dark:text-gray-300 hover:bg-pink-100 dark:hover:bg-pink-900/30 hover:text-pink-600 transition-colors cursor-pointer"
									title="Instagram"
								>
									<Instagram class="w-3.5 h-3.5" />
								</a>
							{/if}
							{#if currentOshi.socials.tiktok}
								<a
									href={currentOshi.socials.tiktok}
									target="_blank"
									rel="noopener noreferrer"
									class="p-1.5 bg-gray-100 dark:bg-white/5 rounded-full text-gray-500 dark:text-gray-300 hover:bg-black hover:text-white transition-colors cursor-pointer"
									title="TikTok"
								>
									<svg
										class="w-3.5 h-3.5"
										viewBox="0 0 24 24"
										fill="currentColor"
										xmlns="http://www.w3.org/2000/svg"
									>
										<path
											d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"
										/>
									</svg>
								</a>
							{/if}
							{#if currentOshi.socials.idn_app}
								<a
									href={currentOshi.socials.idn_app}
									target="_blank"
									rel="noopener noreferrer"
									class="p-1.5 bg-gray-100 dark:bg-white/5 rounded-full text-gray-500 dark:text-gray-300 hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 transition-colors cursor-pointer"
									title="IDN App"
								>
									<Smartphone class="w-3.5 h-3.5" />
								</a>
							{/if}
							{#if currentOshi.socials.showroom}
								<a
									href={currentOshi.socials.showroom}
									target="_blank"
									rel="noopener noreferrer"
									class="p-1.5 bg-gray-100 dark:bg-white/5 rounded-full text-gray-500 dark:text-gray-300 hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:text-blue-600 transition-colors cursor-pointer"
									title="Showroom"
								>
									<Tv class="w-3.5 h-3.5" />
								</a>
							{/if}
						</div>
					{/if}
				</div>
			</div>

			<!-- Stats Grid -->
			<div class="mt-6 grid grid-cols-3 gap-2 md:gap-3 border-t border-gray-100 pt-4">
				<div
					class="flex flex-col md:flex-row items-center justify-center md:justify-start gap-1 md:gap-3 p-2 rounded-xl hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors"
				>
					<div
						class="p-2 rounded-full bg-red-50 dark:bg-red-900/20 shadow-sm text-red-600 dark:text-red-400"
					>
						<Heart class="w-4 h-4" />
					</div>
					<div class="text-center md:text-left">
						<p class="text-lg font-black text-gray-800 dark:text-gray-200 leading-none">
							{oshiMeetings}
						</p>
						<p class="text-[10px] font-bold text-gray-400 uppercase">
							{t('profile.stats.oshiMeetings')}
						</p>
					</div>
				</div>
				<div
					class="flex flex-col md:flex-row items-center justify-center md:justify-start gap-1 md:gap-3 p-2 rounded-xl hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors"
				>
					<div
						class="p-2 rounded-full bg-yellow-50 dark:bg-yellow-900/20 shadow-sm text-yellow-600 dark:text-yellow-400"
					>
						<Dices class="w-4 h-4" />
					</div>
					<div class="text-center md:text-left">
						<p class="text-lg font-black text-gray-800 dark:text-gray-200 leading-none">
							{rouletteCount}
						</p>
						<p class="text-[10px] font-bold text-gray-400 uppercase">
							{t('profile.oshi.roulette')}
						</p>
					</div>
				</div>
				<div
					class="flex flex-col md:flex-row items-center justify-center md:justify-start gap-1 md:gap-3 p-2 rounded-xl hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors"
				>
					<div
						class="p-2 rounded-full bg-pink-50 dark:bg-pink-900/20 shadow-sm text-pink-600 dark:text-pink-400"
					>
						<Cake class="w-4 h-4" />
					</div>
					<div class="text-center md:text-left">
						<p class="text-lg font-black text-gray-800 dark:text-gray-200 leading-none">
							{birthdayCount}
						</p>
						<p class="text-[10px] font-bold text-gray-400 uppercase">
							{t('profile.oshi.birthday')}
						</p>
					</div>
				</div>
			</div>
		{:else}
			<!-- Empty State: Select Oshi -->
			<div class="flex flex-col items-center justify-center text-center py-8 -mt-12">
				<div class="relative mb-4 group cursor-pointer">
					<button
						onclick={onOpenOshiModal}
						class="w-24 h-24 rounded-full bg-white dark:bg-zinc-800 shadow-lg flex items-center justify-center border-4 border-dashed border-gray-200 dark:border-zinc-700 group-hover:border-red-300 transition-colors cursor-pointer"
					>
						<Plus class="w-8 h-8 text-gray-300 group-hover:text-red-400" />
					</button>
					<div
						class="absolute -bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 bg-red-500 text-white text-xs font-bold rounded-full shadow-lg transform scale-90 group-hover:scale-100 transition-transform pointer-events-none"
					>
						{t('profile.oshi.selectBadge')}
					</div>
				</div>
				<h3 class="text-lg font-bold text-gray-700 dark:text-gray-300">
					{t('profile.oshi.emptyTitle')}
				</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400 max-w-xs mx-auto mt-1">
					{t('profile.oshi.emptyDescription')}
				</p>
				<div class="mt-4">
					<Button size="sm" variant="outline" onclick={onOpenOshiModal}
						>{t('profile.oshi.browseButton')}</Button
					>
				</div>
			</div>
		{/if}
	</div>

	<!-- Oshi Counter / Indicator -->
	{#if oshis.length > 0}
		<div
			class="absolute top-3 left-3 z-10 bg-black/50 backdrop-blur-sm text-white text-[10px] font-bold px-2.5 py-1 rounded-full flex items-center gap-1.5"
		>
			<span>{currentIndex + 1}/{oshis.length}</span>
			<span class="opacity-70">Oshi</span>
		</div>
	{/if}

	<!-- Add Oshi Button (when < 5 and not empty) -->
	{#if oshis.length > 0 && oshis.length < 5}
		<button
			onclick={onOpenOshiModal}
			class="absolute top-3 right-3 z-10 bg-white/80 dark:bg-zinc-800/80 hover:bg-white dark:hover:bg-zinc-800 text-red-500 hover:text-red-600 backdrop-blur-sm rounded-full p-1.5 shadow-lg transition-all duration-200 cursor-pointer {!isHovering
				? 'opacity-0'
				: 'opacity-100'}"
			title={t('profile.oshi.addOshi')}
		>
			<Plus class="w-4 h-4" />
		</button>
	{/if}

	<!-- Prev/Next Buttons -->
	{#if oshis.length > 1}
		<button
			onclick={goPrev}
			class="absolute left-2 top-[140px] -translate-y-1/2 z-10 bg-black/30 hover:bg-black/50 text-white rounded-full p-1.5 transition-all duration-200 cursor-pointer {!isHovering
				? 'opacity-0'
				: 'opacity-100'}"
			aria-label="Previous oshi"
		>
			<ChevronLeft class="w-5 h-5" />
		</button>
		<button
			onclick={goNext}
			class="absolute right-2 top-[140px] -translate-y-1/2 z-10 bg-black/30 hover:bg-black/50 text-white rounded-full p-1.5 transition-all duration-200 cursor-pointer {!isHovering
				? 'opacity-0'
				: 'opacity-100'}"
			aria-label="Next oshi"
		>
			<ChevronRight class="w-5 h-5" />
		</button>
	{/if}
</div>
