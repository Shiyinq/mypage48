<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
		allowScaleUp?: boolean;
		fitHeight?: boolean;
	}

	let { children, allowScaleUp = false, fitHeight = false }: Props = $props();

	let wrapper: HTMLDivElement | undefined = $state();
	let content: HTMLDivElement | undefined = $state();
	let scale = $state(1);
	let scaledHeight = $state<number | undefined>(undefined);

	$effect(() => {
		if (!wrapper || !content) return;

		const update = () => {
			requestAnimationFrame(() => {
				if (!wrapper || !content) return;

				const availableW = wrapper.clientWidth;
				const availableH = wrapper.clientHeight;
				const neededW = content.scrollWidth;
				const neededH = content.scrollHeight;

				if (neededW <= 0 || neededH <= 0) return;

				let nextScale = availableW / neededW;

				if (fitHeight && availableH > 0) {
					const scaleH = availableH / neededH;
					nextScale = Math.min(nextScale, scaleH);
				}

				if (!allowScaleUp) {
					nextScale = Math.min(1, nextScale);
				}

				scale = nextScale;
				scaledHeight = neededH * nextScale;
			});
		};

		update();
		const observer = new ResizeObserver(update);
		observer.observe(wrapper);
		observer.observe(content);

		return () => observer.disconnect();
	});
</script>

<div
	bind:this={wrapper}
	class="w-full overflow-hidden {fitHeight ? 'flex justify-center h-full items-center' : ''}"
	style:height={!fitHeight && scaledHeight != null && scaledHeight > 0
		? `${scaledHeight}px`
		: undefined}
>
	<div
		bind:this={content}
		class="w-fit"
		style:transform="scale({scale})"
		style:transform-origin={fitHeight ? 'center center' : 'top left'}
	>
		{@render children()}
	</div>
</div>
