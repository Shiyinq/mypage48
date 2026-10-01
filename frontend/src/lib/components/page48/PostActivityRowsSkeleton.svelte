<script lang="ts">
	interface Props {
		/** Shape of the list being loaded: quote cards or repost/like user rows. */
		kind: 'posts' | 'users';
		count?: number;
	}

	let { kind, count = 3 }: Props = $props();
</script>

<div class="flex animate-pulse flex-col divide-y divide-gray-200/60 dark:divide-white/10">
	{#each Array(count) as _, i (i)}
		{#if kind === 'posts'}
			<!-- Mirrors PostCard -->
			<div class="flex gap-4 px-5 pb-3 pt-5 sm:px-6">
				<div class="h-11 w-11 shrink-0 rounded-full bg-gray-200/80 dark:bg-zinc-800"></div>
				<div class="flex min-w-0 flex-1 flex-col gap-2 pt-0.5">
					<div class="flex items-center justify-between gap-2">
						<div class="h-4 w-28 rounded bg-gray-200 dark:bg-zinc-800"></div>
						<div class="h-3.5 w-9 rounded bg-gray-200/80 dark:bg-zinc-800"></div>
					</div>
					<div class="h-3.5 w-full rounded bg-gray-200 dark:bg-zinc-800"></div>
					<div class="h-3.5 w-11/12 rounded bg-gray-200 dark:bg-zinc-800"></div>
					<div class="mt-1.5 flex items-center gap-6">
						{#each [0, 1, 2, 3] as _}
							<div class="h-4 w-7 rounded-full bg-gray-200/80 dark:bg-zinc-800"></div>
						{/each}
					</div>
				</div>
			</div>
		{:else}
			<!-- Mirrors UserListItem -->
			<div class="flex items-start gap-3 px-5 py-3 sm:px-6">
				<div class="h-11 w-11 shrink-0 rounded-full bg-gray-200/80 dark:bg-zinc-800"></div>
				<div class="flex min-w-0 flex-1 flex-col gap-2 pt-0.5">
					<div class="h-4 w-32 rounded bg-gray-200 dark:bg-zinc-800"></div>
					<div class="h-3.5 w-3/4 rounded bg-gray-200 dark:bg-zinc-800"></div>
				</div>
			</div>
		{/if}
	{/each}
</div>
