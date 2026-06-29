<script lang="ts">
	import { spring } from 'svelte/motion';
	import { onMount } from 'svelte';
	import LandingNavbar from '$lib/components/landing-page/LandingNavbar.svelte';
	import Footer from '$lib/components/landing-page/Footer.svelte';
	import { page } from '$app/stores';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import ScrollToTop from '$lib/components/common/ScrollToTop.svelte';
	import { isImmersive } from '$lib/stores';
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	let scrollY = $state(0);
	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));

	let isLiveRoute = $derived($page.url.pathname.includes('/live'));

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
	<AppBackground interactive={true} bind:mouse {scrollY} />

	<!-- NAV -->
	{#if !isLiveRoute && !isImmersive.value}
		<LandingNavbar mouse={$mouse} showLogin={true} />
	{/if}

	<!-- CONTENT -->
	<main
		class={isLiveRoute || isImmersive.value
			? 'relative w-full h-full'
			: 'relative max-w-7xl mx-auto px-3 sm:px-6'}
	>
		{@render children?.()}
	</main>

	<!-- FOOTER -->
	{#if !isLiveRoute && !isImmersive.value}
		<Footer />
	{/if}
</div>

<!-- Scroll to Top Button (uses its own svelte:window bind:scrollY without conflicts) -->
<ScrollToTop />
