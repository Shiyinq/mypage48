<script lang="ts">
	import type { PCLiveHistory } from '$lib/types/liveHistory';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import { Eye, Lock, Play } from 'lucide-svelte';
	import { onMount, onDestroy } from 'svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import OptimizedImage from '$lib/components/common/OptimizedImage.svelte';

	interface Props {
		item: PCLiveHistory;
		isPublic?: boolean;
	}

	let { item, isPublic = false }: Props = $props();
	let isOwned = $derived(isPublic ? false : item.is_owned);
	const { t, locale } = useTranslation();

	let rotateX = $state(0);
	let rotateY = $state(0);
	let isFlipping = $state(false);
	let isFlipped = $state(false);
	let isFlippingTransition = $state(false);
	let isHovered = $state(false);
	let clickTimeout: ReturnType<typeof setTimeout> | null = null;
	let cardEl = $state<HTMLDivElement | null>(null);

	function handleMouseMove(e: MouseEvent) {
		if (isFlipping || !cardEl) return;
		const rect = cardEl.getBoundingClientRect();
		const x = e.clientX - rect.left;
		const y = e.clientY - rect.top;
		const centerX = rect.width / 2;
		const centerY = rect.height / 2;

		// max rotation 20 deg
		rotateY = ((x - centerX) / centerX) * 20;
		rotateX = -((y - centerY) / centerY) * 20;
	}

	function handleMouseLeave() {
		rotateX = 0;
		rotateY = 0;
		isHovered = false;
	}

	function handleMouseEnter() {
		isHovered = true;
	}

	function handleDeviceOrientation(e: DeviceOrientationEvent) {
		if (isFlipping || !e.beta || !e.gamma) return;

		// beta is front/back tilt [-180, 180]
		// gamma is left/right tilt [-90, 90]

		// Map tilt to rotation (-20 to 20 deg to match mouse effect)
		// Assume normal holding angle is 45 degrees
		let rX = (e.beta - 45) * 0.5;
		let rY = e.gamma * 0.5;

		// Clamp to max 20 degrees
		rotateX = Math.max(-20, Math.min(20, -rX));
		rotateY = Math.max(-20, Math.min(20, rY));

		// Keep the hover effect active on mobile
		if (!isHovered) {
			isHovered = true;
		}
	}

	onMount(() => {
		if (typeof window !== 'undefined' && window.DeviceOrientationEvent) {
			window.addEventListener('deviceorientation', handleDeviceOrientation);
		}
	});

	onDestroy(() => {
		if (typeof window !== 'undefined' && window.DeviceOrientationEvent) {
			window.removeEventListener('deviceorientation', handleDeviceOrientation);
		}
	});

	function handleClick() {
		if (isFlipping || isFlippingTransition) return;

		if (clickTimeout !== null) {
			// Double click
			clearTimeout(clickTimeout);
			clickTimeout = null;
			triggerSpin();
		} else {
			// Wait for double click
			clickTimeout = setTimeout(() => {
				clickTimeout = null;
				// Single click: flip the card
				isFlipped = !isFlipped;
				isFlippingTransition = true;
				rotateX = 0;
				rotateY = 0;
				setTimeout(() => {
					isFlippingTransition = false;
				}, 500); // 500ms duration for flip
			}, 250);
		}
	}

	function triggerSpin() {
		isFlipping = true;
		rotateX = 0;
		rotateY = 0;
		setTimeout(() => {
			isFlipping = false;
		}, 1000);
	}

	let memberImage = $derived(
		item.platform === 'showroom' && item.member?.img
			? item.member.img
			: item.image || item.member?.img
	);

	let memberImageMedium = $derived(
		item.platform === 'showroom' && item.member?.img ? null : item.image_medium
	);

	let memberImageSmall = $derived(
		item.platform === 'showroom' && item.member?.img ? null : item.image_small
	);

	let blurHash = $derived(item.platform === 'showroom' && item.member?.img ? null : item.blurHash);

	let displayDate = $derived.by(() => {
		if (!item.start_at) return '';
		const date = new Date(item.start_at);
		const currentYear = new Date().getFullYear();
		const isCurrentYear = date.getFullYear() === currentYear;
		const options: Intl.DateTimeFormatOptions = {
			month: 'short',
			day: 'numeric',
			...(isCurrentYear ? {} : { year: 'numeric' })
		};
		return date.toLocaleDateString(locale.value === 'id' ? 'id-ID' : 'en-US', options);
	});

	let seed = $derived((item.title || '').length + (item.duration || 0));
	let holographicColor = $derived(`hsl(${seed % 360}, 100%, 70%)`);

	let viewNum = $derived(item.view_num || 0);

	let cardTier = $derived.by(() => {
		if (viewNum >= 100000) return 'ultra-rare';
		if (viewNum >= 50000) return 'rare';
		if (viewNum >= 20000) return 'legendary';
		if (viewNum >= 10000) return 'epic';
		if (viewNum >= 5000) return 'normal';
		return 'common';
	});

	let tierConfig = $derived.by(() => {
		switch (cardTier) {
			case 'ultra-rare':
				return {
					name: t('liveHistory.tier.ultraRare') || 'ULTRA RARE',
					color: 'from-[#fcfb04] to-[#d6d500]',
					text: 'text-black',
					border: 'border-[#fcfb04]',
					shadow: 'shadow-[0_0_20px_rgba(252,251,4,0.8)]'
				};
			case 'rare':
				return {
					name: t('liveHistory.tier.rare') || 'RARE',
					color: 'from-[#fcc404] to-[#dca900]',
					text: 'text-black',
					border: 'border-[#fcc404]',
					shadow: 'shadow-[0_0_15px_rgba(252,196,4,0.7)]'
				};
			case 'legendary':
				return {
					name: t('liveHistory.tier.legendary') || 'LEGENDARY',
					color: 'from-[#fbad3c] to-[#e09825]',
					text: 'text-black',
					border: 'border-[#fbad3c]',
					shadow: 'shadow-[0_0_15px_rgba(251,173,60,0.7)]'
				};
			case 'epic':
				return {
					name: t('liveHistory.tier.epic') || 'EPIC',
					color: 'from-fuchsia-500 to-purple-600',
					text: 'text-white',
					border: 'border-purple-500',
					shadow: 'shadow-[0_0_10px_rgba(168,85,247,0.5)]'
				};
			case 'normal':
				return {
					name: t('liveHistory.tier.normal') || 'NORMAL',
					color: 'from-blue-400 to-cyan-500',
					text: 'text-black',
					border: 'border-blue-500',
					shadow: ''
				};
			default:
				return {
					name: t('liveHistory.tier.common') || 'COMMON',
					color: 'from-zinc-400 to-zinc-500',
					text: 'text-white',
					border: 'border-zinc-700',
					shadow: ''
				};
		}
	});

	let backFaceConfig = $derived.by(() => {
		switch (cardTier) {
			case 'ultra-rare':
				return {
					text: 'text-[#fcfb04]',
					dropShadow: 'drop-shadow-[0_0_8px_rgba(252,251,4,0.8)]',
					bgFrom: 'from-[#fcfb04]/20'
				};
			case 'rare':
				return {
					text: 'text-[#fcc404]',
					dropShadow: 'drop-shadow-[0_0_8px_rgba(252,196,4,0.8)]',
					bgFrom: 'from-[#fcc404]/20'
				};
			case 'legendary':
				return {
					text: 'text-[#fbad3c]',
					dropShadow: 'drop-shadow-[0_0_8px_rgba(251,173,60,0.8)]',
					bgFrom: 'from-[#fbad3c]/20'
				};
			case 'epic':
				return {
					text: 'text-purple-400',
					dropShadow: 'drop-shadow-[0_0_8px_rgba(192,132,252,0.8)]',
					bgFrom: 'from-purple-900'
				};
			case 'normal':
				return {
					text: 'text-blue-400',
					dropShadow: 'drop-shadow-[0_0_8px_rgba(96,165,250,0.8)]',
					bgFrom: 'from-blue-900'
				};
			default:
				return {
					text: 'text-zinc-400',
					dropShadow: 'drop-shadow-[0_0_8px_rgba(161,161,170,0.8)]',
					bgFrom: 'from-zinc-700'
				};
		}
	});

	let foilStyle = $derived.by(() => {
		switch (cardTier) {
			case 'ultra-rare':
				return `linear-gradient(115deg, transparent 20%, #fcfb04 30%, #fff 40%, #fcfb04 50%, transparent 60%)`;
			case 'rare':
				return `linear-gradient(115deg, transparent 20%, #fcc404 30%, #fff 40%, #fcc404 50%, transparent 60%)`;
			case 'legendary':
				return `linear-gradient(115deg, transparent 20%, #fbad3c 30%, #fff 40%, #fbad3c 50%, transparent 60%)`;
			case 'epic':
				return `linear-gradient(115deg, transparent 20%, #ff0844 30%, #ffb199 40%, #ff0844 50%, transparent 60%)`;
			case 'normal':
				return `linear-gradient(115deg, transparent 20%, #00d2ff 30%, #3a7bd5 40%, #00d2ff 50%, transparent 60%)`;
			default:
				return `linear-gradient(115deg, transparent 20%, ${holographicColor} 35%, rgba(255,255,255,0.5) 50%, ${holographicColor} 65%, transparent 80%)`;
		}
	});

	let autoShineStyle = $derived.by(() => {
		switch (cardTier) {
			case 'ultra-rare':
				return `linear-gradient(110deg, transparent 25%, rgba(252,251,4,0.4) 40%, rgba(255,255,255,0.9) 50%, rgba(252,251,4,0.4) 60%, transparent 75%)`;
			case 'rare':
				return `linear-gradient(110deg, transparent 25%, rgba(252,196,4,0.4) 40%, rgba(255,255,255,0.9) 50%, rgba(252,196,4,0.4) 60%, transparent 75%)`;
			case 'legendary':
				return `linear-gradient(110deg, transparent 25%, rgba(251,173,60,0.4) 40%, rgba(255,255,255,0.9) 50%, rgba(251,173,60,0.4) 60%, transparent 75%)`;
			default:
				return `linear-gradient(110deg, transparent 25%, rgba(255,255,255,0.4) 40%, rgba(255,255,255,0.8) 50%, rgba(255,255,255,0.4) 60%, transparent 75%)`;
		}
	});

	let glossOpacity = $derived(cardTier === 'ultra-rare' || cardTier === 'rare' ? 0.9 : 0.7);

	let glareX = $derived(50 + rotateY * 2.5);
	let glareY = $derived(50 - rotateX * 2.5);
</script>

<div
	class="relative group perspective-1000 w-full min-w-0 cursor-pointer"
	role="button"
	tabindex="0"
	onclick={handleClick}
	onkeydown={(e) => {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			handleClick();
		}
	}}
	onmouseenter={handleMouseEnter}
	onmousemove={handleMouseMove}
	onmouseleave={handleMouseLeave}
>
	<!-- Card Container -->
	<div
		bind:this={cardEl}
		class="relative aspect-[3/4] w-full rounded-2xl shadow-2xl {isFlipping
			? isFlipped
				? 'animate-flip-back'
				: 'animate-flip-front'
			: 'transition-transform ease-out group-hover:scale-[1.02]'}"
		style="{isFlipping
			? ''
			: `transform: perspective(1000px) rotateX(${rotateX}deg) rotateY(${isFlipped ? rotateY + 180 : rotateY}deg); transition-duration: ${isFlippingTransition ? '500ms' : '150ms'};`} transform-style: preserve-3d;"
	>
		<!-- Front Face -->
		<div
			class="absolute inset-0 rounded-2xl overflow-hidden bg-zinc-900 border-[3px] {tierConfig.border} {tierConfig.shadow} transition-colors duration-300"
			style="backface-visibility: hidden;"
		>
			{#if !isOwned}
				<div
					class="absolute inset-0 z-20 bg-black/40 backdrop-blur-[1px] rounded-xl sm:rounded-2xl flex flex-col items-center justify-center pointer-events-none"
				>
					<div
						class="bg-black/60 p-2 sm:p-3 rounded-full border border-white/10 mb-1 sm:mb-2 shadow-xl backdrop-blur-md"
					>
						<Lock class="w-4 h-4 sm:w-6 sm:h-6 text-white/60" />
					</div>
					<span
						class="text-[9px] sm:text-xs font-black tracking-widest bg-zinc-900/80 px-2 py-0.5 rounded text-white backdrop-blur-sm"
						>{t('liveHistory.tier.notOwned') || 'NOT OWNED'}</span
					>
				</div>
			{/if}

			<!-- Background Image -->
			<div class="absolute inset-0 {isOwned ? '' : 'grayscale-[0.85] opacity-80'}">
				<OptimizedImage
					src={memberImage ? getExternalMediaUrl(memberImage) : '/images/default-avatar.png'}
					srcMedium={memberImageMedium ? getExternalMediaUrl(memberImageMedium) : null}
					srcSmall={memberImageSmall ? getExternalMediaUrl(memberImageSmall) : null}
					{blurHash}
					alt={item.title || 'Live'}
					sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
					class="w-full h-full object-cover transition-transform duration-500"
					style="transform: scale(1.05);"
				/>
				<!-- Gradient Overlay -->
				<div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-black/10"></div>
			</div>

			<!-- Holographic glare effect (Only if owned) -->
			{#if isOwned}
				<!-- Auto shine for top tiers when not hovered -->
				{#if !isHovered && (cardTier === 'ultra-rare' || cardTier === 'rare' || cardTier === 'legendary')}
					<div
						class="absolute inset-0 pointer-events-none mix-blend-color-dodge rounded-2xl overflow-hidden z-20 animate-auto-shine"
						style="background: {autoShineStyle}; background-size: 200% 100%; background-repeat: no-repeat;"
					></div>
				{/if}

				<!-- Premium Gloss Reflection -->
				<div
					class="absolute inset-0 opacity-0 transition-opacity duration-300 pointer-events-none mix-blend-overlay"
					style="opacity: {isHovered
						? glossOpacity
						: 0}; background: linear-gradient(110deg, transparent 25%, rgba(255,255,255,0.7) 40%, rgba(255,255,255,0.9) 50%, rgba(255,255,255,0.7) 60%, transparent 75%); background-size: 300% 300%; background-position: {glareX}% {glareY}%;"
				></div>

				<!-- Holographic Foil -->
				<div
					class="absolute inset-0 opacity-0 transition-opacity duration-300 pointer-events-none mix-blend-color-dodge"
					style="opacity: {isHovered
						? 0.6
						: 0}; background: {foilStyle}; background-size: 300% 300%; background-position: {glareX}% {glareY}%;"
				></div>
			{/if}

			<!-- Card Content -->
			<div
				class="relative z-10 p-2 sm:p-3 h-full flex flex-col justify-between {isOwned
					? 'text-white'
					: 'text-gray-300'}"
			>
				<!-- Top Bar -->
				<div class="flex justify-between items-start gap-1 w-full">
					<div class="flex items-center shrink-0">
						<div class="sm:hidden flex">
							<PlatformLogo platform={item.platform} size="xs" />
						</div>
						<div class="hidden sm:flex">
							<PlatformLogo platform={item.platform} size="sm" />
						</div>
					</div>

					<div class="flex flex-col items-end gap-1 sm:gap-1.5 min-w-0 shrink">
						<div
							class="flex items-center gap-1 sm:gap-1.5 text-[8px] sm:text-[9px] font-bold bg-black/60 backdrop-blur-md px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-md sm:rounded-lg border border-white/10 shadow-sm text-white whitespace-nowrap shrink-0"
						>
							<span>{displayDate}</span>
							<div class="w-px h-2 sm:h-2.5 bg-white/20"></div>
							<span class="flex items-center gap-0.5">
								{item.view_num?.toLocaleString() || '-'}
								<Eye class="w-2.5 h-2.5 sm:w-3 sm:h-3 text-gray-300" />
							</span>
						</div>
					</div>
				</div>

				<!-- Bottom Info -->
				<div class="flex flex-col items-start gap-1 sm:gap-1.5">
					<!-- Tier Badge -->
					<div
						class="bg-gradient-to-r {tierConfig.color} backdrop-blur-md px-1 sm:px-1.5 py-[1px] sm:py-0.5 rounded border border-white/20 {tierConfig.text} text-[6px] sm:text-[7px] font-black tracking-widest uppercase shadow-sm whitespace-nowrap shrink-0"
					>
						{tierConfig.name}
					</div>

					<div class="flex flex-col w-full">
						<h3
							class="font-black text-sm sm:text-lg lg:text-xl leading-tight mb-0.5 sm:mb-1 line-clamp-2 drop-shadow-lg"
						>
							{item.member?.name || 'Member'}
						</h3>

						<p class="text-[9px] sm:text-xs text-gray-300 line-clamp-2">
							{item.title || 'JKT48 Live'}
						</p>
					</div>
				</div>
			</div>
		</div>

		<!-- Back Face -->
		<div
			class="absolute inset-0 rounded-2xl overflow-hidden shadow-xl bg-zinc-900 border-[3px] {tierConfig.border}"
			style="backface-visibility: hidden; transform: rotateY(180deg);"
		>
			<div
				class="absolute inset-0 bg-gradient-to-br {backFaceConfig.bgFrom} via-zinc-900 to-black"
			></div>
			<div
				class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-30"
			></div>

			<!-- Pattern overlay -->
			<div
				class="absolute inset-0 opacity-10"
				style="background-image: radial-gradient(circle at 2px 2px, white 1px, transparent 0); background-size: 20px 20px;"
			></div>

			<div class="absolute inset-0 flex flex-col items-center justify-center p-2">
				<div
					class="w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-white/10 border border-white/20 flex items-center justify-center mb-2 sm:mb-4 backdrop-blur-sm"
				>
					<Play
						class="w-6 h-6 sm:w-8 sm:h-8 ml-1 sm:ml-1.5 {backFaceConfig.text} {backFaceConfig.dropShadow}"
					/>
				</div>
				<h3 class="font-black text-lg sm:text-2xl tracking-tight text-white mb-0.5 sm:mb-1">
					PC <span class="{backFaceConfig.text} {backFaceConfig.dropShadow}">LIVE</span>
				</h3>
				<p
					class="text-[7px] sm:text-[10px] text-gray-400 font-bold tracking-widest uppercase text-center leading-tight"
				>
					{t('liveHistory.pcLive.description') || 'Photo Card Collection'}
				</p>
			</div>
		</div>
	</div>
</div>

<style>
	@keyframes flip-front {
		0% {
			transform: perspective(1000px) rotateY(0deg);
		}
		100% {
			transform: perspective(1000px) rotateY(360deg);
		}
	}
	@keyframes flip-back {
		0% {
			transform: perspective(1000px) rotateY(180deg);
		}
		100% {
			transform: perspective(1000px) rotateY(540deg);
		}
	}
	.animate-flip-front {
		animation: flip-front 1s ease-in-out;
	}
	.animate-flip-back {
		animation: flip-back 1s ease-in-out;
	}
	@keyframes auto-shine {
		0% {
			background-position: 200% center;
			opacity: 0;
		}
		1% {
			opacity: 1;
		}
		28% {
			background-position: -200% center;
			opacity: 1;
		}
		29% {
			opacity: 0;
		}
		100% {
			background-position: -200% center;
			opacity: 0;
		}
	}
	.animate-auto-shine {
		animation: auto-shine 3.5s linear infinite;
	}
</style>
