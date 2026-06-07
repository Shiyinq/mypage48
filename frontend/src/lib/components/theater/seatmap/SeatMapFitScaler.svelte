<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	let wrapper: HTMLDivElement | undefined = $state();
	let content: HTMLDivElement | undefined = $state();
	let scale = $state(1);
	let scaledHeight = $state<number | undefined>(undefined);

	$effect(() => {
		if (!wrapper || !content) return;

		const update = () => {
			requestAnimationFrame(() => {
				if (!wrapper || !content) return;

				const available = wrapper.clientWidth;
				const needed = content.scrollWidth;
				const naturalHeight = content.scrollHeight;

				if (needed <= 0 || naturalHeight <= 0) return;

				const nextScale = Math.min(1, available / needed);
				scale = nextScale;
				scaledHeight = naturalHeight * nextScale;
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
	class="w-full overflow-hidden"
	style:height={scaledHeight != null && scaledHeight > 0 ? `${scaledHeight}px` : 'auto'}
>
	<div
		bind:this={content}
		class="w-fit"
		style:transform="scale({scale})"
		style:transform-origin="top left"
	>
		{@render children()}
	</div>
</div>
