<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';
	import { setlistsStore } from '$lib/stores/theater.svelte';
	import {
		Ticket as TicketIcon,
		Calendar,
		Clock,
		MapPin,
		DollarSign,
		Hash,
		NotebookPen,
		ChevronDown,
		LoaderCircle,
		CircleCheck
	} from 'lucide-svelte';
	import { SHOW_IMAGES, THEATER_ROWS } from '$lib/constants';
	import TwoShotSection from './TwoShotSection.svelte';

	interface Props {
		formData: {
			event: {
				title: string;
				date: string;
				time: string;
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				[key: string]: any;
			};
			seat: {
				section: string;
				number: string;
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				[key: string]: any;
			};
			ticket_id: string;
			price: number;
			notes: string;
			two_shot: {
				member_name: string;
				type: 'Roulette' | 'Birthday';
				price: number;
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				[key: string]: any;
			};
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			[key: string]: any;
		};
		isSubmitting?: boolean;
		isFormValid?: boolean;
		// 2-Shot props
		showTwoShot?: boolean;
		twoShotImage?: string | null;
		onsubmit?: () => void;
		onclick?: () => void;
		onphotoClick?: () => void;
		ondrop?: (file: File) => void;
	}

	let {
		formData = $bindable(),
		isSubmitting = $bindable(false),
		isFormValid = false,
		showTwoShot = $bindable(false),
		twoShotImage = $bindable(null),
		onsubmit,
		onclick,
		onphotoClick,
		ondrop
	}: Props = $props();

	const { t } = useTranslation();

	let SHOW_OPTIONS = $derived(
		setlistsStore.data ? setlistsStore.data.map((s) => s.title) : SHOW_IMAGES.map((s) => s.title)
	);

	onMount(() => {
		setlistsStore.load();
	});

	const ROW_OPTIONS = THEATER_ROWS;
</script>

<div
	class="bg-white/80 dark:bg-zinc-800/80 backdrop-blur-xl p-4 sm:p-6 md:p-8 rounded-3xl border border-white/50 dark:border-zinc-700 shadow-xl h-fit"
>
	<form
		onsubmit={(e) => {
			e.preventDefault();
			onsubmit?.();
		}}
		class="space-y-8"
	>
		<!-- Event Details -->
		<div class="space-y-4">
			<h3
				class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2"
			>
				<TicketIcon class="w-4 h-4" />
				{$t('forms.eventDetails')}
			</h3>
			<div>
				<label
					class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
					for="event-title">{$t('forms.showTitle')}</label
				>
				<div class="relative group">
					<div
						class="absolute left-3 top-1/2 -translate-y-1/2 text-red-400 z-10 pointer-events-none"
					>
						<TicketIcon class="w-5 h-5" />
					</div>
					<select
						id="event-title"
						bind:value={formData.event.title}
						class="w-full pl-10 pr-10 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none font-bold text-gray-900 dark:text-gray-100 transition-all appearance-none cursor-pointer"
					>
						<option value="" disabled>{$t('forms.selectSetlist')}</option>
						{#each SHOW_OPTIONS as show}<option value={show}>{show}</option>{/each}
					</select>
					<ChevronDown
						class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
					/>
				</div>
			</div>
			<div class="grid grid-cols-2 gap-4">
				<div>
					<label
						class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
						for="event-date">{$t('forms.date')}</label
					>
					<div class="relative">
						<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
							<Calendar class="w-4 h-4" />
						</div>
						<input
							id="event-date"
							type="date"
							bind:value={formData.event.date}
							class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
						/>
					</div>
				</div>
				<div>
					<label
						class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
						for="event-time">{$t('forms.showTime')}</label
					>
					<div class="relative">
						<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
							<Clock class="w-4 h-4" />
						</div>
						<input
							id="event-time"
							type="time"
							bind:value={formData.event.time}
							class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
						/>
					</div>
				</div>
			</div>
		</div>

		<!-- Seat & Price -->
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
							{#each ROW_OPTIONS as r}<option value={r}>{r}</option>{/each}
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
						placeholder="1"
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
							placeholder="200000"
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

		<!-- 2-Shot -->
		<TwoShotSection
			bind:showTwoShot
			{twoShotImage}
			bind:memberName={formData.two_shot.member_name}
			bind:twoShotType={formData.two_shot.type}
			bind:twoShotPrice={formData.two_shot.price}
			onphotoClick={() => onphotoClick?.()}
			ondrop={(file) => ondrop?.(file)}
		/>

		<!-- Notes -->
		<div class="space-y-4 pt-4 border-t border-gray-100 dark:border-zinc-700">
			<h3
				class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2"
			>
				<NotebookPen class="w-4 h-4" />
				{$t('forms.experienceLog')}
			</h3>
			<textarea
				bind:value={formData.notes}
				class="w-full p-4 bg-yellow-50/50 dark:bg-zinc-800/50 border border-yellow-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-yellow-400 dark:focus:ring-zinc-600 outline-none text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 min-h-[120px]"
				placeholder={$t('forms.notesPlaceholder')}
			></textarea>
		</div>

		<button
			type="submit"
			onclick={() => onclick?.()}
			disabled={isSubmitting || !isFormValid}
			class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.01] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer disabled:shadow-none disabled:transform-none"
		>
			{#if isSubmitting}
				<LoaderCircle class="w-6 h-6 animate-spin" />
			{:else}
				<CircleCheck class="w-6 h-6" />
			{/if}
			{$t('forms.saveTicket')}
		</button>
	</form>
</div>
