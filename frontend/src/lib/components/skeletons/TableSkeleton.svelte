<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	/**
	 * Reusable table skeleton component for loading states
	 */
	export let rows: number = 5;
	export let columns: string[] = [];
	export let className: string = '';
</script>

<div
	class="glass-panel rounded-3xl overflow-hidden shadow-sm {className}"
	role="status"
	aria-label="Loading"
>
	<div class="overflow-x-auto">
		<table class="w-full text-left border-collapse">
			<thead>
				<tr
					class="bg-gray-50/80 dark:bg-zinc-800/80 border-b border-gray-200 dark:border-zinc-700 text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 font-bold"
				>
					{#each columns as column}
						<th class="p-4">{column}</th>
					{/each}
				</tr>
			</thead>
			<tbody class="bg-white/50 dark:bg-zinc-900/50 divide-y divide-gray-100 dark:divide-zinc-700">
				{#each Array(rows) as _}
					<tr class="border-b border-gray-100 dark:border-zinc-700">
						{#each columns as _, i}
							<td class="p-4">
								<div
									class="h-4 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse"
									style="width: {i === 0 ? '80px' : i === columns.length - 1 ? '60px' : '120px'}"
								></div>
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
