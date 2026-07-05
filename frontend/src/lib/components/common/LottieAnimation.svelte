<script lang="ts">
	import { onDestroy } from 'svelte';
	import lottie, { type AnimationItem } from 'lottie-web';

	let {
		src,
		width = '100%',
		height = '100%',
		loop = true,
		autoplay = true,
		speed = 1,
		className = '',
		onready,
		onerror
	} = $props<{
		src: string;
		width?: string;
		height?: string;
		loop?: boolean;
		autoplay?: boolean;
		speed?: number | string;
		className?: string;
		onready?: () => void;
		onerror?: () => void;
	}>();

	let hasError = $state(false);
	let animation: AnimationItem | null = null;

	function lottieAction(node: HTMLElement, url: string) {
		let currentAnim: AnimationItem | null = null;
		let abortController = new AbortController();

		async function load(currentUrl: string) {
			if (!currentUrl) return;
			hasError = false;
			abortController.abort();
			abortController = new AbortController();

			try {
				const res = await fetch(currentUrl, { signal: abortController.signal });
				if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

				let animationData;
				try {
					animationData = await res.json();
				} catch (_e) {
					throw new Error('Invalid JSON format (might be .riv or unsupported format)');
				}

				if (currentAnim) currentAnim.destroy();

				currentAnim = lottie.loadAnimation({
					container: node,
					renderer: 'svg',
					loop,
					autoplay,
					animationData
				});
				currentAnim.setSpeed(Number(speed));

				currentAnim.addEventListener('DOMLoaded', () => {
					if (onready) onready();
				});
				currentAnim.addEventListener('error', () => {
					hasError = true;
					if (onerror) onerror();
				});
				animation = currentAnim;
			} catch (err) {
				if (err instanceof Error && err.name === 'AbortError') return;
				console.error('Failed to load lottie animation:', err);
				hasError = true;
				if (onerror) onerror();
			}
		}

		load(url);

		return {
			update(newUrl: string) {
				if (newUrl !== url) {
					url = newUrl;
					load(url);
				}
			},
			destroy() {
				abortController.abort();
				if (currentAnim) currentAnim.destroy();
			}
		};
	}

	onDestroy(() => {
		if (animation) {
			animation.destroy();
		}
	});
</script>

<div
	use:lottieAction={src}
	class={className}
	style="width: {width}; height: {height}; display: {hasError ? 'none' : 'block'};"
></div>
