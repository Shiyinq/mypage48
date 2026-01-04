<script lang="ts">
	import { navigating } from '$app/stores';
	import { onDestroy } from 'svelte';

	// Delay before showing loading bar (ms) - prevents flashing on fast navigations
	const SHOW_DELAY = 150;

	let p = 0;
	let visible = false;
	let interval: ReturnType<typeof setInterval>;
	let delayTimeout: ReturnType<typeof setTimeout>;

	function start() {
		// Clear any existing timers
		clearInterval(interval);
		clearTimeout(delayTimeout);

		// Reset progress but don't show yet
		p = 0;

		// Only show loading bar after delay (prevents flash on fast navigations)
		delayTimeout = setTimeout(() => {
			visible = true;
			p = 0.1; // Initial jump

			interval = setInterval(() => {
				// Asymptotic approach to 0.95
				p += (0.95 - p) * 0.05;
			}, 100);
		}, SHOW_DELAY);
	}

	function finish() {
		// Cancel the delay timeout if navigation finished before bar was shown
		clearTimeout(delayTimeout);
		clearInterval(interval);

		// If visible, animate to 100% and hide
		if (visible) {
			p = 1;
			setTimeout(() => {
				visible = false;
				setTimeout(() => {
					p = 0;
				}, 300);
			}, 400);
		} else {
			// Navigation finished before bar was shown, just reset
			p = 0;
		}
	}

	// Watch for navigation changes
	$: if ($navigating) {
		if (!visible || p >= 1) {
			start();
		}
	} else {
		finish();
	}

	onDestroy(() => {
		clearInterval(interval);
		clearTimeout(delayTimeout);
	});
</script>

{#if visible}
	<div class="fixed top-0 left-0 right-0 z-[100000] pointer-events-none h-[3px]">
		<div
			class="h-full bg-[#e3000f] shadow-[0_0_10px_rgba(227,0,15,0.5)]"
			style="width: {p * 100}%; transition: width 200ms ease-out;"
		></div>
	</div>
{/if}
