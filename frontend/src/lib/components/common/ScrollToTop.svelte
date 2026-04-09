<script lang="ts">
	import { ArrowUp } from 'lucide-svelte';
	import { fly } from 'svelte/transition';
	import { page } from '$app/stores';
	import { isAuthenticated } from '$lib/stores';

	let scrollY = 0;
	let showButton = false;

	// Show button if scrolled down AND (not on landing page OR user is authenticated)
	// This hides it on the public landing page ('/') but keeps it on the dashboard ('/')
	$: showButton = scrollY > 300;

	function scrollToTop() {
		if (typeof window !== 'undefined') {
			window.scrollTo({
				top: 0,
				behavior: 'smooth'
			});

			// Backup for various scroll containers
			document.documentElement.scrollTo({ top: 0, behavior: 'smooth' });
			document.body.scrollTo({ top: 0, behavior: 'smooth' });
		}
	}
</script>

<svelte:window bind:scrollY />

{#if showButton}
	<button
		on:click={scrollToTop}
		transition:fly={{ y: 20, duration: 300 }}
		class="fixed z-[9999] bottom-24 right-4 md:bottom-8 md:right-8 idol-gradient text-white p-3 rounded-full shadow-lg shadow-red-500/30 transition-all duration-300 hover:scale-110 group focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 cursor-pointer pointer-events-auto"
		aria-label="Scroll to top"
	>
		<ArrowUp class="w-6 h-6 transition-transform group-hover:-translate-y-1" />
	</button>
{/if}
