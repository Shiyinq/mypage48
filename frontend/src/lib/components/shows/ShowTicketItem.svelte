<script lang="ts">
	import { Calendar, MapPin, Trash2, Ticket as TicketIcon } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { OptimizedImage } from '$lib/components/common';
	import type { Ticket } from '$lib/types';

	interface Props {
		ticket: Ticket;
		onDelete: (id: string) => void;
	}

	let { ticket, onDelete }: Props = $props();

	const { t } = useTranslation();
</script>

<div
	class="glass-panel p-4 rounded-2xl flex gap-4 transition-all hover:bg-white/80 dark:hover:bg-zinc-800/80"
>
	<div class="w-20 h-20 rounded-xl bg-gray-100 dark:bg-zinc-800 flex-shrink-0 overflow-hidden">
		{#if ticket.imageUrl}
			<OptimizedImage
				src={ticket.imageUrl}
				srcMedium={ticket.imageUrl_medium}
				srcSmall={ticket.imageUrl_small}
				blurHash={ticket.blurHash}
				alt={ticket.event.title}
				class="w-full h-full object-cover"
				sizes="80px"
			/>
		{:else}
			<div class="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-600">
				<TicketIcon class="w-8 h-8" />
			</div>
		{/if}
	</div>
	<div class="flex-1 min-w-0">
		<h3 class="font-bold text-gray-800 dark:text-gray-200 truncate">
			{ticket.event.title}
		</h3>
		<div class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2 mt-1">
			<Calendar class="w-3 h-3" />
			{ticket.event.date}
		</div>
		<div class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2 mt-0.5">
			<MapPin class="w-3 h-3" />
			{t('shows.row')}
			{ticket.seat.section}-{ticket.seat.number}
		</div>
		<div class="mt-2 font-bold text-red-600 dark:text-red-500 text-sm">
			IDR {ticket.price.toLocaleString()}
		</div>
	</div>
	<div class="flex flex-col justify-center">
		<button
			onclick={() => onDelete(ticket._id)}
			class="p-2 text-gray-300 dark:text-gray-600 hover:text-red-600 dark:hover:text-red-500 transition-colors cursor-pointer"
			><Trash2 class="w-5 h-5" /></button
		>
	</div>
</div>
