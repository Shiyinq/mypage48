<script lang="ts">
	import { Crown, QrCode } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { User } from '$lib/types';
	import { getTeamColors } from '$lib/constants';
	import { page } from '$app/stores';
	import QRCode from 'qrcode';
	import { fade } from 'svelte/transition';

	interface Props {
		profile?: User | null;
		loading?: boolean;
		activeOshiMemberType?: string;
	}

	let { profile = null, loading = true, activeOshiMemberType = undefined }: Props = $props();

	const { t } = useTranslation();

	let teamColors = $derived(getTeamColors(activeOshiMemberType ?? profile?.oshis?.[0]?.memberType));

	let qrCodeUrl = $state<string | null>(null);
	let isQrExpanded = $state(false);

	let rotateX = $state(0);
	let rotateY = $state(0);
	let isFlipping = $state(false);
	let clickTimeout: ReturnType<typeof setTimeout> | null = null;
	let cardEl = $state<HTMLDivElement | null>(null);

	function closeQr() {
		isQrExpanded = false;
	}

	function handleMouseMove(e: MouseEvent) {
		if (isFlipping || isQrExpanded || !cardEl) return;
		const rect = cardEl.getBoundingClientRect();
		const x = e.clientX - rect.left;
		const y = e.clientY - rect.top;
		const centerX = rect.width / 2;
		const centerY = rect.height / 2;

		// max rotation 15 deg
		rotateY = ((x - centerX) / centerX) * 15;
		rotateX = -((y - centerY) / centerY) * 15;
	}

	function handleMouseLeave() {
		rotateX = 0;
		rotateY = 0;
	}

	function handleClick() {
		if (clickTimeout) {
			clearTimeout(clickTimeout);
			clickTimeout = null;
			triggerFlip();
		} else {
			clickTimeout = setTimeout(() => {
				isQrExpanded = true;
				clickTimeout = null;
			}, 250);
		}
	}

	function triggerFlip() {
		if (isFlipping) return;
		isFlipping = true;
		rotateX = 0;
		rotateY = 0;
		setTimeout(() => {
			isFlipping = false;
		}, 1000);
	}

	let isModalFlipping = $state(false);
	let modalClickTimeout: ReturnType<typeof setTimeout> | null = null;

	function handleModalClick(e: Event) {
		e.stopPropagation();
		if (modalClickTimeout) {
			clearTimeout(modalClickTimeout);
			modalClickTimeout = null;
			if (isModalFlipping) return;
			isModalFlipping = true;
			setTimeout(() => {
				isModalFlipping = false;
			}, 1000);
		} else {
			modalClickTimeout = setTimeout(() => {
				modalClickTimeout = null;
			}, 250);
		}
	}

	function portal(node: HTMLElement) {
		document.body.appendChild(node);
		return {
			destroy() {
				if (node.parentNode) {
					node.parentNode.removeChild(node);
				}
			}
		};
	}

	$effect(() => {
		if (profile?.username && $page?.url?.origin) {
			const profileUrl = `${$page.url.origin}/u/${profile.username}`;
			QRCode.toDataURL(profileUrl, {
				margin: 1,
				color: {
					dark: '#000000',
					light: '#ffffff'
				}
			})
				.then((url) => {
					qrCodeUrl = url;
				})
				.catch((err) => {
					console.error('Failed to generate QR code:', err);
				});
		}
	});
</script>

<svelte:window
	onkeydown={(e) => {
		if (isQrExpanded && e.key === 'Escape') closeQr();
	}}
/>

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
	onmousemove={handleMouseMove}
	onmouseleave={handleMouseLeave}
>
	<!-- Card Container -->
	<div
		bind:this={cardEl}
		class="relative h-56 w-full rounded-3xl shadow-2xl max-w-full {isFlipping
			? 'animate-flip'
			: 'transition-transform duration-200 ease-out group-hover:scale-[1.02]'} {profile?.ofcStatus ===
		'Active'
			? 'ring-2 ring-[var(--team-ring)]/50 ring-offset-2 ring-offset-white'
			: ''}"
		style="--team-ring: {teamColors.ring}; --team-glow: {teamColors.glow}; --team-badge-bg: {teamColors.badgeBg}; --team-badge-border: {teamColors.badgeBorder}; --team-badge-dot: {teamColors.badgeDot}; --team-badge-text: {teamColors.badgeText}; {isFlipping
			? ''
			: `transform: perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg);`} transform-style: preserve-3d;"
	>
		<div class="absolute inset-0 rounded-3xl overflow-hidden" style="backface-visibility: hidden;">
			<!-- Background -->
			<div class="absolute inset-0 bg-gradient-to-br from-gray-900 via-red-900 to-black"></div>
			<div
				class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20"
			></div>

			<!-- Holographic Overlay -->
			<div
				class="absolute inset-0 bg-gradient-to-tr from-white/10 via-transparent to-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"
			></div>

			<!-- Active OFC Glow Effect -->
			{#if profile?.ofcStatus === 'Active'}
				<div
					class="absolute -top-2 -right-2 w-20 h-20 rounded-full blur-2xl opacity-30 animate-pulse"
					style="background-color: {teamColors.glow}"
				></div>
			{/if}

			<!-- Red Accent Curves -->
			<div
				class="absolute -top-10 -right-10 w-40 h-40 bg-red-600 rounded-full blur-3xl opacity-50"
			></div>
			<div
				class="absolute -bottom-10 -left-10 w-40 h-40 bg-red-600 rounded-full blur-3xl opacity-30"
			></div>

			<!-- Card Content -->
			<div
				class="relative z-10 p-4 sm:p-6 h-full flex flex-col justify-between text-white overflow-hidden"
			>
				<!-- Top Row -->
				<div class="flex justify-between items-start gap-2 min-w-0">
					<div class="flex items-center gap-1.5 sm:gap-2 min-w-0 flex-shrink">
						<div
							class="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center flex-shrink-0"
						>
							<Crown class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-yellow-400" />
						</div>
						<div class="min-w-0">
							<p
								class="text-[10px] sm:text-[11px] font-bold text-red-400 tracking-widest uppercase truncate"
							>
								{t('profile.memberCard.officialFanClub')}
							</p>
							<h3 class="font-black text-base sm:text-lg tracking-tight truncate">
								MYPAGE<span class="text-red-500">48</span>
							</h3>
						</div>
					</div>
					<div class="flex flex-col items-end gap-1 min-w-0">
						<!-- Member ID -->
						<div class="text-right min-w-0 w-full">
							<p class="text-[10px] sm:text-[11px] text-gray-400 font-bold truncate">
								{t('profile.memberCard.memberId')}
							</p>
							<p class="font-mono font-bold text-shadow text-xs sm:text-base truncate">
								{#if loading}
									<span
										class="inline-block w-16 sm:w-20 h-3.5 sm:h-4 bg-white/20 rounded animate-pulse"
									></span>
								{:else}
									{profile?.memberId || 'N/A'}
								{/if}
							</p>
						</div>
						<!-- OFC Status Badge -->
						{#if loading}
							<div
								class="h-4 sm:h-5 w-12 sm:w-16 bg-white/20 rounded-full animate-pulse mt-1"
							></div>
						{:else}
							<div
								class="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-full backdrop-blur-md mt-1 {profile?.ofcStatus ===
								'Active'
									? 'bg-[var(--team-badge-bg)]/20 border border-[var(--team-badge-border)]/30'
									: 'bg-white/10 border border-white/20'} flex-shrink"
							>
								<span
									class="w-1 h-1 sm:w-1.5 sm:h-1.5 rounded-full flex-shrink-0 {profile?.ofcStatus ===
									'Active'
										? 'bg-[var(--team-badge-dot)] animate-pulse'
										: 'bg-gray-400'}"
									style={profile?.ofcStatus === 'Active'
										? `box-shadow: 0 0 6px ${teamColors.badgeDot}`
										: ''}
								></span>
								<span
									class="text-[10px] sm:text-[11px] font-bold uppercase tracking-wider {profile?.ofcStatus ===
									'Active'
										? 'text-[var(--team-badge-text)]'
										: 'text-gray-400'} truncate"
								>
									{profile?.ofcStatus === 'Active'
										? t('profile.memberCard.ofcActive')
										: t('profile.memberCard.ofcInactive')}
								</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Chip & Wave -->
				<div class="flex items-center gap-3 sm:gap-4 my-1 sm:my-2 opacity-80 min-w-0">
					<div
						class="w-8 h-6 sm:w-10 sm:h-8 rounded-md bg-gradient-to-br from-yellow-200 to-yellow-600 border border-yellow-600 shadow-inner flex items-center justify-center flex-shrink-0"
					>
						<div class="w-4 h-3 sm:w-6 sm:h-4 border border-yellow-800/30 rounded-sm"></div>
					</div>
					<!-- WifiIcon -->
					<svg
						viewBox="0 0 24 24"
						fill="currentColor"
						class="w-5 h-5 sm:w-6 sm:h-6 rotate-90 text-gray-500 flex-shrink-0"
					>
						<path
							d="M12 19.5C12 19.5 12 19.5 12 19.5C13.3807 19.5 14.5 18.3807 14.5 17C14.5 15.6193 13.3807 14.5 12 14.5C10.6193 14.5 9.5 15.6193 9.5 17C9.5 18.3807 10.6193 19.5 12 19.5Z"
						/>
						<path
							fill-rule="evenodd"
							clip-rule="evenodd"
							d="M12 3C6.477 3 1.643 6.374 0.192 11.19L1.9 12.63C3.03 8.77 6.93 6 12 6C17.07 6 20.97 8.77 22.1 12.63L23.808 11.19C22.357 6.374 17.523 3 12 3ZM12 7C8.27 7 5.11 8.84 3.9 11.85L5.65 13.11C6.45 11.12 8.65 10 12 10C15.35 10 17.55 11.12 18.35 13.11L20.1 11.85C18.89 8.84 15.73 7 12 7Z"
							opacity="0.5"
						/>
					</svg>
				</div>

				<!-- Bottom Row -->
				<div class="flex justify-between items-end gap-2 min-w-0">
					<div class="min-w-0">
						<p class="text-[10px] sm:text-[11px] text-gray-400 font-bold uppercase mb-0.5 truncate">
							{t('profile.memberCard.cardHolder')}
						</p>
						<p
							class="text-base sm:text-lg font-bold tracking-wide uppercase text-shadow-sm truncate"
						>
							{#if loading}
								<span class="inline-block w-32 sm:w-40 h-4 sm:h-5 bg-white/20 rounded animate-pulse"
								></span>
							{:else}
								{profile?.name || 'N/A'}
							{/if}
						</p>
					</div>
					<div
						class="bg-white p-1 rounded-lg flex-shrink-0 group-hover:scale-105 transition-transform"
					>
						{#if qrCodeUrl}
							<img
								src={qrCodeUrl}
								alt="Profile QR Code"
								class="w-6 h-6 sm:w-8 sm:h-8 object-contain"
							/>
						{:else}
							<QrCode class="w-6 h-6 sm:w-8 sm:h-8 text-black" />
						{/if}
					</div>
				</div>
			</div>
		</div>

		<!-- Back Face -->
		<div
			class="absolute inset-0 rounded-3xl overflow-hidden shadow-xl"
			style="backface-visibility: hidden; transform: rotateY(180deg);"
		>
			<div class="absolute inset-0 bg-gradient-to-br from-gray-900 via-red-900 to-black"></div>
			<div
				class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20"
			></div>

			<div class="absolute inset-0 flex flex-col items-center justify-center opacity-30">
				<Crown class="w-16 h-16 text-yellow-400 mb-2" />
				<h3 class="font-black text-2xl tracking-tight text-white">
					MYPAGE<span class="text-red-500">48</span>
				</h3>
			</div>
		</div>
	</div>
</div>

<!-- QR Code Expanded Modal -->
{#if isQrExpanded}
	<div
		use:portal
		class="fixed inset-0 z-[100] flex flex-col items-center justify-center p-4 gap-8"
		transition:fade={{ duration: 200 }}
	>
		<button
			class="absolute inset-0 w-full h-full bg-black/60 backdrop-blur-sm border-none cursor-default"
			onclick={closeQr}
			aria-label="Close modal"
		></button>

		<!-- Modal Content - looks like a fanclub card -->
		<div
			class="relative w-full max-w-sm rounded-3xl shadow-2xl select-none {isModalFlipping
				? 'animate-flip'
				: 'transition-transform duration-200'} {profile?.ofcStatus === 'Active'
				? 'ring-2 ring-[var(--team-ring)]/50 ring-offset-4 ring-offset-black/50'
				: ''}"
			style="--team-ring: {teamColors.ring}; --team-glow: {teamColors.glow}; transform-style: preserve-3d; perspective: 1000px;"
			onclick={handleModalClick}
			onkeydown={(e) => {
				if (e.key === 'Enter' || e.key === ' ') {
					e.preventDefault();
					handleModalClick(e);
				}
			}}
			role="button"
			tabindex="0"
			aria-label="Rotate QR Card"
		>
			<!-- Front Face -->
			<div class="relative w-full rounded-3xl overflow-hidden" style="backface-visibility: hidden;">
				<!-- Background -->
				<div class="absolute inset-0 bg-gradient-to-br from-gray-900 via-red-900 to-black"></div>
				<div
					class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20"
				></div>

				<!-- Active OFC Glow Effect -->
				{#if profile?.ofcStatus === 'Active'}
					<div
						class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 rounded-full blur-3xl opacity-30 animate-pulse"
						style="background-color: {teamColors.glow}"
					></div>
				{/if}

				<!-- Content -->
				<div
					class="relative z-10 p-8 flex flex-col items-center justify-center text-white min-h-[400px]"
				>
					<div class="flex items-center gap-2 mb-6">
						<Crown class="w-6 h-6 text-yellow-400" />
						<h3 class="font-black text-xl tracking-tight">
							MYPAGE<span class="text-red-500">48</span>
						</h3>
					</div>

					<div class="bg-white p-4 rounded-2xl shadow-xl mb-6">
						{#if qrCodeUrl}
							<img
								src={qrCodeUrl}
								alt="Profile QR Code"
								class="w-48 h-48 object-contain pointer-events-none select-none"
							/>
						{:else}
							<QrCode class="w-48 h-48 text-black pointer-events-none select-none" />
						{/if}
					</div>

					<div class="text-center">
						<p class="text-xs text-gray-400 font-bold uppercase mb-1">
							{t('profile.memberCard.memberId')}
						</p>
						<p class="font-mono font-bold text-lg mb-2 text-shadow">{profile?.memberId || 'N/A'}</p>
						<p class="text-sm font-bold tracking-wide uppercase text-shadow-sm">
							{profile?.name || 'N/A'}
						</p>
					</div>
				</div>
			</div>

			<!-- Back Face -->
			<div
				class="absolute inset-0 rounded-3xl overflow-hidden shadow-xl"
				style="backface-visibility: hidden; transform: rotateY(180deg);"
			>
				<div class="absolute inset-0 bg-gradient-to-br from-gray-900 via-red-900 to-black"></div>
				<div
					class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20"
				></div>

				<div class="absolute inset-0 flex flex-col items-center justify-center opacity-30">
					<Crown class="w-16 h-16 text-yellow-400 mb-2" />
					<h3 class="font-black text-2xl tracking-tight text-white">
						MYPAGE<span class="text-red-500">48</span>
					</h3>
				</div>
			</div>
		</div>

		<!-- Close Button Below Card -->
		<button
			onclick={(e) => {
				e.stopPropagation();
				closeQr();
			}}
			class="p-4 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-full transition-all cursor-pointer text-white shadow-xl hover:scale-110 active:scale-95"
			aria-label="Close"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="w-6 h-6"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2.5"
				stroke-linecap="round"
				stroke-linejoin="round"
				><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg
			>
		</button>
	</div>
{/if}

<style>
	@keyframes flip {
		0% {
			transform: perspective(1000px) rotateY(0deg);
		}
		100% {
			transform: perspective(1000px) rotateY(360deg);
		}
	}
	.animate-flip {
		animation: flip 1s ease-in-out;
	}
</style>
