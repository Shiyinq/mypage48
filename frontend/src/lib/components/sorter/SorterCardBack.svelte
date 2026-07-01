<script lang="ts">
	interface Props {
		rank?: number;
	}

	let { rank = 0 }: Props = $props();
</script>

<div
	class="relative w-full h-full flex flex-col items-center p-[8%] bg-gradient-to-br from-red-800 to-red-950 overflow-hidden"
>
	<span
		class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 font-black text-center leading-none select-none drop-shadow-md text-[clamp(18px,7cqw,48px)] {rank ===
		1
			? 'text-yellow-400'
			: rank === 2
				? 'text-slate-300'
				: rank === 3
					? 'text-amber-600'
					: 'text-black/55'}"
	>
		{rank}
	</span>

	<div class="mt-auto flex flex-col items-center gap-[0.5%] w-full">
		<svg
			viewBox="0 0 24 24"
			class="w-[35%] min-w-[12px] text-yellow-400/80"
			fill="currentColor"
			stroke="none"
		>
			<path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14" />
		</svg>
		<span
			class="text-white/50 text-[clamp(4px,1.5cqw,8px)] font-black tracking-[0.15em] text-center leading-tight select-none"
		>
			OSHI SORTER
		</span>
	</div>
</div>
