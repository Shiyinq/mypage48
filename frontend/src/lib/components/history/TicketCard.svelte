<script lang="ts">
	import {
		Calendar,
		Clock,
		MapPin,
		NotebookPen,
		Pencil,
		Save,
		Trash2,
		X,
		Ticket as TicketIcon
	} from 'lucide-svelte';
	import type { Ticket } from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatCurrency } from '$lib/utils/formatting';
	import { formatDate } from '$lib/i18n';
	import { cleanseMarkdown } from '$lib/utils/markdown';
	interface Props {
		ticket: Ticket;
		onupdateNote?: (ticketId: string, note: string) => void;
		oneditTicket?: (ticket: Ticket) => void;
		ondeleteTicket?: (ticketId: string) => void;
	}

	let { ticket, onupdateNote, oneditTicket, ondeleteTicket }: Props = $props();

	const { t } = useTranslation();

	let isEditingNote = $state(false);
	let noteText = $state('');

	function startEditingNote() {
		isEditingNote = true;
		noteText = cleanseMarkdown(ticket.notes || '');
	}

	function cancelEditingNote() {
		isEditingNote = false;
		noteText = '';
	}

	function saveNote() {
		if (ticket.notes !== noteText) {
			onupdateNote?.(ticket._id, noteText);
		}
		isEditingNote = false;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			saveNote();
		}
	}
</script>

<div
	class="bg-white dark:bg-zinc-900 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-gray-100 dark:border-zinc-700 flex flex-row group animate-fade-in h-[210px] w-full"
>
	<!-- Image Section (Left) -->
	<div class="w-[140px] sm:w-[180px] h-full relative bg-gray-50 overflow-hidden flex-shrink-0">
		{#if ticket.imageUrl}
			<div class="w-full h-full relative">
				<img
					src={ticket.imageUrl}
					alt={ticket.event.title}
					class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
				/>
				<div
					class="absolute inset-0 bg-gradient-to-r from-black/60 to-transparent opacity-60"
				></div>
			</div>
		{:else}
			<div
				class="w-full h-full idol-gradient flex items-center justify-center relative overflow-hidden bg-gray-800"
			>
				<div
					class="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(255,255,255,0.2)_1px,_transparent_1px)] bg-[length:20px_20px] opacity-30"
				></div>
				<TicketIcon class="text-white opacity-20 w-16 h-16 transform -rotate-12" />
			</div>
		{/if}

		<div class="absolute top-2 left-2">
			<span
				class="inline-block px-2 py-0.5 bg-black/40 backdrop-blur-md text-white text-[10px] font-bold rounded-md uppercase tracking-wider border border-white/20 shadow-sm"
			>
				{ticket.event.day ? $t('time.days.' + ticket.event.day.toLowerCase()) : $t('history.show')}
			</span>
		</div>
	</div>

	<!-- Content Section (Right) -->
	<div class="flex-1 flex flex-col min-w-0">
		<!-- Header -->
		<div class="p-3 pb-0">
			<div class="flex justify-between items-start gap-2">
				<div class="flex-1 min-w-0">
					<div class="text-gray-400 dark:text-gray-500 font-mono text-[10px] mb-0.5 tracking-wide">
						#{ticket.ticket_id}
					</div>
					<h3
						class="font-bold text-gray-900 dark:text-gray-100 leading-tight text-sm line-clamp-3 break-words"
					>
						{ticket.event.title}
					</h3>
				</div>
				<div class="text-right flex-shrink-0">
					<span class="text-red-600 font-bold text-sm block">
						{formatCurrency(ticket.price)}
					</span>
				</div>
			</div>
		</div>

		<!-- Details Grid -->
		<div class="px-3 py-2 grid grid-cols-2 gap-x-2 gap-y-1 text-xs">
			<!-- Date & Time -->
			<div class="flex items-center text-gray-600 dark:text-gray-400">
				<Calendar class="w-3 h-3 mr-1.5 text-red-500 flex-shrink-0" />
				<span class="truncate"
					>{$formatDate(ticket.event.date, {
						day: 'numeric',
						month: 'short',
						year: '2-digit'
					})}</span
				>
			</div>

			<div class="flex items-center text-gray-600 dark:text-gray-400">
				<Clock class="w-3 h-3 mr-1.5 text-red-500 flex-shrink-0" />
				<span>{ticket.event.time}</span>
			</div>
			<!-- Seat -->
			<div class="col-span-2 flex items-center mt-1">
				<div
					class="w-5 h-5 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center mr-1.5 flex-shrink-0 text-red-600"
				>
					<MapPin class="w-2.5 h-2.5" />
				</div>
				<span class="font-bold text-gray-800 dark:text-gray-200">
					{ticket.seat.section} - {ticket.seat.number}
				</span>
			</div>
		</div>

		<!-- Notes Area (Compact) -->
		<div class="px-3 flex-1 min-h-0 flex flex-col">
			{#if isEditingNote}
				<div class="flex-1 relative animate-fade-in pb-1">
					<textarea
						bind:value={noteText}
						onkeydown={handleKeydown}
						class="w-full h-full p-2 text-xs text-gray-900 border border-gray-200 rounded-lg focus:ring-1 focus:ring-red-500 focus:border-transparent outline-none bg-yellow-50/50 resize-none"
						placeholder="Add note..."
					></textarea>
					<div class="absolute bottom-2 right-2 flex gap-1">
						<button
							onclick={cancelEditingNote}
							class="p-1 text-gray-400 hover:text-gray-600 bg-white rounded shadow-sm border border-gray-100 cursor-pointer"
						>
							<X class="w-3 h-3" />
						</button>
						<button
							onclick={saveNote}
							class="p-1 text-red-600 hover:text-red-700 bg-white rounded shadow-sm border border-red-50 cursor-pointer"
						>
							<Save class="w-3 h-3" />
						</button>
					</div>
				</div>
			{:else}
				<div
					class="group/note relative flex-1 bg-gray-50 dark:bg-zinc-800/50 rounded-lg px-2 py-1.5 border border-transparent hover:border-gray-200 dark:hover:border-zinc-700 transition-colors cursor-pointer"
					onclick={startEditingNote}
					onkeydown={(e) => e.key === 'Enter' && startEditingNote()}
					role="button"
					tabindex="0"
				>
					{#if ticket.notes}
						<p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 italic">
							"{cleanseMarkdown(ticket.notes)}"
						</p>
					{:else}
						<div
							class="h-full flex items-center text-gray-400 dark:text-gray-600 italic text-[10px]"
						>
							<NotebookPen class="w-3 h-3 mr-1 opacity-50" />
							{$t('history.addNote')}
						</div>
					{/if}
					<div
						class="absolute top-1 right-1 opacity-0 group-hover/note:opacity-100 transition-opacity"
					>
						<Pencil class="w-3 h-3 text-gray-400" />
					</div>
				</div>
			{/if}
		</div>

		<!-- Footer Actions -->
		<div
			class="px-3 py-2 flex justify-between items-center border-t border-gray-50 dark:border-zinc-800 mt-1"
		>
			<button
				onclick={() => oneditTicket?.(ticket)}
				class="text-[10px] font-bold text-gray-500 hover:text-red-600 flex items-center gap-1 transition-colors cursor-pointer"
			>
				<Pencil class="w-3 h-3" />
				{$t('history.editDetails')}
			</button>
			<button
				onclick={() => ondeleteTicket?.(ticket._id)}
				class="text-gray-400 hover:text-red-600 transition-colors cursor-pointer"
			>
				<Trash2 class="w-3.5 h-3.5" />
			</button>
		</div>
	</div>
</div>
