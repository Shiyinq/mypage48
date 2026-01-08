<script lang="ts">
	import { Pencil, Trash2, Calendar, Music } from 'lucide-svelte';
	import type { Setlist } from '$lib/apis/setlists';
	import { createEventDispatcher } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let setlists: Setlist[] = [];

	const dispatch = createEventDispatcher();
	const { t } = useTranslation();
</script>

<div class="glass-panel rounded-3xl overflow-hidden shadow-sm">
	<div class="overflow-x-auto">
		<table class="w-full text-left border-collapse">
			<thead>
				<tr
					class="bg-gray-50/80 dark:bg-zinc-800/80 border-b border-gray-200 dark:border-zinc-700 text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 font-bold"
				>
					<th class="p-4">{$t('admin.setlists.table.setlistInfo')}</th>
					<th class="p-4">{$t('admin.setlists.table.japaneseTitle')}</th>
					<th class="p-4">{$t('admin.setlists.table.type')}</th>
					<th class="p-4">{$t('admin.setlists.table.status')}</th>
					<th class="p-4 text-right">{$t('admin.setlists.table.actions')}</th>
				</tr>
			</thead>
			<tbody class="bg-white/50 dark:bg-zinc-900/50 divide-y divide-gray-100 dark:divide-zinc-700">
				{#each setlists as setlist (setlist.setlistId)}
					<tr
						class="group border-b border-gray-100 dark:border-zinc-700 hover:bg-red-50/30 dark:hover:bg-red-900/10 transition-colors"
					>
						<td class="p-4">
							<div class="flex items-center gap-3">
								<div
									class="w-12 h-16 rounded-lg bg-gray-100 dark:bg-zinc-800 overflow-hidden flex-shrink-0 border border-gray-200 dark:border-zinc-700"
								>
									{#if setlist.imageUrl}
										<img
											src={setlist.imageUrl}
											alt={setlist.title}
											class="w-full h-full object-cover"
										/>
									{:else}
										<div
											class="w-full h-full idol-gradient flex items-center justify-center relative overflow-hidden"
										>
											<Music class="w-5 h-5 text-white/40" />
										</div>
									{/if}
								</div>
								<div>
									<div class="font-bold text-gray-800 dark:text-gray-200 text-sm line-clamp-1">
										{setlist.title}
									</div>
									<div class="text-xs text-gray-400 dark:text-gray-500 mt-1">
										{$t('admin.setlists.table.songs', { count: (setlist.songs || []).length })}
									</div>
								</div>
							</div>
						</td>
						<td class="p-4">
							<span class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 italic">
								{setlist.titleJapanese || '-'}
							</span>
						</td>
						<td class="p-4">
							<span
								class="px-2 py-1 rounded-md text-xs font-bold border {setlist.type === 'setlist'
									? 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-900/20 dark:text-purple-400 dark:border-purple-800'
									: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800'}"
							>
								{setlist.type === 'setlist'
									? $t('admin.setlists.table.theaterSetlist')
									: $t('admin.setlists.table.specialEvent')}
							</span>
						</td>
						<td class="p-4">
							<span
								class="px-2 py-1 rounded-full text-xs font-bold {setlist.active
									? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
									: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'}"
							>
								{setlist.active
									? $t('admin.setlists.table.active')
									: $t('admin.setlists.table.inactive')}
							</span>
						</td>
						<td class="p-4 text-right">
							<div class="flex items-center justify-end gap-2">
								<button
									on:click={() => dispatch('edit', setlist)}
									class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-full transition-colors cursor-pointer"
								>
									<Pencil class="w-4 h-4" />
								</button>
								<button
									on:click={() => dispatch('delete', setlist)}
									class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-full transition-colors cursor-pointer"
								>
									<Trash2 class="w-4 h-4" />
								</button>
							</div>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
