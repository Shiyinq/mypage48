<script lang="ts">
	/**
	 * Skeleton for Event History Table matching the specific layout
	 */
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();
	interface Props {
		rows?: number;
	}

	let { rows = 5 }: Props = $props();
</script>

<div
	class="glass-panel rounded-3xl overflow-hidden shadow-sm border border-gray-100 dark:border-zinc-800"
	role="status"
	aria-label="Loading History"
>
	<div class="overflow-x-auto">
		<table class="w-full text-left border-collapse">
			<thead>
				<tr
					class="bg-gray-50/80 dark:bg-zinc-800/80 border-b border-gray-200 dark:border-zinc-700 text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 font-bold"
				>
					<th class="p-4">{$t('common.date')}</th>
					<th class="p-4">{$t('theater.events.eventName')}</th>
					<th class="p-4">Type</th>
					<th class="p-4">Members</th>
					<th class="p-4 text-right">Link</th>
				</tr>
			</thead>
			<tbody class="bg-white/50 dark:bg-zinc-900/50 divide-y divide-gray-100 dark:divide-zinc-700">
				{#each Array(rows)}
					<tr class="animate-pulse">
						<!-- Date Column -->
						<td class="p-4 whitespace-nowrap">
							<div class="flex flex-col gap-1">
								<div class="h-4 w-20 bg-gray-200 dark:bg-zinc-700 rounded"></div>
								<div class="h-3 w-12 bg-gray-200 dark:bg-zinc-700 rounded"></div>
							</div>
						</td>
						<!-- Event Details Column (Combined) -->
						<td class="p-4">
							<div class="flex items-center gap-3">
								<div
									class="w-12 h-8 rounded bg-gray-200 dark:bg-zinc-700 flex-shrink-0 border border-gray-200 dark:border-zinc-800"
								></div>
								<div class="h-4 w-48 bg-gray-200 dark:bg-zinc-700 rounded"></div>
							</div>
						</td>
						<!-- Type Column -->
						<td class="p-4">
							<div class="w-10 h-10 rounded-full bg-gray-200 dark:bg-zinc-700"></div>
						</td>
						<!-- Members Column -->
						<td class="p-4">
							<div class="h-4 w-8 bg-gray-200 dark:bg-zinc-700 rounded"></div>
						</td>
						<!-- Link Column -->
						<td class="p-4 text-right">
							<div class="inline-block w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700"></div>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
