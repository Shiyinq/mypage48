<script lang="ts">
	import { spring } from 'svelte/motion';
	import LandingNavbar from '$lib/components/landing-page/LandingNavbar.svelte';
	import Footer from '$lib/components/landing-page/Footer.svelte';
	import { page } from '$app/stores';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';

	let scrollY = 0;
	let mouse = spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 });

	$: isFullScreenRoute = $page.url.pathname.includes('/live/multiview');
</script>

<svelte:window bind:scrollY />

<div
	role="presentation"
	class="min-h-screen bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 relative overflow-x-hidden font-sans selection:bg-red-500/20"
>
	<!-- Background Elements -->
	<AnimatedBackground interactive={true} bind:mouse bind:scrollY />


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
