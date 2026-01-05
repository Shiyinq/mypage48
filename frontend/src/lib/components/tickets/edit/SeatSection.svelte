<script lang="ts">
	import { MapPin, DollarSign, Hash, ChevronDown } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let formData: any;
	export let rowOptions: readonly string[];

	const { t } = useTranslation();
</script>

<div class="space-y-4 pt-4 border-t border-gray-100 dark:border-zinc-700">
	<h3
		class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2"
	>
		<MapPin class="w-4 h-4" />
		{$t('forms.seatPayment')}
	</h3>
	<div class="grid grid-cols-3 gap-4">
		<div>
			<label
				class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
				for="seat-section">{$t('forms.row')}</label
			>
			<div class="relative">
				<select
					id="seat-section"
					bind:value={formData.seat.section}
					class="w-full p-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-center font-black text-lg text-gray-900 dark:text-gray-100 appearance-none cursor-pointer"
				>
					<option value="" disabled>-</option>
					{#each rowOptions as r}<option value={r}>{r}</option>{/each}
				</select>
				<ChevronDown
					class="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-300 pointer-events-none"
				/>
			</div>
		</div>
		<div class="col-span-2">
			<label
				class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
				for="seat-number">{$t('forms.seatNumber')}</label
			>
			<input
				id="seat-number"
				type="number"
				bind:value={formData.seat.number}
				class="w-full p-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-center font-black text-lg text-gray-900 dark:text-gray-100 placeholder-gray-300 dark:placeholder-gray-600"
			/>
		</div>
	</div>
	<div class="grid grid-cols-2 gap-4">
		<div>
			<label
				class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
				for="ticket-price">{$t('forms.price')}</label
			>
			<div class="relative">
				<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
					<DollarSign class="w-4 h-4" />
				</div>
				<input
					id="ticket-price"
					type="number"
					bind:value={formData.price}
					class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-gray-100"
				/>
			</div>
		</div>
		<div>
			<label
				class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
				for="ticket-id">{$t('forms.ticketId')}</label
			>
			<div class="relative">
				<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
					<Hash class="w-4 h-4" />
				</div>
				<input
					id="ticket-id"
					type="text"
					bind:value={formData.ticket_id}
					class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
					placeholder="T123456"
				/>
			</div>
		</div>
	</div>
</div>
