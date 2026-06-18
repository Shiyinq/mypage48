<script lang="ts">
	interface Props {
		/**
		 * Skeleton component for ticket/history cards
		 */
		count?: number;
		className?: string;
	}

	let { count = 6, className = '' }: Props = $props();
</script>

<div
	class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 {className}"
	role="status"
	aria-label="Loading"
>
	<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
	{#each Array(count)}
		<div class="shadow-sm transition-all duration-300 w-full group transform-gpu rounded-2xl">
			<div
				class="ticket-mask bg-white dark:bg-zinc-900 rounded-2xl overflow-hidden border border-gray-100 dark:border-zinc-700 flex flex-row h-full min-h-[180px] animate-pulse w-full"
			>
				<!-- Image Section (Left) -->
				<div
					class="w-[140px] sm:w-[180px] h-full bg-gray-200 dark:bg-zinc-800 relative flex-shrink-0"
				>
					<div class="absolute top-2 left-2 w-12 h-4 rounded-md bg-gray-300 dark:bg-zinc-700"></div>
				</div>

				<!-- Dotted Divider Line -->
				<div
					class="w-0 border-l-[2px] border-dotted border-gray-300 dark:border-zinc-600 my-3 relative z-10"
				></div>

				<!-- Content Section (Right) -->
				<div class="flex-1 flex flex-col min-w-0">
					<!-- Header -->
					<div class="p-3 pb-0 space-y-2">
						<div class="flex justify-between items-start gap-2">
							<div class="flex-1 min-w-0 space-y-1.5">
								<div class="h-2 w-12 bg-gray-200 dark:bg-zinc-800 rounded"></div>
								<div class="h-4 w-3/4 bg-gray-200 dark:bg-zinc-800 rounded"></div>
								<div class="h-4 w-1/2 bg-gray-200 dark:bg-zinc-800 rounded"></div>
							</div>
						</div>
					</div>

					<!-- Details Grid -->
					<div class="px-3 py-2 grid grid-cols-2 gap-x-2 gap-y-1">
						<div class="flex items-center gap-1.5">
							<div class="w-3 h-3 rounded-full bg-gray-200 dark:bg-zinc-800"></div>
							<div class="h-3 w-16 bg-gray-200 dark:bg-zinc-800 rounded"></div>
						</div>
						<div class="flex items-center gap-1.5">
							<div class="w-3 h-3 rounded-full bg-gray-200 dark:bg-zinc-800"></div>
							<div class="h-3 w-12 bg-gray-200 dark:bg-zinc-800 rounded"></div>
						</div>
						<!-- Seat -->
						<div class="col-span-2 flex items-center mt-1 gap-1.5">
							<div class="w-5 h-5 rounded-full bg-gray-200 dark:bg-zinc-800"></div>
							<div class="h-3 w-20 bg-gray-200 dark:bg-zinc-800 rounded"></div>
						</div>
					</div>

					<!-- Notes Area -->
					<div class="px-3 flex-1 min-h-0 flex flex-col">
						<div class="flex-1 bg-gray-50 dark:bg-zinc-800/50 rounded-lg p-2">
							<div class="h-full w-full bg-gray-200 dark:bg-zinc-800/50 rounded"></div>
						</div>
					</div>

					<!-- Footer Actions -->
					<div
						class="px-3 py-2 flex justify-between items-center border-t border-gray-100 dark:border-zinc-800 mt-1"
					>
						<div class="h-3 w-16 bg-gray-200 dark:bg-zinc-800 rounded"></div>
						<div class="h-4 w-4 rounded bg-gray-200 dark:bg-zinc-800"></div>
					</div>
				</div>
			</div>
		</div>
	{/each}
</div>

<style>
	.ticket-mask {
		--mask-pos: 140px;
		--cutout-size: 10px;
		-webkit-mask-image:
			radial-gradient(
				circle at var(--mask-pos) 0,
				transparent var(--cutout-size),
				black calc(var(--cutout-size) + 0.5px)
			),
			radial-gradient(
				circle at var(--mask-pos) 100%,
				transparent var(--cutout-size),
				black calc(var(--cutout-size) + 0.5px)
			);
		-webkit-mask-size:
			100% 51%,
			100% 51%;
		-webkit-mask-position: top, bottom;
		-webkit-mask-repeat: no-repeat;
		mask-image:
			radial-gradient(
				circle at var(--mask-pos) 0,
				transparent var(--cutout-size),
				black calc(var(--cutout-size) + 0.5px)
			),
			radial-gradient(
				circle at var(--mask-pos) 100%,
				transparent var(--cutout-size),
				black calc(var(--cutout-size) + 0.5px)
			);
		mask-size:
			100% 51%,
			100% 51%;
		mask-position: top, bottom;
		mask-repeat: no-repeat;
	}

	@media (min-width: 640px) {
		.ticket-mask {
			--mask-pos: 180px;
		}
	}
</style>
