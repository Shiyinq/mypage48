<script lang="ts">
	import { Ticket } from 'lucide-svelte';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';
	export let title: string;
	export let subtitle: string;
	export let cardWidth = 'max-w-md';
	export let icon: any = Ticket;
</script>

<div
	class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden py-12 bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 font-sans selection:bg-red-500/20"
>
	<!-- Background Elements -->
	<AnimatedBackground hideDecorationsOnMobile={true} />

	<div class="w-full {cardWidth}">
		<!-- Header -->
		<div class="text-center mb-8 animate-fade-in">
			<div
				class="w-16 h-16 rounded-full idol-gradient flex items-center justify-center text-white shadow-xl mx-auto mb-4 ring-4 ring-white/50 dark:ring-white/10"
			>
				<svelte:component this={icon} class="w-8 h-8" />
			</div>
			<div class="mb-2">
				<h1 class="text-3xl font-black text-gray-900 dark:text-white tracking-tight inline-block">
					MyPage<span class="text-red-600">48</span>
				</h1>
				{#if title}
					<span class="mx-2 text-gray-300 dark:text-gray-600">|</span>
					<span class="text-xl font-bold text-gray-700 dark:text-gray-300">{title}</span>
				{/if}
			</div>
			<p class="text-gray-500 dark:text-gray-400 font-medium mt-2">{subtitle}</p>
		</div>

		<!-- Card -->
		<div
			class="glass-panel p-8 rounded-3xl shadow-2xl border border-white/60 dark:border-zinc-800 backdrop-blur-xl animate-[slideUpFade_0.5s_ease-out]"
		>
			<slot />

			<div class="mt-6 pt-6 border-t border-gray-100 dark:border-zinc-800 text-center">
				<slot name="footer" />
			</div>
		</div>
	</div>
</div>
