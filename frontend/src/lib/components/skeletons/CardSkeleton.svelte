<script lang="ts">
	/**
	 * Reusable card skeleton component for loading states
	 */
	export let lines: number = 3;
	export let showIcon: boolean = true;
	export let className: string = '';
</script>

<div
	class="glass-panel rounded-3xl p-5 animate-pulse {className}"
	role="status"
	aria-label="Loading"
>
	{#if showIcon}
		<div class="flex items-center gap-3 mb-4">
			<div class="w-10 h-10 rounded-xl bg-gray-200 dark:bg-zinc-700"></div>
			<div class="flex-1">
				<div class="h-4 w-24 bg-gray-200 dark:bg-zinc-700 rounded mb-2"></div>
				<div class="h-3 w-16 bg-gray-200 dark:bg-zinc-700 rounded"></div>
			</div>
		</div>
	{/if}
	<div class="space-y-3">
		{#each Array(lines) as _, i}
			<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded" style="width: {100 - i * 15}%"></div>
		{/each}
	</div>
</div>
