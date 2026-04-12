<script lang="ts">
	import type { TicketItem } from '$lib/apis/setlists';
	import { Clock, Trash2 } from 'lucide-svelte';
	import { formatCurrency } from '$lib/utils/formatting';
	import { formatDate } from '$lib/i18n';

	interface Props {
		ticket: TicketItem;
		onclick?: () => void;
	}

	let { ticket, onclick }: Props = $props();

	function handleDelete(e: MouseEvent) {
		e.stopPropagation();
		onclick?.();
	}
</script>

<div
	class="group relative bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 p-1 overflow-hidden transition-all hover:shadow-md hover:border-purple-200 dark:hover:border-purple-900/30"
>
	<!-- Visual accent on left -->
	<div
		class="absolute left-0 top-0 bottom-0 w-1.5 bg-gradient-to-b from-purple-500 to-indigo-600 rounded-l-full"
	></div>

	<div class="flex items-center gap-4 p-4 pl-6">
		<!-- Date Box -->
		<div
			class="flex-shrink-0 flex flex-col items-center justify-center w-14 h-14 bg-gray-50 dark:bg-zinc-800 rounded-xl border border-gray-100 dark:border-zinc-700"
		>
			<span class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase leading-none">
				{$formatDate(ticket.event.date, {
					month: 'short'
				})}
			</span>

			<span class="text-xl font-black text-gray-900 dark:text-white leading-tight">
				{new Date(ticket.event.date).getDate()}
			</span>
		</div>

		<!-- Ticket Info -->
		<div class="flex-1 min-w-0">
			<div class="flex items-center gap-2 mb-1">
				<span
					class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 text-xs font-bold border border-purple-100 dark:border-purple-900/30"
				>
					<Clock class="w-3 h-3" />
					{ticket.event.time}
				</span>
				<span class="text-xs text-gray-400 font-medium">
					{new Date(ticket.event.date).getFullYear()}
				</span>
			</div>
			<div class="flex items-baseline gap-2">
				<span class="text-sm text-gray-500 dark:text-gray-400 font-medium">Seat</span>
				<span class="text-lg font-bold text-gray-900 dark:text-white font-mono tracking-tight">
					{ticket.seat.section}-{ticket.seat.number}
				</span>
			</div>
		</div>

		<!-- Price & Check -->
		<div class="text-right hidden sm:block">
			<div class="text-sm font-bold text-gray-900 dark:text-white">
				{formatCurrency(ticket.price)}
			</div>
			{#if ticket.notes}
				<div class="text-xs text-gray-400 italic max-w-[150px] truncate">
					"{ticket.notes}"
				</div>
			{/if}
		</div>

		<!-- Delete Action -->
		<button
			onclick={handleDelete}
			class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl opacity-0 group-hover:opacity-100 transition-all transform scale-90 group-hover:scale-100 cursor-pointer"
		>
			<Trash2 class="w-4.5 h-4.5" />
		</button>
	</div>
</div>
