<script lang="ts">
	import { Ticket } from 'lucide-svelte';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	interface Props {
		title: string;
		subtitle: string;
		cardWidth?: string;
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		icon?: any;
		children?: import('svelte').Snippet;
		footer?: import('svelte').Snippet;
	}

	let {
		title,
		subtitle,
		cardWidth = 'max-w-md',
		icon = Ticket,
		children,
		footer
	}: Props = $props();

	const SvelteComponent = $derived(icon);
</script>

<div
	class="min-h-screen flex items-center justify-center p-3 relative overflow-hidden py-4 sm:py-6 bg-gradient-to-b from-pink-50/20 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 font-sans selection:bg-red-500/20"
>
	<!-- Background Elements -->
	<AppBackground hideDecorationsOnMobile={true} />

	<div class="w-full {cardWidth} px-1">
		<!-- Card -->
		<div
			class="glass-panel p-5 sm:p-7 rounded-[2rem] shadow-sm border border-gray-200/50 dark:border-zinc-800/80 backdrop-blur-xl transition-all"
		>
			<!-- Header (Inside card) -->
			<div class="text-center mb-6">
				<div
					class="w-12 h-12 rounded-2xl idol-gradient flex items-center justify-center text-white shadow-lg shadow-red-500/10 mx-auto mb-4 rotate-3 ring-4 ring-white dark:ring-zinc-900"
				>
					<SvelteComponent class="w-6 h-6" />
				</div>
				<div class="flex flex-col sm:flex-row items-center justify-center gap-1.5 mb-2">
					<h1
						class="text-2xl sm:text-3xl font-black text-gray-900 dark:text-white tracking-tighter leading-none"
					>
						MyPage<span class="text-red-600">48</span>
					</h1>
					{#if title}
						<div class="flex items-center gap-1.5">
							<span class="hidden sm:block text-gray-300 dark:text-zinc-700">|</span>
							<span
								class="text-lg sm:text-xl font-bold text-gray-700 dark:text-zinc-300 leading-none"
								>{title}</span
							>
						</div>
					{/if}
				</div>
				<p class="text-gray-500 dark:text-zinc-500 font-medium text-[13px]">{subtitle}</p>
			</div>

			{@render children?.()}

			<div class="mt-8 pt-6 border-t border-gray-100 dark:border-zinc-800/50 text-center">
				{@render footer?.()}
			</div>
		</div>
	</div>
</div>
