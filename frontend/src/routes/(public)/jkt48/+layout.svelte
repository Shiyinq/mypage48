<script lang="ts">
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { spring } from 'svelte/motion';
	import LandingNavbar from '$lib/components/landing-page/LandingNavbar.svelte';
	import Footer from '$lib/components/landing-page/Footer.svelte';
	import { Sparkles, Star } from 'lucide-svelte';
	import { page } from '$app/stores';

	let scrollY = 0;
	let mouse = spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 });

	$: isFullScreenRoute = $page.url.pathname.includes('/live/multiview');

	function handleMouseMove(event: MouseEvent) {
		const { clientX, clientY } = event;
		const { innerWidth, innerHeight } = window;
		const x = clientX / innerWidth - 0.5;
		const y = clientY / innerHeight - 0.5;
		mouse.set({ x, y });
	}

	let decorations: Array<{
		x: number;
		y: number;
		scale: number;
		delay: number;
		duration: number;
		depth: number;
		type: 'star' | 'sparkle';
	}> = [];

	onMount(() => {
		decorations = Array.from({ length: 20 }, () => ({
			x: Math.random() * 100,
			y: Math.random() * 100,
			scale: 0.5 + Math.random() * 1.5,
			delay: Math.random() * 5,
			duration: 3 + Math.random() * 4,
			depth: (Math.random() - 0.5) * 150,
			type: Math.random() > 0.5 ? 'star' : 'sparkle'
		}));
	});
</script>

<svelte:window bind:scrollY />

<div
	role="presentation"
	class="min-h-screen bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 relative overflow-x-hidden font-sans selection:bg-red-500/20"
	on:mousemove={handleMouseMove}
>
	<!-- Background Elements -->
	<div class="fixed inset-0 pointer-events-none z-0">
		<div
			class="absolute inset-0 opacity-[0.4]"
			style="background-image: radial-gradient(#fb7185 1px, transparent 1px); background-size: 32px 32px;"
		></div>

		<!-- Soft Glows -->
		<div
			class="absolute top-0 right-0 w-[800px] h-[800px] bg-red-100/30 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/2"
		></div>
		<div
			class="absolute bottom-0 left-0 w-[600px] h-[600px] bg-pink-100/30 rounded-full blur-[100px] translate-y-1/2 -translate-x-1/2"
		></div>

		<!-- Dynamic Decor Elements -->
		{#each decorations as d}
			<div
				in:fade={{ duration: 2000 }}
				class="absolute cursor-pointer hover:z-10 group pointer-events-auto"
				style="
                left: {d.x}%;
                top: {d.y}%;
                transform: scale({d.scale}) translate({$mouse.x * d.depth}px, {$mouse.y * d.depth +
					scrollY * d.depth * 0.002}px);
            "
			>
				<div
					class="animate-float"
					style="animation-delay: {d.delay}s; animation-duration: {d.duration}s;"
				>
					<div
						class="transition-all duration-500 ease-out group-hover:scale-150 group-hover:rotate-12 {d.type ===
						'star'
							? 'text-red-300 dark:text-red-500/30 group-hover:text-red-500'
							: 'text-pink-300 dark:text-pink-500/30 group-hover:text-pink-500'}"
					>
						<div class="animate-pulse" style="animation-duration: {d.duration / 1.5}s">
							{#if d.type === 'star'}
								<Star size={24} fill="currentColor" class="opacity-60" />
							{:else}
								<Sparkles size={28} class="opacity-80" />
							{/if}
						</div>
					</div>
				</div>
			</div>
		{/each}
	</div>

	<!-- NAV -->
	{#if !isFullScreenRoute}
		<LandingNavbar mouse={$mouse} showLogin={true} />
	{/if}

	<!-- CONTENT -->
	<main class={isFullScreenRoute ? 'relative w-full h-full' : 'relative max-w-7xl mx-auto px-6'}>
		<slot />
	</main>

	<!-- FOOTER -->
	{#if !isFullScreenRoute}
		<Footer />
	{/if}
</div>

<style>
	@keyframes float {
		0%,
		100% {
			transform: translateY(0) scale(1);
			opacity: 0.4;
		}
		50% {
			transform: translateY(-20px) scale(1.1);
			opacity: 0.8;
		}
	}
	.animate-float {
		animation: float ease-in-out infinite;
	}
</style>
