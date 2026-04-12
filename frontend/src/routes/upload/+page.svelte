<script lang="ts">
	import { ticketsStore, showToast, storageStore } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { invalidateDashboard } from '$lib/stores/dashboard';
	import { invalidateTheater, setlistsStore } from '$lib/stores/theater';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { extractTicketData } from '$lib/apis/llm';

	import { validateImageFile, getValidationErrorI18nKey } from '$lib/utils/fileValidation';
	import ValidationAlertModal from '$lib/components/ValidationAlertModal.svelte';

	import { ScanLine, Keyboard } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { PageHeader } from '$lib/components';
	import { SHOW_IMAGES, THEATER_ROWS } from '$lib/constants';
	import { UploadModeSelection, UploadAnalyzing, TicketImagePreview } from '$lib/components/upload';
	import TicketForm from '$lib/components/upload/TicketForm.svelte';
	import { calculateDayFromDate, calculateGateOpenTime } from '$lib/utils/ticketUtils';
	import { cleanseMarkdown, cleanseStorageUrl } from '$lib/utils/markdown';
	interface Props {}

	let {}: Props = $props();

	const { t } = useTranslation();

	// Constants
	const SHOW_OPTIONS = SHOW_IMAGES.map((s) => s.title);

	onMount(() => {
		setlistsStore.load();
	});

	let mode: 'SELECTION' | 'ANALYZING' | 'EDITING' = $state('SELECTION');

	let image: string | null = $state(null);
	let isSubmitting = $state(false);

	// 2-Shot
	let showTwoShot = $state(false);
	let twoShotImage: string | null = $state(null);
	let twoShotInputRef: HTMLInputElement | undefined = $state();

	// Validation alert modal state
	let showValidationAlert = $state(false);
	let validationAlertMessage = $state('');

	// Temporary state matching Ticket structure but editable
	let formData = $state({
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
	});

	let fileInputRef: HTMLInputElement | undefined = $state();

	// Normalization functions
	const normalizeTime = (raw: string | undefined): string => {
		if (!raw) return '';
		const clean = raw.trim().toUpperCase();
		const amPmMatch = clean.match(/(\d{1,2})[:.](\d{2})\s*(AM|PM)?/);
		if (amPmMatch) {
			let [, h, m, period] = amPmMatch;
			let hours = parseInt(h, 10);
			if (period === 'PM' && hours < 12) hours += 12;
			if (period === 'AM' && hours === 12) hours = 0;
			return `${hours.toString().padStart(2, '0')}:${m}`;
		}
		const simpleMatch = clean.match(/(\d{1,2})[:.](\d{2})/);
		return simpleMatch ? `${simpleMatch[1].padStart(2, '0')}:${simpleMatch[2]}` : '';
	};

	const processFile = (file: File) => {
		// Validate file before processing
		const validation = validateImageFile(file);
		if (!validation.valid) {
			validationAlertMessage = $t(getValidationErrorI18nKey(validation.error));
			showValidationAlert = true;
			return;
		}

		const reader = new FileReader();
		reader.onloadend = () => {
			image = reader.result as string;
			if (mode === 'SELECTION') analyzeImage(image);
		};
		reader.readAsDataURL(file);
	};

	const handleFileChange = (e: Event) => {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		processFile(file);
		target.value = ''; // Reset input
	};

	const handleFileDrop = (file: File) => {
		processFile(file);
	};

	const analyzeImage = async (base64: string) => {
		mode = 'ANALYZING';
		try {
			const result = await extractTicketData(base64);
			await setlistsStore.load();

			const currentSetlists = $setlistsStore.data
				? $setlistsStore.data.map((s) => s.title)
				: SHOW_OPTIONS;

			const detectedTitle =
				currentSetlists.find((opt) =>
					(result.title || '').toLowerCase().includes(opt.toLowerCase())
				) || '';
			const inputChar = (result.section || '').toUpperCase().trim().charAt(0);
			const detectedRow = (THEATER_ROWS as ReadonlyArray<string>).includes(inputChar)
				? inputChar
				: '';

			formData = {
				...formData,
				ticket_id: result.ticket_id || '',
				price: result.price || 200000,
				event: {
					...formData.event,
					title: detectedTitle,
					date: result.date || formData.event.date,
					day: result.day || calculateDayFromDate(result.date || formData.event.date),
					time: normalizeTime(result.time),
					gate_open:
						normalizeTime(result.gate_open) || calculateGateOpenTime(normalizeTime(result.time))
				},
				seat: { ...formData.seat, section: detectedRow, number: result.number || '' }
			};
			mode = 'EDITING';
		} catch (e) {
			logger.error('Image analysis failed', e, { context: 'UploadPage' });
			showToast($t('forms.analysisFailed'), 'error');
			mode = 'EDITING';
		}
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

	const processTwoShotFile = (file: File) => {
		// Validate file before processing
		const validation = validateImageFile(file);
		if (!validation.valid) {
			validationAlertMessage = $t(getValidationErrorI18nKey(validation.error));
			showValidationAlert = true;
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
		// Final validation check before submit
		if (!isFormValid) return;

		isSubmitting = true;
		try {
			// Upload images to storage if present
			let ticketImageUrl: string | undefined;
			let twoShotImageUrl: string | undefined;

			if (image) {
				const uploadResult = await storageStore.uploadImage(image, 'ticket');
				ticketImageUrl = uploadResult.filename;
			}

			if (showTwoShot && twoShotImage) {
				const uploadResult = await storageStore.uploadImage(twoShotImage, 'twoshot');
				twoShotImageUrl = uploadResult.filename;
			}

			// Prepare object for API
			const payload = {
				ticket_id: formData.ticket_id || `MANUAL-${Date.now()}`,
				event: formData.event,
				seat: { ...formData.seat, number: Number(formData.seat.number) },
				price: Number(formData.price),
				currency: 'IDR',
				rules: formData.rules,
				imageUrl: cleanseStorageUrl(ticketImageUrl),
				notes: cleanseMarkdown(formData.notes),
				two_shot: showTwoShot
					? {
							imageUrl: cleanseStorageUrl(twoShotImageUrl),
							member_name: formData.two_shot.member_name,
							type: formData.two_shot.type,
							price: Number(formData.two_shot.price)
						}
					: undefined
			};

			// Use store action (handles API + cache invalidation)
			await ticketsStore.create(payload);

			// Invalidate dashboard and theater cache
			invalidateDashboard();
			invalidateTheater();

			showToast($t('upload.uploadSuccess'));
			goto('/');
		} catch (e) {
			logger.error('Ticket upload failed', e, { context: 'UploadPage' });
			showToast($t('upload.uploadError'), 'error');
		} finally {
			isSubmitting = false;
		}
	};

	const handleManualEntry = () => {
		mode = 'EDITING';
		image = null;
	};

	$effect(() => {
		const modeParam = $page.url.searchParams.get('mode');
		if (modeParam === 'manual' && mode !== 'EDITING' && !isSubmitting) {
			handleManualEntry();
		} else if (modeParam === 'scan' && mode !== 'SELECTION') {
			mode = 'SELECTION';
		}
	});

	// Reactive Day Calculation
	$effect(() => {
		if (formData.event.date) {
			const newDay = calculateDayFromDate(formData.event.date);
			if (newDay && newDay !== formData.event.day) {
				formData.event.day = newDay;
			}
		}
	});

	// Reactive Gate Open Calculation (30 mins before Show Time)
	$effect(() => {
		if (formData.event.time) {
			const newGateOpen = calculateGateOpenTime(formData.event.time);
			if (newGateOpen && newGateOpen !== formData.event.gate_open) {
				formData.event.gate_open = newGateOpen;
			}
		}
	});

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
					formData.two_shot.price >= 0 &&
					twoShotImage))
		)
	);
</script>

<SEO title={$t('upload.title')} path="/upload" description={$t('seo.upload')} />

<!-- Page Header (Hidden visually but kept for MobileHeader store sync) -->
<div class="hidden max-w-5xl mx-auto pt-4 sm:pt-6 px-4 mb-4">
	<PageHeader
		title={$t('upload.title')}
		subtitle={$t('upload.subtitle')}
		icon={ScanLine}
		theme="red"
	/>
</div>

{#if mode === 'SELECTION'}
	<UploadModeSelection
		onScanClick={() => fileInputRef?.click()}
		onManualClick={handleManualEntry}
		{onCancel}
	/>
{/if}

{#if mode === 'ANALYZING'}
	<UploadAnalyzing />
{/if}

{#if mode === 'EDITING'}
	<div class="max-w-5xl mx-auto pt-0 px-4 pb-24 animate-fade-in">
		<div class="mb-6 flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="p-2 rounded-xl bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400">
					<Keyboard class="w-5 h-5" />
				</div>
				<div>
					<h2 class="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tight">
						{$t('forms.newTicket')}
					</h2>
					<p class="text-xs text-slate-500 dark:text-slate-400 font-medium">
						{$t('forms.addToCollection')}
					</p>
				</div>
			</div>
			<button
				onclick={onCancel}
				class="text-[10px] sm:text-sm font-bold text-gray-500 dark:text-gray-400 hover:text-red-600 bg-white dark:bg-zinc-800 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full shadow-sm border border-gray-200 dark:border-zinc-700 cursor-pointer whitespace-nowrap"
				>{$t('forms.cancel')}</button
			>
		</div>

		<div class="grid gap-8 lg:grid-cols-2">
			<!-- Image Preview -->
			<div class="flex flex-col gap-4">
				<TicketImagePreview
					{image}
					onChangePhoto={() => fileInputRef?.click()}
					ondrop={handleFileDrop}
				/>
			</div>

			<!-- FORM -->
			<TicketForm
				bind:formData
				bind:isSubmitting
				{isFormValid}
				bind:showTwoShot
				bind:twoShotImage
				onclick={handleFormSubmit}
				onsubmit={handleFormSubmit}
				onphotoClick={() => twoShotInputRef?.click()}
				ondrop={handleTwoShotDrop}
			/>
		</div>
	</div>
{/if}

<input
	type="file"
	bind:this={fileInputRef}
	class="hidden"
	accept="image/*"
	onchange={handleFileChange}
/>
<input
	type="file"
	accept="image/*"
	class="hidden"
	id="two-shot-photo"
	bind:this={twoShotInputRef}
	onchange={handleTwoShotFileChange}
/>

<!-- Validation Alert Modal -->
<ValidationAlertModal
	show={showValidationAlert}
	title={$t('validation.alert.title')}
	message={validationAlertMessage}
	onClose={() => (showValidationAlert = false)}
/>
