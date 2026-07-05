<script lang="ts">
	import { fade, scale, slide } from 'svelte/transition';
	import { giftEvents, type GiftEvent } from '$lib/stores/gift.svelte';
	import { LottieAnimation, RiveAnimation } from '$lib/components/common';

	interface Props {
		roomIdentifier?: string;
	}

	let { roomIdentifier = '' }: Props = $props();

	let activeGift: GiftEvent | null = $state(null);
	let giftTimeout: ReturnType<typeof setTimeout> | undefined;

	function showGift(event: GiftEvent) {
		activeGift = event;
		if (giftTimeout) clearTimeout(giftTimeout);

		// Safety timeout: if asset fails to load within 20s, clear it anyway
		giftTimeout = setTimeout(() => {
			if (activeGift?.timestamp === event.timestamp) {
				activeGift = null;
			}
		}, 20000);
	}

	function startGiftTimer() {
		if (giftTimeout) clearTimeout(giftTimeout);
		giftTimeout = setTimeout(() => {
			activeGift = null;
		}, 10000); // Show for 10 seconds AFTER loading
	}

	function getExternalMediaUrl(url?: string) {
		if (!url) return '';
		if (url.includes('idn.app')) {
			try {
				const u = new URL(url);
				u.searchParams.delete('timestamp');
				return u.toString();
			} catch {
				return url;
			}
		}
		return url;
	}
	$effect(() => {
		if (giftEvents.value && giftEvents.value.roomIdentifier === roomIdentifier) {
			showGift(giftEvents.value);
		}
	});
</script>

{#if activeGift}
	{#key activeGift.timestamp}
		<div
			transition:fade={{ duration: 300 }}
			class="absolute inset-0 z-[5600] pointer-events-none p-4 rounded-2xl overflow-hidden"
		>
			<!-- Official IDN Style Top Toast -->
			<div
				class="absolute top-4 left-1/2 -translate-x-1/2 flex items-center justify-center w-full px-4"
			>
				<div
					transition:slide={{ duration: 400, axis: 'y' }}
					class="flex items-center gap-2.5 px-3.5 py-1.5 backdrop-blur-md rounded-full border border-white/20 shadow-2xl scale-90 sm:scale-100"
					style="background: {activeGift.gift.color
						? `linear-gradient(to right, ${activeGift.gift.color}EE, ${activeGift.gift.color}AA)`
						: 'linear-gradient(to right, #f97316EE, #ef4444AA)'}"
				>
					{#if activeGift.avatar}
						<img
							src={activeGift.avatar}
							alt={activeGift.user}
							referrerpolicy="no-referrer"
							class="w-7 h-7 rounded-full border border-white/40 shadow-sm object-cover"
						/>
					{/if}
					<div class="text-left">
						<p
							class="text-[9px] font-black text-white leading-none whitespace-nowrap drop-shadow-sm"
						>
							{activeGift.user}
						</p>
						<p class="text-[7px] font-bold text-white/90 leading-tight">
							mengirim {activeGift.gift.name}
						</p>
					</div>
				</div>
			</div>

			<div
				transition:scale={{ duration: 600, start: 0.8 }}
				class="absolute inset-0 flex items-center justify-center"
			>
				<!-- Lottie Player or Image for Gift -->
				{#if activeGift.gift.img}
					<div
						class="relative flex items-center justify-center p-8 scale-90 sm:scale-110 md:scale-125"
					>
						{#if activeGift.gift.img.includes('/animation/') || !activeGift.gift.img.match(/\.(png|jpg|jpeg|webp|gif|svg)$/i)}
							{#if activeGift.gift.img.toLowerCase().endsWith('.riv')}
								<RiveAnimation
									src={getExternalMediaUrl(activeGift.gift.img)}
									width="200px"
									height="200px"
									onready={startGiftTimer}
									onerror={() => {
										setTimeout(() => {
											activeGift = null;
										}, 100);
									}}
								/>
							{:else}
								<LottieAnimation
									src={getExternalMediaUrl(activeGift.gift.img)}
									speed={1.2}
									width="200px"
									height="200px"
									onready={startGiftTimer}
									onerror={() => {
										setTimeout(() => {
											activeGift = null;
										}, 100);
									}}
								/>
							{/if}
						{:else}
							<img
								src={getExternalMediaUrl(activeGift.gift.img)}
								alt={activeGift.gift.name}
								referrerpolicy="no-referrer"
								style="width: 150px; height: 150px;"
								class="object-contain drop-shadow-2xl"
								onload={startGiftTimer}
								onerror={() => {
									setTimeout(() => {
										activeGift = null;
									}, 100);
								}}
							/>
						{/if}
						<!-- Glow Effect -->
						<div
							class="absolute inset-0 bg-white/5 blur-[40px] rounded-full animate-pulse z-[-1]"
						></div>
					</div>
				{/if}
			</div>
		</div>
	{/key}
{/if}
