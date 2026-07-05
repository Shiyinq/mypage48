<script lang="ts">
	import { onDestroy } from 'svelte';
	import type { Rive } from '@rive-app/canvas';

	let {
		src,
		width = '100%',
		height = '100%',
		autoplay = true,
		className = '',
		onready,
		onerror
	} = $props<{
		src: string;
		width?: string;
		height?: string;
		autoplay?: boolean;
		className?: string;
		onready?: () => void;
		onerror?: () => void;
	}>();

	let hasError = $state(false);
	let riveInstance: Rive | null = null;

	function riveAction(node: HTMLCanvasElement, url: string) {
		let currentAnim: Rive | null = null;

		async function load(currentUrl: string) {
			if (!currentUrl) return;
			hasError = false;

			if (currentAnim) currentAnim.cleanup();

			try {
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				const riveModule = (await import('@rive-app/canvas')) as any;
				const RiveClass = riveModule.Rive || riveModule.default?.Rive || riveModule.default;

				if (!RiveClass) throw new Error('Could not resolve Rive class');

				currentAnim = new RiveClass({
					src: currentUrl,
					canvas: node,
					autoplay: autoplay,
					onLoad: () => {
						if (onready) onready();
					},
					onLoadError: () => {
						console.error('Failed to load rive animation from:', currentUrl);
						hasError = true;
						if (onerror) onerror();
					}
				});
				riveInstance = currentAnim;
			} catch (err) {
				console.error('Error initializing rive:', err);
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
				if (currentAnim) currentAnim.cleanup();
			}
		};
	}

	onDestroy(() => {
		if (riveInstance) {
			riveInstance.cleanup();
		}
	});
</script>

<canvas
	use:riveAction={src}
	class={className}
	style="width: {width}; height: {height}; display: {hasError ? 'none' : 'block'};"
></canvas>
