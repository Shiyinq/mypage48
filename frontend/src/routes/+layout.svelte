<script lang="ts">
	import ToastContainer from '$lib/components/ToastContainer.svelte';
	import '../app.css';
	import { onMount } from 'svelte';
	import { spring } from 'svelte/motion';
	import { fade } from 'svelte/transition';
	import { navigating } from '$app/stores';

	let coords = spring(
		{ x: 0, y: 0 },
		{
			stiffness: 0.5,
			damping: 0.6
		}
	);

	let size = spring(10, {
		stiffness: 0.1,
		damping: 0.3
	});

	onMount(() => {
		const handleMouseMove = (e: MouseEvent) => {
			coords.set({ x: e.clientX, y: e.clientY });

			// Simple intent detection: grow cursor if hovering over text or interactive
			const target = e.target as HTMLElement;
			if (
				target &&
				(target.tagName === 'BUTTON' ||
					target.tagName === 'A' ||
					target.closest('a') ||
					target.closest('button'))
			) {
				size.set(40);
			} else {
				size.set(10);
			}
		};

		window.addEventListener('mousemove', handleMouseMove);

		return () => {
			window.removeEventListener('mousemove', handleMouseMove);
		};
	});
</script>

<div class="atmosphere"></div>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>

<div class="bg-asset" in:fade={{ duration: 1500 }}>
	<img src="/assets/background/bg-landing.png" alt="Hero Background" />
</div>

{#if $navigating}
	<div class="loading-bar"></div>
{/if}

<div
	class="custom-cursor"
	style="left: {$coords.x}px; top: {$coords.y}px; width: {$size}px; height: {$size}px;"
></div>

<ToastContainer />
<main class="organic-container">
	<slot />
</main>

<style>
	.custom-cursor {
		position: fixed;
		border-radius: 50%;
		background: #fff;
		mix-blend-mode: difference;
		pointer-events: none;
		transform: translate(-50%, -50%);
		z-index: 9999;
		transition:
			width 0.2s,
			height 0.2s; /* Initial size transition handled by spring, but this helps smoothly render changes if spring is busy */
	}

	.bg-asset {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 100%;
		height: 100%;
		z-index: 0;
		opacity: 0.5;
		pointer-events: none;
	}

	.bg-asset img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		object-position: center;
		mask-image: radial-gradient(circle, black 40%, transparent 80%);
		-webkit-mask-image: radial-gradient(circle, black 40%, transparent 80%);
	}

	/* Ensure content sits above background */
	main {
		position: relative;
		z-index: 10;
		width: 100%;
		min-height: 100vh;
	}

	.loading-bar {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 3px;
		background: linear-gradient(90deg, var(--primary), var(--secondary), var(--primary));
		background-size: 200% 100%;
		z-index: 10000;
		animation: loading-scan 1.5s linear infinite;
	}

	@keyframes loading-scan {
		0% {
			background-position: 100% 0;
		}
		100% {
			background-position: -100% 0;
		}
	}
</style>
