<script lang="ts">
	import { Pencil, Trash2, User } from 'lucide-svelte';
	import type { Member } from '$lib/apis/members';
	import { createEventDispatcher } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { getExternalMediaUrl } from '$lib/utils/media';

	export let members: Member[] = [];

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
					<th class="p-4">{$t('admin.members.table.memberInfo')}</th>
					<th class="p-4">{$t('admin.members.table.generation')}</th>
					<th class="p-4">{$t('admin.members.table.jikoshoukai')}</th>
					<th class="p-4">{$t('admin.members.table.status')}</th>
					<th class="p-4 text-right">{$t('admin.members.table.actions')}</th>
				</tr>
			</thead>
			<tbody class="bg-white/50 dark:bg-zinc-900/50 divide-y divide-gray-100 dark:divide-zinc-700">
				{#each members as member (member.id)}
					<tr
						class="group border-b border-gray-100 dark:border-zinc-700 hover:bg-red-50/30 dark:hover:bg-red-900/10 transition-colors"
					>
						<td class="p-4">
							<div class="flex items-center gap-3">
								<div
									class="w-10 h-10 rounded-full bg-gray-100 dark:bg-zinc-800 overflow-hidden flex-shrink-0 border border-gray-200 dark:border-zinc-700"
								>
									{#if member.img}
										<img
											src={getExternalMediaUrl(member.img)}
											alt={member.name}
											class="w-full h-full object-cover"
										/>
									{:else}
										<div
											class="w-full h-full idol-gradient flex items-center justify-center relative overflow-hidden"
										>
											<User class="w-5 h-5 text-white/40" />
										</div>
									{/if}
								</div>
								<div>
									<div class="font-bold text-gray-800 dark:text-gray-200 text-sm">
										{member.name}
									</div>
									<div class="text-xs text-gray-400 dark:text-gray-500">
										{member.nickname}
									</div>
								</div>
							</div>
						</td>
						<td class="p-4">
							<span class="text-sm font-medium text-gray-600 dark:text-gray-400">
								{$t('admin.members.table.gen', { gen: member.generation })}
							</span>
						</td>
						<td class="p-4 max-w-xs">
							<span class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 italic">
								{member.jiko || '-'}
							</span>
						</td>
						<td class="p-4">
							<span
								class="px-2 py-1 rounded-full text-xs font-bold {member.active
									? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
									: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'}"
							>
								{member.active
									? $t('admin.members.table.active')
									: $t('admin.members.table.graduated')}
							</span>
						</td>
						<td class="p-4 text-right">
							<div class="flex items-center justify-end gap-2">
								<button
									on:click={() => dispatch('edit', member)}
									class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-full transition-colors cursor-pointer"
								>
									<Pencil class="w-4 h-4" />
								</button>
								<button
									on:click={() => dispatch('delete', member)}
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
