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
	import { formatCurrency, formatDateFull } from '$lib/utils/formatting';
	import { createEventDispatcher } from 'svelte';

	export let ticket: Ticket;

	const { t } = useTranslation();
	const dispatch = createEventDispatcher();

	let isEditingNote = false;
	let noteText = '';

	function startEditingNote() {
		isEditingNote = true;
		noteText = ticket.notes || '';
	}

	function cancelEditingNote() {
		isEditingNote = false;
		noteText = '';
	}

	function saveNote() {
		if (ticket.notes !== noteText) {
			dispatch('updateNote', { ticketId: ticket._id, note: noteText });
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
	class="bg-white dark:bg-zinc-900 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-gray-100 dark:border-zinc-700 flex flex-col group animate-fade-in h-full"
>
	<!-- Image Section -->
	<div class="h-48 w-full relative bg-gray-50 overflow-hidden flex-shrink-0">
		{#if ticket.imageUrl}
			<div class="w-full h-full relative">
				<img
					src={ticket.imageUrl}
					alt={ticket.event.title}
					class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
				/>
				<div
					class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-90"
				></div>
			</div>
		{:else}
			<div
				class="w-full h-full idol-gradient flex items-center justify-center relative overflow-hidden bg-gray-800"
			>
				<div
					class="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(255,255,255,0.2)_1px,_transparent_1px)] bg-[length:20px_20px] opacity-30"
				></div>
				<TicketIcon class="text-white opacity-20 w-24 h-24 transform -rotate-12" />
			</div>
		{/if}

		<div class="absolute top-3 left-3">
			<span
				class="inline-block px-3 py-1 bg-black/30 backdrop-blur-md text-white text-[10px] font-bold rounded-full uppercase tracking-wider border border-white/20 shadow-lg"
			>
				{ticket.event.day ? $t('time.days.' + ticket.event.day.toLowerCase()) : $t('history.show')}
			</span>
		</div>

		<div class="absolute bottom-0 left-0 right-0 p-5">
			<div class="text-white/80 font-mono text-xs mb-1 tracking-wide">
				#{ticket.ticket_id}
			</div>
			<h3 class="font-bold text-white leading-tight text-xl line-clamp-2 drop-shadow-md">
				{ticket.event.title}
			</h3>
		</div>
	</div>

	<!-- Body -->
	<div class="p-5 flex-1 flex flex-col gap-4">
		<div class="grid grid-cols-2 gap-4">
			<div class="flex flex-col">
				<span class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase mb-1"
					>{$t('history.date')}</span
				>
				<div class="flex items-center text-gray-700 dark:text-gray-300 text-sm font-semibold">
					<Calendar class="w-3.5 h-3.5 mr-1.5 text-red-500" />
					{formatDateFull(ticket.event.date)}
				</div>
			</div>
			<div class="flex flex-col">
				<span class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase mb-1"
					>{$t('history.time')}</span
				>
				<div class="flex items-center text-gray-700 dark:text-gray-300 text-sm font-semibold">
					<Clock class="w-3.5 h-3.5 mr-1.5 text-red-500" />
					{ticket.event.time}
				</div>
			</div>
		</div>

		<div
			class="bg-red-50 dark:bg-red-900/20 rounded-xl p-3 border border-red-100 dark:border-red-500/30 flex items-center justify-between"
		>
			<div class="flex items-center gap-3">
				<div
					class="w-8 h-8 rounded-full bg-white flex items-center justify-center shadow-sm text-red-600"
				>
					<MapPin class="w-4 h-4" />
				</div>
				<div class="flex flex-col">
					<span class="text-[10px] text-red-400 dark:text-red-300 font-bold uppercase"
						>{$t('history.seat')}</span
					>
					<span class="text-gray-900 dark:text-gray-100 font-extrabold text-sm"
						>{ticket.seat.section} - {ticket.seat.number}</span
					>
				</div>
			</div>
			<div class="text-right">
				<span class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase block mb-0.5"
					>{$t('history.price')}</span
				>
				<span class="text-red-600 font-bold text-sm">
					{formatCurrency(ticket.price)}
				</span>
			</div>
		</div>

		<!-- Notes -->
		<div class="flex-1">
			<div class="flex items-center justify-between mb-2">
				<span
					class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase flex items-center gap-1"
				>
					<NotebookPen class="w-3 h-3" />
					{$t('history.notes')}
				</span>
				{#if !isEditingNote}
					<button
						on:click={startEditingNote}
						class="text-xs text-red-500 hover:text-red-700 font-medium flex items-center gap-1"
					>
						{#if ticket.notes}
							<Pencil class="w-3 h-3" /> {$t('history.editNote')}
						{:else}
							<NotebookPen class="w-3 h-3" /> {$t('history.addNote')}
						{/if}
					</button>
				{/if}
			</div>

			{#if isEditingNote}
				<div class="animate-fade-in">
					<textarea
						bind:value={noteText}
						on:keydown={handleKeydown}
						class="w-full p-3 text-sm text-gray-900 border border-gray-200 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none bg-yellow-50/50 min-h-[80px]"
						placeholder="Write about your experience..."
					></textarea>
					<div class="flex justify-end gap-2 mt-2">
						<button
							on:click={cancelEditingNote}
							class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
						>
							<X class="w-4 h-4" />
						</button>
						<button
							on:click={saveNote}
							class="px-3 py-1.5 bg-red-600 text-white text-xs font-bold rounded-md hover:bg-red-700 transition-colors flex items-center gap-1"
						>
							<Save class="w-3 h-3" />
							{$t('history.saveNote')}
						</button>
					</div>
				</div>
			{:else}
				<div
					class="bg-yellow-50/50 dark:bg-zinc-800/50 rounded-lg p-3 border border-yellow-100/50 dark:border-zinc-600 min-h-[60px]"
				>
					{#if ticket.notes}
						<p
							class="text-sm text-gray-900 dark:text-gray-200 whitespace-pre-wrap font-light italic leading-relaxed line-clamp-3"
						>
							"{ticket.notes}"
						</p>
					{:else}
						<p class="text-xs text-gray-400 dark:text-gray-500 italic">
							{$t('history.noNotes')}
						</p>
					{/if}
				</div>
			{/if}
		</div>
	</div>

	<div
		class="px-5 py-3 border-t border-gray-100 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800/50 flex justify-between items-center mt-auto"
	>
		<button
			on:click={() => dispatch('editTicket', ticket)}
			class="text-xs font-bold text-gray-900 dark:text-gray-200 hover:text-red-600 flex items-center gap-1 px-2 py-1 rounded-md hover:bg-white dark:hover:bg-zinc-700 transition-colors cursor-pointer"
		>
			<Pencil class="w-3 h-3" />
			{$t('history.editDetails')}
		</button>
		<button
			on:click={() => dispatch('deleteTicket', ticket._id)}
			class="text-gray-400 hover:text-red-600 transition-colors p-2 hover:bg-white rounded-full border border-transparent hover:border-red-100 hover:shadow-sm cursor-pointer"
		>
			<Trash2 class="w-4 h-4" />
		</button>
	</div>
</div>
