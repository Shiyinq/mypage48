<script lang="ts">
	import { navigating } from '$app/stores';
	import { onDestroy } from 'svelte';

	let p = 0;
	let visible = false;
	let interval: ReturnType<typeof setInterval>;

	function start() {
		// Clear any existing finish timers or intervals
		clearInterval(interval);

		visible = true;
		p = 0;
		// Initial "start" jump
		p = 0.1;

		interval = setInterval(() => {
			// Asymptotic approach to 0.95
			// The closer we get to 0.95, the smaller the step
			p += (0.95 - p) * 0.05;
		}, 100);
	}

	function finish() {
		clearInterval(interval);
		p = 1;

		// Wait for the width transition to complete (approx 200ms)
		// then hide the bar
		setTimeout(() => {
			visible = false;
			// Reset p after it is hidden to be ready for next time
			setTimeout(() => {
				p = 0;
			}, 300);
		}, 400);
	}

	// Watch for navigation changes
	$: if ($navigating) {
		// If we aren't currently showing the bar, or if we are (but effectively "done" from a previous run that didn't clean up?), start over
		if (!visible || p >= 1) {
			start();
		}
	} else {
		// If navigation stopped and we are visible, finish the animation
		if (visible && p < 1) {
			finish();
		}
	}

	onDestroy(() => {
		if (interval) clearInterval(interval);
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
