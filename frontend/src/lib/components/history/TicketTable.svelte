<script lang="ts">
	import { stopPropagation } from 'svelte/legacy';

	import { Clock, Pencil, Save, Trash2, X, Ticket as TicketIcon } from 'lucide-svelte';
	import type { Ticket } from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatCurrency } from '$lib/utils/formatting';
	import { formatDate } from '$lib/i18n';
	import { cleanseMarkdown } from '$lib/utils/markdown';
	import { createEventDispatcher } from 'svelte';

	interface Props {
		tickets?: Ticket[];
		onupdateNote?: (ticketId: string, note: string) => void;
		oneditTicket?: (ticket: Ticket) => void;
		ondeleteTicket?: (ticketId: string) => void;
	}

	let { tickets = [], onupdateNote, oneditTicket, ondeleteTicket }: Props = $props();

	const { t } = useTranslation();

	let editingNoteId: string | null = $state(null);
	let noteText = $state('');

	function startEditingNote(ticket: Ticket) {
		editingNoteId = ticket._id;
		noteText = cleanseMarkdown(ticket.notes || '');
	}

	function saveNote(ticket: Ticket) {
		if (ticket.notes !== noteText) {
			onupdateNote?.(ticket._id, noteText);
		}
		editingNoteId = null;
	}

	function cancelEditingNote() {
		editingNoteId = null;
		noteText = '';
	}
</script>

<div class="glass-panel rounded-3xl overflow-hidden shadow-sm">
	<div class="overflow-x-auto">
		<table class="w-full text-left border-collapse">
			<thead>
				<tr
					class="bg-gray-50/80 dark:bg-zinc-800/80 border-b border-gray-200 dark:border-zinc-700 text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 font-bold"
				>
					<th class="p-4">{$t('history.date')}</th>
					<th class="p-4">{$t('history.eventDetails')}</th>
					<th class="p-4">{$t('history.seat')}</th>
					<th class="p-4">{$t('history.price')}</th>
					<th class="p-4">{$t('history.notes')}</th>
					<th class="p-4 text-right">{$t('history.actions')}</th>
				</tr>
			</thead>
			<tbody class="bg-white/50 dark:bg-zinc-900/50 divide-y divide-gray-100 dark:divide-zinc-700">
				{#each tickets as ticket (ticket._id)}
					<tr
						class="group border-b border-gray-100 dark:border-zinc-700 hover:bg-red-50/30 dark:hover:bg-red-900/10 transition-colors"
					>
						<td class="p-4">
							<div class="flex flex-col">
								<span class="font-bold text-gray-800 dark:text-gray-200 text-sm">
									{$formatDate(ticket.event.date, {
										day: 'numeric',
										month: 'short',
										year: '2-digit'
									})}
								</span>

								<span
									class="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1 mt-0.5"
								>
									<Clock class="w-3 h-3" />
									{ticket.event.time}
								</span>
							</div>
						</td>
						<td class="p-4">
							<div class="flex items-center gap-3">
								<div
									class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-zinc-800 overflow-hidden flex-shrink-0 border border-gray-200 dark:border-zinc-700"
								>
									{#if ticket.imageUrl}
										<img src={ticket.imageUrl} alt="" class="w-full h-full object-cover" />
									{:else}
										<div
											class="w-full h-full idol-gradient flex items-center justify-center relative overflow-hidden"
										>
											<TicketIcon class="w-5 h-5 text-white/40 transform -rotate-12" />
										</div>
									{/if}
								</div>
								<div>
									<div class="font-bold text-gray-800 dark:text-gray-200 text-sm line-clamp-1">
										{ticket.event.title}
									</div>
									<div class="text-xs text-gray-400 dark:text-gray-500 font-mono">
										#{ticket.ticket_id}
									</div>
								</div>
							</div>
						</td>
						<td class="p-4">
							<div
								class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 shadow-sm"
							>
								<span
									class="text-xs font-bold text-red-500 bg-red-50 dark:bg-red-900/30 px-1.5 rounded"
									>{ticket.seat.section}</span
								>
								<span class="text-sm font-bold text-gray-700 dark:text-gray-300"
									>{ticket.seat.number}</span
								>
							</div>
						</td>
						<td class="p-4">
							<span class="text-sm font-medium text-gray-600 dark:text-gray-400">
								{formatCurrency(ticket.price)}
							</span>
						</td>
						<td class="p-4 w-1/3">
							{#if editingNoteId === ticket._id}
								<div class="flex items-center gap-2">
									<!-- svelte-ignore a11y_autofocus -->
									<input
										autofocus
										bind:value={noteText}
										class="w-full text-sm text-gray-900 dark:text-gray-100 p-2 border border-red-200 dark:border-red-500/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 bg-white dark:bg-zinc-800"
										onkeydown={(e) => e.key === 'Enter' && saveNote(ticket)}
										onblur={() => saveNote(ticket)}
									/>
									<button
										onclick={stopPropagation(() => saveNote(ticket))}
										class="p-1.5 bg-red-600 text-white rounded-md hover:bg-red-700 cursor-pointer"
										><Save class="w-3 h-3" /></button
									>
									<button
										onclick={stopPropagation(cancelEditingNote)}
										class="p-1.5 bg-gray-200 dark:bg-zinc-700 text-gray-600 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-zinc-600 cursor-pointer"
										><X class="w-3 h-3" /></button
									>
								</div>
							{:else}
								<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
								<div
									onclick={() => startEditingNote(ticket)}
									class="text-sm text-gray-500 dark:text-gray-400 italic cursor-pointer hover:text-red-600 flex items-center gap-2 group/note"
								>
									<span class="line-clamp-1"
										>{cleanseMarkdown(ticket.notes) || $t('history.addNote')}</span
									>
									<Pencil
										class="w-3 h-3 opacity-0 group-hover/note:opacity-100 transition-opacity"
									/>
								</div>
							{/if}
						</td>
						<td class="p-4 text-right">
							<div class="flex items-center justify-end gap-2">
								<button
									onclick={() => oneditTicket?.(ticket)}
									class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-full transition-colors cursor-pointer"
								>
									<Pencil class="w-4 h-4" />
								</button>
								<button
									onclick={() => ondeleteTicket?.(ticket._id)}
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
