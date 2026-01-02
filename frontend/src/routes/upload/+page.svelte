<script lang="ts">
	import { tickets, showToast } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { extractTicketData } from '$lib/services/geminiService';
	import { theater } from '$lib/apis/theater';
	import { validateImageFile, getValidationErrorI18nKey } from '$lib/utils/fileValidation';
	import ValidationAlertModal from '$lib/components/ValidationAlertModal.svelte';

	import {
		Loader2,
		CheckCircle,
		NotebookPen,
		Keyboard,
		Calendar,
		Clock,
		MapPin,
		DollarSign,
		Hash,
		Ticket as TicketIcon,
		ChevronDown
	} from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { PageHeader } from '$lib/components';
	import { SHOW_IMAGES, THEATER_ROWS } from '$lib/constants';
	import {
		UploadModeSelection,
		UploadAnalyzing,
		TicketImagePreview,
		TwoShotSection
	} from '$lib/components/upload';

	const { t } = useTranslation();

	// Constants
	const SHOW_OPTIONS = SHOW_IMAGES.map((s) => s.title);
	const ROW_OPTIONS = THEATER_ROWS;

	let mode: 'SELECTION' | 'ANALYZING' | 'EDITING' = 'SELECTION';
	let image: string | null = null;
	let isSubmitting = false;

	// 2-Shot
	let showTwoShot = false;
	let twoShotImage: string | null = null;
	let twoShotInputRef: HTMLInputElement;

	// Validation alert modal state
	let showValidationAlert = false;
	let validationAlertMessage = '';

	// Temporary state matching Ticket structure but editable
	let formData = {
		event: {
			title: '',
			date: new Date().toISOString().split('T')[0],
			day: '',
			time: '',
			gate_open: '',
			venue: 'JKT48 Theater'
		},
		seat: {
			section: '',
			number: ''
		},
		ticket_id: '',
		price: 200000,
		currency: 'IDR',
		notes: '',
		rules: { refund_allowed: false, exchange_allowed: false },
		two_shot: {
			imageUrl: '',
			member_name: '',
			type: 'Roulette' as 'Roulette' | 'Birthday',
			price: 100000
		}
	};

	let fileInputRef: HTMLInputElement;

	// Normalization
	const normalizeTime = (raw: string | undefined): string => {
		if (!raw) return '';
		const clean = raw.trim().toUpperCase();
		const amPmMatch = clean.match(/(\d{1,2})[:.](d{2})\s*(AM|PM)?/);
		if (amPmMatch) {
			let [, h, m, period] = amPmMatch;
			let hours = parseInt(h, 10);
			if (period === 'PM' && hours < 12) hours += 12;
			if (period === 'AM' && hours === 12) hours = 0;
			return `${hours.toString().padStart(2, '0')}:${m}`;
		}
		const simpleMatch = clean.match(/(\d{1,2})[:.](d{2})/);
		return simpleMatch ? `${simpleMatch[1].padStart(2, '0')}:${simpleMatch[2]}` : '';
	};

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
			if (mode === 'SELECTION') analyzeImage(image);
		};
		reader.readAsDataURL(file);
	};

	const analyzeImage = async (base64: string) => {
		mode = 'ANALYZING';
		try {
			const result = await extractTicketData(base64);
			// ... Match logic ...
			const detectedTitle =
				SHOW_OPTIONS.find((opt) =>
					(result.title || '').toLowerCase().includes(opt.toLowerCase())
				) || '';
			const inputChar = (result.section || '').toUpperCase().trim().charAt(0);
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			const detectedRow = THEATER_ROWS.includes(inputChar as any) ? inputChar : '';

			formData = {
				...formData,
				ticket_id: result.ticket_id || '',
				price: result.price || 200000,
				event: {
					...formData.event,
					title: detectedTitle,
					date: result.date || formData.event.date,
					day: result.day || '',
					time: normalizeTime(result.time),
					gate_open: normalizeTime(result.gate_open)
				},
				seat: { ...formData.seat, section: detectedRow, number: result.number || '' }
			};
			mode = 'EDITING';
		} catch (e) {
			console.error(e);
			showToast($t('forms.analysisFailed'), 'error');
			mode = 'EDITING';
		}
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

	const onCancel = () => goto('/');

	const handleFormSubmit = async () => {
		isSubmitting = true;
		try {
			// Prepare object for API
			const payload = {
				ticket_id: formData.ticket_id || `MANUAL-${Date.now()}`,
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
					: undefined
			};

			await theater.createTicket(payload);
			// Fetch fresh data from server after create
			const freshTickets = await theater.getMyTickets();
			tickets.set(freshTickets);
			showToast('Ticket saved successfully!');
			goto('/');
		} catch (e) {
			console.error(e);
			showToast('Failed to save ticket. Please try again.', 'error');
		} finally {
			isSubmitting = false;
		}
	};

	const handleManualEntry = () => {
		mode = 'EDITING';
		image = null;
	};

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
</script>

<SEO title={$t('upload.title')} path="/upload" description={$t('seo.upload')} />

{#if mode === 'SELECTION'}
	<UploadModeSelection
		onScanClick={() => fileInputRef.click()}
		onManualClick={handleManualEntry}
		{onCancel}
	/>
{/if}

{#if mode === 'ANALYZING'}
	<UploadAnalyzing />
{/if}

{#if mode === 'EDITING'}
	<div class="max-w-5xl mx-auto p-4 pb-24 animate-fade-in">
		<div class="flex items-center justify-between mb-6">
			<PageHeader
				icon={Keyboard}
				title={$t('forms.newTicket')}
				subtitle={$t('forms.addToCollection')}
				theme="red"
			/>
			<button
				on:click={onCancel}
				class="text-sm font-bold text-gray-500 dark:text-gray-400 hover:text-red-600 bg-white dark:bg-zinc-800 px-4 py-2 rounded-full shadow-sm border border-gray-200 dark:border-zinc-700 cursor-pointer"
				>{$t('forms.cancel')}</button
			>
		</div>

		<div class="grid gap-8 lg:grid-cols-2">
			<!-- Image Preview -->
			<div class="flex flex-col gap-4">
				<TicketImagePreview {image} onChangePhoto={() => fileInputRef.click()} />
			</div>

			<!-- FORM -->
			<div
				class="bg-white/80 dark:bg-zinc-800/80 backdrop-blur-xl p-6 md:p-8 rounded-3xl border border-white/50 dark:border-zinc-700 shadow-xl h-fit"
			>
				<form on:submit|preventDefault={handleFormSubmit} class="space-y-8">
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
						bind:twoShotImage
						bind:memberName={formData.two_shot.member_name}
						bind:twoShotType={formData.two_shot.type}
						bind:twoShotPrice={formData.two_shot.price}
						onPhotoClick={() => twoShotInputRef.click()}
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
						disabled={isSubmitting || !isFormValid}
						class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.01] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer disabled:shadow-none disabled:transform-none"
					>
						{#if isSubmitting}
							<Loader2 class="w-6 h-6 animate-spin" />
						{:else}
							<CheckCircle class="w-6 h-6" />
						{/if}
						{$t('forms.saveTicket')}
					</button>
				</form>
			</div>
		</div>
	</div>
{/if}

<input
	type="file"
	bind:this={fileInputRef}
	class="hidden"
	accept="image/*"
	on:change={handleFileChange}
/>
<input
	type="file"
	accept="image/*"
	class="hidden"
	id="two-shot-photo"
	bind:this={twoShotInputRef}
	on:change={handleTwoShotFileChange}
/>

<!-- Validation Alert Modal -->
<ValidationAlertModal
	show={showValidationAlert}
	title={$t('validation.alert.title')}
	message={validationAlertMessage}
	onClose={() => (showValidationAlert = false)}
/>
