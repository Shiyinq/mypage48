<script lang="ts">
	import { Ticket } from 'lucide-svelte';
	interface Props {
		mouse?: { x: number; y: number };
		tagline?: string;
	}

	let { mouse = { x: 0, y: 0 }, tagline = '' }: Props = $props();
</script>

<div class="flex items-center gap-3 group">
	<div
		class="w-10 h-10 rounded-full idol-gradient flex items-center justify-center text-white shadow-xl shadow-red-500/20 ring-4 ring-white dark:ring-zinc-800 transition-transform group-hover:scale-105 duration-300"
	>
		<Ticket class="w-5 h-5 transition-transform group-hover:rotate-12" />
	</div>
	<div class="flex flex-col relative">
		<div
			class="absolute inset-0"
			style="transform: translate({mouse.x * 10}px, {mouse.y * 10}px)"
		></div>
		<h1
			class="text-xl font-black tracking-tighter text-slate-900 dark:text-white leading-none relative z-10"
			style="transform: translate({mouse.x * 5}px, {mouse.y * 5}px)"
		>
			MyPage<span class="text-red-600">48</span>
		</h1>
		{#if tagline}
			<span
				class="text-[8px] sm:text-[9px] font-bold text-slate-400 dark:text-zinc-500 tracking-[0.2em] uppercase mt-0.5 hidden sm:block relative z-10"
				style="transform: translate({mouse.x * 8}px, {mouse.y * 8}px)"
			>
				{tagline}
			</span>
		{/if}
	</div>
</div>
