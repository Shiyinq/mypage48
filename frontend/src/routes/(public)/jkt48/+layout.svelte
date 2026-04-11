<script lang="ts">
	import { spring } from 'svelte/motion';
	import { onMount } from 'svelte';
	import LandingNavbar from '$lib/components/landing-page/LandingNavbar.svelte';
	import Footer from '$lib/components/landing-page/Footer.svelte';
	import { page } from '$app/stores';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';
	import ScrollToTop from '$lib/components/common/ScrollToTop.svelte';

	let scrollY = 0;
	let mouse = spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 });

	$: isFullScreenRoute = $page.url.pathname.includes('/live/multiview');

	// Use addEventListener instead of svelte:window bind:scrollY
	// to avoid conflicting with ScrollToTop's own bind:scrollY binding
	onMount(() => {
		const handleScroll = () => {
			scrollY = window.scrollY;
		};
		window.addEventListener('scroll', handleScroll, { passive: true });
		return () => window.removeEventListener('scroll', handleScroll);
	});
</script>

<div
	class="min-h-screen bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 relative font-sans selection:bg-red-500/20"
>
	<!-- Background Elements -->
	<AnimatedBackground interactive={true} bind:mouse {scrollY} />

	<!-- NAV -->
	{#if !isFullScreenRoute}
		<LandingNavbar mouse={$mouse} showLogin={true} />
	{/if}

	<!-- CONTENT -->
	<main
		class={isFullScreenRoute ? 'relative w-full h-full' : 'relative max-w-7xl mx-auto px-3 sm:px-6'}
	>
		<slot />
	</main>

	<!-- FOOTER -->
	{#if !isFullScreenRoute}
		<Footer />
	{/if}
</div>

<!-- Scroll to Top Button (uses its own svelte:window bind:scrollY without conflicts) -->
<ScrollToTop />
