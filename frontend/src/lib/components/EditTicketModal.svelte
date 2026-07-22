<script lang="ts">
	import { ticketsStore, showToast, storageStore } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { invalidateDashboard } from '$lib/stores/dashboard.svelte';
	import { invalidateTheater } from '$lib/stores/theater.svelte';
	import { invalidateMemories } from '$lib/stores/memories.svelte';
	import { validateImageFile, getValidationErrorI18nKey } from '$lib/utils/fileValidation';
	import { calculateDayFromDate, calculateGateOpenTime } from '$lib/utils/ticketUtils';
	import ValidationAlertModal from '$lib/components/ValidationAlertModal.svelte';
	import type { Ticket } from '$lib/types';
	import { LoaderCircle, CircleCheck, NotebookPen } from 'lucide-svelte';
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { THEATER_ROWS } from '$lib/constants';
	import { setlistsStore } from '$lib/stores/theater.svelte';
	import { cleanseMarkdown, cleanseStorageUrl } from '$lib/utils/markdown';
	import { getErrorMessage } from '$lib/utils/api';
	import { portal } from '$lib/actions/portal';

	// Sub-components
	import ImagePreview from './tickets/edit/ImagePreview.svelte';
	import EventSection from './tickets/edit/EventSection.svelte';
	import SeatSection from './tickets/edit/SeatSection.svelte';
	import TwoShotSection from './tickets/edit/TwoShotSection.svelte';
	import ImageCropperModal from '$lib/components/common/ImageCropperModal.svelte';

	interface Props {
		ticket: Ticket;
		onclose?: () => void;
		onsave?: (updated: Ticket) => void;
	}

	let { ticket, onclose, onsave }: Props = $props();

	const { t } = useTranslation();

	onMount(() => {
		setlistsStore.loadOptions();
		const originalOverflow = document.body.style.overflow;
		document.body.style.overflow = 'hidden';
		return () => {
			document.body.style.overflow = originalOverflow;
		};
	});

	const ROW_OPTIONS = THEATER_ROWS;

	let isSubmitting = $state(false);
	let fileInputRef: HTMLInputElement | undefined = $state();
	let twoShotInputRef: HTMLInputElement | undefined = $state();

	// State
	let formData = $state({
		event: { title: '', date: '', day: '', time: '', gate_open: '', venue: '' },
		seat: { section: '', number: '' as string | number },
		ticket_id: '',
		price: 0,
		currency: 'IDR',
		notes: '',
		rules: { refund_allowed: false, exchange_allowed: false },
		two_shot: {
			imageUrl: '',
			member_name: '',
			type: 'Roulette' as 'Roulette' | 'Birthday',
			price: 100000
		}
	});

	let image: string | null = $state(null);
	let showTwoShot = $state(false);
	let twoShotImage: string | null = $state(null);

	// Sync form data when ticket changes
	$effect(() => {
		formData = {
			event: { ...ticket.event, gate_open: ticket.event.gate_open ?? '' },
			seat: { ...ticket.seat },
			ticket_id: ticket.ticket_id,
			price: ticket.price,
			currency: ticket.currency,
			notes: cleanseMarkdown(ticket.notes || ''),
			rules: { ...ticket.rules },
			two_shot: ticket.two_shot
				? { ...ticket.two_shot, imageUrl: ticket.two_shot.imageUrl ?? '' }
				: {
						imageUrl: '',
						member_name: '',
						type: 'Roulette' as 'Roulette' | 'Birthday',
						price: 100000
					}
		};
		image = ticket.imageUrl || null;
		showTwoShot = !!ticket.two_shot;
		twoShotImage = ticket.two_shot?.imageUrl || null;
	});

	// Validation alert modal state
	let showValidationAlert = $state(false);
	let validationAlertMessage = $state('');

	// Cropper state
	let cropTarget = $state<'TICKET' | 'TWOSHOT' | null>(null);
	let imageToCrop = $state<string | null>(null);

	// Validation
	let isFormValid = $derived(
		!!(
			formData.event.title &&
			formData.event.date &&
			formData.event.time &&
			formData.seat.section &&
			formData.seat.number &&
			formData.price > 0 &&
			formData.ticket_id &&
			(!showTwoShot ||
				(showTwoShot &&
					formData.two_shot.member_name &&
					formData.two_shot.price !== null &&
					formData.two_shot.price >= 0))
		)
	);

	// Reactive Day Calculation
	$effect(() => {
		if (formData.event.date) {
			const newDay = calculateDayFromDate(formData.event.date);
			if (newDay && newDay !== formData.event.day) {
				formData.event.day = newDay;
				formData = { ...formData }; // Force update
			}
		}
	});

	// Reactive Gate Open Calculation (30 mins before Show Time)
	$effect(() => {
		if (formData.event.time) {
			const newGateOpen = calculateGateOpenTime(formData.event.time);
			if (newGateOpen && newGateOpen !== formData.event.gate_open) {
				formData.event.gate_open = newGateOpen;
				formData = { ...formData }; // Force update
			}
		}
	});

	// Handlers
	const processFile = (file: File) => {
		// Validate file before processing
		const validation = validateImageFile(file);
		if (!validation.valid) {
			validationAlertMessage = t(getValidationErrorI18nKey(validation.error));
			showValidationAlert = true;
			return;
		}

		const reader = new FileReader();
		reader.onloadend = () => {
			image = reader.result as string;
		};
		reader.readAsDataURL(file);
	};

	const handleFileChange = (e: Event) => {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		// Skip basic read and push to cropper instead if desired, but we already have `processFile`
		// which sets `image` state directly. To be consistent with upload, we can let them select existing for crop.
		processFile(file);
		target.value = ''; // Reset input
	};

	const handleEditTicketImage = () => {
		if (image) {
			imageToCrop = image;
			cropTarget = 'TICKET';
		}
	};

	const handleEditTwoShotImage = () => {
		if (twoShotImage) {
			imageToCrop = twoShotImage;
			cropTarget = 'TWOSHOT';
		}
	};

	const handleCropSave = (croppedBase64: string) => {
		if (cropTarget === 'TICKET') {
			image = croppedBase64;
		} else if (cropTarget === 'TWOSHOT') {
			twoShotImage = croppedBase64;
		}
		cropTarget = null;
		imageToCrop = null;
	};

	const handleCropCancel = () => {
		cropTarget = null;
		imageToCrop = null;
	};

	// Helper to check if image is base64 (new upload) vs storage filename
	const isBase64Image = (value: string | null): boolean => {
		if (!value) return false;
		return value.startsWith('data:image/');
	};

	const processTwoShotFile = (file: File) => {
		// Validate file before processing
		const validation = validateImageFile(file);
		if (!validation.valid) {
			validationAlertMessage = t(getValidationErrorI18nKey(validation.error));
			showValidationAlert = true;
			return;
		}

		const reader = new FileReader();
		reader.onloadend = () => {
			twoShotImage = reader.result as string;
		};
		reader.readAsDataURL(file);
	};

	const handleTwoShotFileChange = (e: Event) => {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;
		processTwoShotFile(file);
		target.value = ''; // Reset input
	};

	const handleTwoShotDrop = (file: File) => {
		processTwoShotFile(file);
	};

	const handleSubmit = async () => {
		isSubmitting = true;
		try {
			// Upload new images to storage
			let ticketImageUrl: string | undefined;
			let ticketBlurHash: string | undefined;
			let twoShotImageUrl: string | undefined;
			let twoShotBlurHash: string | undefined;

			if (image) {
				if (isBase64Image(image)) {
					// New image - upload to storage
					const uploadResult = await storageStore.uploadImage(image, 'ticket');
					ticketImageUrl = uploadResult.filename;
					ticketBlurHash = uploadResult.blurHash;
				} else {
					// Existing storage filename - keep as-is
					ticketImageUrl = image;
					ticketBlurHash = ticket.blurHash;
				}
			}

			if (showTwoShot && twoShotImage) {
				if (isBase64Image(twoShotImage)) {
					// New image - upload to storage
					const uploadResult = await storageStore.uploadImage(twoShotImage, 'twoshot');
					twoShotImageUrl = uploadResult.filename;
					twoShotBlurHash = uploadResult.blurHash;
				} else {
					// Existing storage filename - keep as-is
					twoShotImageUrl = twoShotImage;
					twoShotBlurHash = ticket.two_shot?.blurHash;
				}
			}

			const payload = {
				ticket_id: formData.ticket_id,
				event: formData.event,
				seat: { ...formData.seat, number: Number(formData.seat.number) },
				price: Number(formData.price),
				currency: 'IDR',
				rules: formData.rules,
				imageUrl: ticketImageUrl ? cleanseStorageUrl(ticketImageUrl) : null,
				blurHash: image ? ticketBlurHash : null,
				notes: cleanseMarkdown(formData.notes),
				two_shot: showTwoShot
					? {
							imageUrl: twoShotImageUrl ? cleanseStorageUrl(twoShotImageUrl) : null,
							blurHash: twoShotImage ? twoShotBlurHash : null,
							member_name: formData.two_shot.member_name,
							type: formData.two_shot.type,
							price: Number(formData.two_shot.price)
						}
					: null
			};

			const updated = await ticketsStore.updateTicket(
				ticket._id,
				payload as unknown as Partial<Ticket>
			);

			// Invalidate dashboard, theater, and memories cache
			invalidateDashboard();
			invalidateTheater();
			invalidateMemories();

			showToast(t('forms.ticketUpdateSuccess'));
			onsave?.(updated);
			onclose?.();
		} catch (e) {
			logger.error('Failed to update ticket', e, { context: 'EditTicketModal' });
			const errorMessage = getErrorMessage(e);
			showToast(errorMessage || t('forms.ticketUpdateError'), 'error');
		} finally {
			isSubmitting = false;
		}
	};
</script>

<div use:portal class="fixed inset-0 z-[1000] flex items-center justify-center p-4 sm:p-6">
	<!-- Backdrop -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="absolute inset-0 bg-black/90 transition-opacity duration-300"
		onclick={() => onclose?.()}
	></div>

	<!-- Modal Content -->
	<div
		class="bg-white dark:bg-zinc-900 w-full max-w-5xl h-[90vh] rounded-3xl shadow-2xl overflow-y-auto custom-scrollbar relative z-10 animate-fade-in"
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
							{t('forms.editTicket')}
							<span
								class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 dark:bg-red-500/30 -z-10 transform -skew-x-12 rounded-sm"
							></span>
						</h2>
					</div>
				</div>

				<button
					onclick={() => onclose?.()}
					class="text-sm font-bold text-gray-500 dark:text-gray-400 hover:text-red-600 bg-white dark:bg-zinc-800 px-4 py-2 rounded-full shadow-sm border border-gray-200 dark:border-zinc-700 cursor-pointer"
				>
					{t('forms.cancel')}
				</button>
			</div>

			<div class="grid gap-8 lg:grid-cols-2">
				<!-- Left: Image Preview -->
				<ImagePreview
					{image}
					onSelect={() => {
						fileInputRef?.click();
					}}
					onEdit={handleEditTicketImage}
					onDelete={() => {
						image = null;
					}}
				/>

				<!-- Right: Form -->
				<div
					class="bg-white/80 dark:bg-zinc-800/80 backdrop-blur-xl p-6 md:p-8 rounded-3xl border border-white/50 dark:border-zinc-700 shadow-xl h-fit"
				>
					<form
						onsubmit={(e) => {
							e.preventDefault();
							handleSubmit();
						}}
						class="space-y-8"
					>
						<!-- Event Details -->
						<EventSection
							bind:title={formData.event.title}
							bind:date={formData.event.date}
							bind:time={formData.event.time}
						/>

						<!-- Seat & Payment -->
						<SeatSection
							bind:section={formData.seat.section}
							bind:number={formData.seat.number}
							bind:price={formData.price}
							bind:ticket_id={formData.ticket_id}
							rowOptions={ROW_OPTIONS}
						/>

						<!-- 2-Shot -->
						<TwoShotSection
							bind:showTwoShot
							{twoShotImage}
							bind:memberName={formData.two_shot.member_name}
							bind:type={formData.two_shot.type}
							bind:price={formData.two_shot.price}
							onSelectImage={() => twoShotInputRef?.click()}
							onEdit={handleEditTwoShotImage}
							onDelete={() => {
								twoShotImage = null;
							}}
							ondrop={handleTwoShotDrop}
						/>

						<!-- Notes -->
						<div class="space-y-4 pt-4 border-t border-gray-100 dark:border-zinc-700">
							<label
								for="edit-ticket-notes"
								class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2 cursor-pointer"
							>
								<NotebookPen class="w-4 h-4" />
								{t('forms.experienceLog')}
								<span class="text-[10px] text-gray-400/70 font-medium normal-case tracking-normal"
									>({t('forms.optional')})</span
								>
							</label>
							<textarea
								id="edit-ticket-notes"
								name="notes"
								bind:value={formData.notes}
								class="w-full p-4 bg-yellow-50/50 dark:bg-zinc-800/50 border border-yellow-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-yellow-400 dark:focus:ring-zinc-600 outline-none text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 min-h-[120px]"
								placeholder={t('forms.notesPlaceholder')}
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
								{t('forms.updateTicket')}
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
	onchange={handleFileChange}
/>
<input
	type="file"
	bind:this={twoShotInputRef}
	class="hidden"
	accept="image/*"
	onchange={handleTwoShotFileChange}
/>

{#if cropTarget && imageToCrop}
	<ImageCropperModal imageUrl={imageToCrop} onClose={handleCropCancel} onSave={handleCropSave} />
{/if}

<!-- Validation Alert Modal -->
<ValidationAlertModal
	show={showValidationAlert}
	title={t('validation.alert.title')}
	message={validationAlertMessage}
	onClose={() => (showValidationAlert = false)}
/>
