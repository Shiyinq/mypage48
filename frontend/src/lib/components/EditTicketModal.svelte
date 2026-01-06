<script lang="ts">
	import { ticketsStore, showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { invalidateDashboard } from '$lib/stores/dashboard';
	import { invalidateTheater } from '$lib/stores/theater';
	import { validateImageFile, getValidationErrorI18nKey } from '$lib/utils/fileValidation';
	import { calculateDayFromDate, calculateGateOpenTime } from '$lib/utils/ticketUtils';
	import ValidationAlertModal from '$lib/components/ValidationAlertModal.svelte';
	import type { Ticket } from '$lib/types';
	import { LoaderCircle, CircleCheck, NotebookPen } from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { SHOW_IMAGES, THEATER_ROWS } from '$lib/constants';

	// Sub-components
	import ImagePreview from './tickets/edit/ImagePreview.svelte';
	import EventSection from './tickets/edit/EventSection.svelte';
	import SeatSection from './tickets/edit/SeatSection.svelte';
	import TwoShotSection from './tickets/edit/TwoShotSection.svelte';

	export let ticket: Ticket;

	const dispatch = createEventDispatcher();
	const { t } = useTranslation();
	const SHOW_OPTIONS = SHOW_IMAGES.map((s) => s.title);
	const ROW_OPTIONS = THEATER_ROWS;

	let isSubmitting = false;
	let fileInputRef: HTMLInputElement;
	let twoShotInputRef: HTMLInputElement;

	// State
	let formData = {
		event: { ...ticket.event },
		seat: { ...ticket.seat },
		ticket_id: ticket.ticket_id,
		price: ticket.price,
		currency: ticket.currency,
		notes: ticket.notes || '',
		rules: { ...ticket.rules },
		two_shot: ticket.two_shot
			? { ...ticket.two_shot }
			: {
					imageUrl: '',
					member_name: '',
					type: 'Roulette' as 'Roulette' | 'Birthday',
					price: 100000
				}
	};

	let image: string | null = ticket.imageUrl || null;
	let showTwoShot = !!ticket.two_shot;
	let twoShotImage: string | null = ticket.two_shot?.imageUrl || null;

	// Validation alert modal state
	let showValidationAlert = false;
	let validationAlertMessage = '';

	// Validation
	$: isFormValid =
		formData.event.title &&
		formData.event.date &&
		formData.event.time &&
		formData.seat.section &&
		formData.seat.number &&
		formData.price > 0 &&
		formData.ticket_id &&
		(!showTwoShot || (showTwoShot && formData.two_shot.member_name));

	// Reactive Day Calculation
	$: if (formData.event.date) {
		const newDay = calculateDayFromDate(formData.event.date);
		if (newDay && newDay !== formData.event.day) {
			formData.event.day = newDay;
			formData = { ...formData }; // Force update
		}
	}

	// Reactive Gate Open Calculation (30 mins before Show Time)
	$: if (formData.event.time) {
		const newGateOpen = calculateGateOpenTime(formData.event.time);
		if (newGateOpen && newGateOpen !== formData.event.gate_open) {
			formData.event.gate_open = newGateOpen;
			formData = { ...formData }; // Force update
		}
	}

	// Handlers
	const handleFileChange = (e: Event) => {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		// Validate file before processing
		const validation = validateImageFile(file);
		if (!validation.valid) {
			validationAlertMessage = $t(getValidationErrorI18nKey(validation.error));
			showValidationAlert = true;
			target.value = ''; // Reset input
			return;
		}

		const reader = new FileReader();
		reader.onloadend = () => {
			image = reader.result as string;
		};
		reader.readAsDataURL(file);
	};

	const handleTwoShotFileChange = (e: Event) => {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		// Validate file before processing
		const validation = validateImageFile(file);
		if (!validation.valid) {
			validationAlertMessage = $t(getValidationErrorI18nKey(validation.error));
			showValidationAlert = true;
			target.value = ''; // Reset input
			return;
		}

		const reader = new FileReader();
		reader.onloadend = () => {
			twoShotImage = reader.result as string;
		};
		reader.readAsDataURL(file);
	};

	const handleSubmit = async () => {
		isSubmitting = true;
		try {
			const payload = {
				ticket_id: formData.ticket_id,
				event: formData.event,
				seat: { ...formData.seat, number: Number(formData.seat.number) },
				price: Number(formData.price),
				currency: 'IDR',
				rules: formData.rules,
				imageUrl: image || undefined,
				notes: formData.notes,
				two_shot: showTwoShot
					? {
							imageUrl: twoShotImage || undefined,
							member_name: formData.two_shot.member_name,
							type: formData.two_shot.type,
							price: Number(formData.two_shot.price)
						}
					: null
			};

			const updated = await ticketsStore.updateTicket(ticket._id, payload);

			// Invalidate dashboard and theater cache
			invalidateDashboard();
			invalidateTheater();

			showToast($t('forms.ticketUpdateSuccess'));
			dispatch('save', updated);
			dispatch('close');
		} catch (e) {
			logger.error('Failed to update ticket', e, { context: 'EditTicketModal' });
			showToast($t('forms.ticketUpdateError'), 'error');
		} finally {
			isSubmitting = false;
		}
	};
</script>

<div class="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6">
	<!-- Backdrop -->
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div
		class="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity duration-300"
		on:click={() => dispatch('close')}
	></div>

	<!-- Modal Content -->
	<div
		class="bg-white/95 dark:bg-zinc-900/95 backdrop-blur-xl w-full max-w-5xl h-[90vh] rounded-3xl shadow-2xl overflow-y-auto custom-scrollbar relative z-10 animate-fade-in"
	>
		<div class="max-w-5xl mx-auto p-4 md:p-8 pb-24">
			<!-- Header -->
			<div class="flex items-center justify-between mb-6">
				<div class="flex items-center gap-3">
					<div
						class="p-3 rounded-2xl bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 shadow-lg shadow-red-100 dark:shadow-red-900/20 border-2 border-white dark:border-zinc-700 transform -rotate-6"
					>
						<NotebookPen class="w-6 h-6" />
					</div>
					<div>
						<h2 class="text-2xl font-bold text-themed leading-none relative w-fit">
							{$t('forms.editTicket')}
							<span
								class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 dark:bg-red-500/30 -z-10 transform -skew-x-12 rounded-sm"
							></span>
						</h2>
					</div>
				</div>

				<button
					on:click={() => dispatch('close')}
					class="text-sm font-bold text-gray-500 dark:text-gray-400 hover:text-red-600 bg-white dark:bg-zinc-800 px-4 py-2 rounded-full shadow-sm border border-gray-200 dark:border-zinc-700 cursor-pointer"
				>
					{$t('forms.cancel')}
				</button>
			</div>

			<div class="grid gap-8 lg:grid-cols-2">
				<!-- Left: Image Preview -->
				<ImagePreview {image} onSelect={() => fileInputRef.click()} />

				<!-- Right: Form -->
				<div
					class="bg-white/80 dark:bg-zinc-800/80 backdrop-blur-xl p-6 md:p-8 rounded-3xl border border-white/50 dark:border-zinc-700 shadow-xl h-fit"
				>
					<form on:submit|preventDefault={handleSubmit} class="space-y-8">
						<!-- Event Details -->
						<EventSection {formData} showOptions={SHOW_OPTIONS} />

						<!-- Seat & Payment -->
						<SeatSection {formData} rowOptions={ROW_OPTIONS} />

						<!-- 2-Shot -->
						<TwoShotSection
							bind:showTwoShot
							{twoShotImage}
							{formData}
							onSelectImage={() => twoShotInputRef.click()}
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

						<div class="pt-4">
							<button
								type="submit"
								disabled={isSubmitting || !isFormValid}
								class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.01] transition-all flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed disabled:shadow-none disabled:transform-none"
							>
								{#if isSubmitting}
									<LoaderCircle class="w-6 h-6 animate-spin" />
								{:else}
									<CircleCheck class="w-6 h-6" />
								{/if}
								{$t('forms.updateTicket')}
							</button>
						</div>
					</form>
				</div>
			</div>
		</div>
	</div>
</div>

<input
	type="file"
	bind:this={fileInputRef}
	class="hidden"
	accept="image/*"
	on:change={handleFileChange}
/>
<input
	type="file"
	bind:this={twoShotInputRef}
	class="hidden"
	accept="image/*"
	on:change={handleTwoShotFileChange}
/>

<!-- Validation Alert Modal -->
<ValidationAlertModal
	show={showValidationAlert}
	title={$t('validation.alert.title')}
	message={validationAlertMessage}
	onClose={() => (showValidationAlert = false)}
/>
