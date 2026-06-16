<script lang="ts">
	import { Heart, Flame, Star } from 'lucide-svelte';
	import { getTeamColors } from '$lib/constants/teamColors';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { spring, type Spring } from 'svelte/motion';

	let decorations: Array<{
		x: number;
		y: number;
		scale: number;
		delay: number;
		duration: number;
		depth: number;
		type: 'dream' | 'love' | 'passion';
	}> = $state([]);

	interface Props {
		interactive?: boolean;
		hideDecorationsOnMobile?: boolean;
		mouse?: Spring<{ x: number; y: number }>;
		scrollY?: number;
	}

	let {
		interactive = false,
		hideDecorationsOnMobile = false,
		mouse = $bindable(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 })),
		scrollY = $bindable(0)
	}: Props = $props();

	function handleMouseMove(event: MouseEvent) {
		if (window.innerWidth < 1024 || !window.matchMedia('(hover: hover)').matches) {
			mouse.set({ x: 0, y: 0 });
			return;
		}

		const clientX = event.clientX;
		const clientY = event.clientY;
		const clientWidth = window.innerWidth;
		const clientHeight = window.innerHeight;
		const x = clientX / clientWidth - 0.5;
		const y = clientY / clientHeight - 0.5;
		mouse.set({ x, y });
	}

	onMount(() => {
		decorations = Array.from({ length: 25 }, () => {
			const rand = Math.random();
			let type: 'dream' | 'love' | 'passion' = 'dream';
			if (rand < 0.33) type = 'love';
			else if (rand < 0.66) type = 'passion';

			return {
				x: Math.random() * 100,
				y: Math.random() * 100,
				scale: 0.5 + Math.random() * 1.5,
				delay: Math.random() * 5,
				duration: 3 + Math.random() * 4,
				depth: (Math.random() - 0.5) * 150,
				type
			};
		});
	});
</script>

<svelte:window onmousemove={handleMouseMove} bind:scrollY />

<div class="fixed inset-0 pointer-events-none z-0 overflow-hidden">
	<div
		class="absolute inset-0 opacity-[0.4]"
		style="background-image: radial-gradient(#fb7185 1px, transparent 1px); background-size: 32px 32px;"
	></div>

	<!-- Soft Glows -->
	<div
		class="absolute top-0 right-0 w-[800px] h-[800px] bg-red-100/30 dark:bg-red-900/10 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/2"
	></div>
	<div
		class="absolute bottom-0 left-0 w-[600px] h-[600px] bg-pink-100/30 dark:bg-rose-950/10 rounded-full blur-[100px] translate-y-1/2 -translate-x-1/2"
	></div>

	<!-- Static Decor Elements -->
	<div
		class={`absolute top-20 left-10 animate-pulse delay-700 ${hideDecorationsOnMobile ? 'hidden md:block' : ''} ${
			interactive
				? 'pointer-events-auto cursor-pointer hover:scale-125 transition-all duration-300'
				: 'pointer-events-none'
		}`}
		style="transform: translate({$mouse.x * 20}px, {$mouse.y * 20 +
			scrollY * 0.2}px); color: {getTeamColors('LOVE').badgeBg};"
	>
		<Heart size={48} fill="currentColor" class="opacity-60" />
	</div>
	<div
		class={`absolute top-40 right-10 animate-pulse delay-300 ${hideDecorationsOnMobile ? 'hidden md:block' : ''} ${
			interactive
				? 'pointer-events-auto cursor-pointer hover:scale-125 hover:rotate-12 transition-all duration-300'
				: 'pointer-events-none'
		}`}
		style="transform: translate({$mouse.x * 60}px, {$mouse.y * 60 +
			scrollY * 0.5}px); color: {getTeamColors('PASSION').badgeBg};"
	>
		<Flame size={32} fill="currentColor" class="opacity-60" />
	</div>

	<!-- Dynamic Decor Elements -->
	{#each decorations as d}
		<div
			in:fade={{ duration: 2000 }}
			class="absolute {interactive
				? 'cursor-pointer hover:z-10 group pointer-events-auto'
				: 'pointer-events-none'}"
			style="
                left: {d.x}%;
                top: {d.y}%;
                transform: scale({d.scale}) translate({($mouse.x || 0) * d.depth}px, {($mouse.y ||
				0) *
				d.depth +
				(scrollY || 0) * d.depth * 0.002}px);
            "
		>
			<div
				class="animate-float"
				style="animation-delay: {d.delay}s; animation-duration: {d.duration}s;"
			>
				<div
					class="transition-all duration-500 ease-out {interactive
						? 'hover:scale-150 hover:rotate-12'
						: ''}"
					style="color: {getTeamColors(d.type).badgeBg};"
				>
					<div
						class={`animate-pulse ${hideDecorationsOnMobile ? 'hidden md:block' : ''}`}
						style="animation-duration: {d.duration / 1.5}s"
					>
						{#if d.type === 'love'}
							<Heart size={28} strokeWidth={2} fill="currentColor" class="opacity-60" />
						{:else if d.type === 'passion'}
							<Flame size={28} strokeWidth={2} fill="currentColor" class="opacity-60" />
						{:else}
							<Star size={28} strokeWidth={2} fill="currentColor" class="opacity-60" />
						{/if}
					</div>
				</div>
			</div>
		</div>
	{/each}
</div>

<style>
	@keyframes float {
		0%,
		100% {
			transform: translateY(0) scale(1);
			opacity: 0.4;
		}
		50% {
			transform: translateY(-20px) scale(1.1);
			opacity: 0.8;
		}
	}
	.animate-float {
		animation-name: float;
		animation-timing-function: ease-in-out;
		animation-iteration-count: infinite;
	}
</style>
