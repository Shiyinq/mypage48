<script lang="ts">
	export let params: Record<string, string> | undefined = undefined;
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

	import { Keyboard } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { PageHeader } from '$lib/components';
	import { SHOW_IMAGES, THEATER_ROWS } from '$lib/constants';
	import {
		UploadModeSelection,
		UploadAnalyzing,
		TicketImagePreview,
		TicketForm
	} from '$lib/components/upload';
	import { calculateDayFromDate, calculateGateOpenTime } from '$lib/utils/ticketUtils';
	import { cleanseMarkdown, cleanseStorageUrl } from '$lib/utils/markdown';

	const { t } = useTranslation();

	// Constants
	const SHOW_OPTIONS = SHOW_IMAGES.map((s) => s.title);

	onMount(() => {
		setlistsStore.load();
	});

	let mode: 'SELECTION' | 'ANALYZING' | 'EDITING' = 'SELECTION';

	$: {
		const modeParam = $page.url.searchParams.get('mode');
		if (modeParam === 'manual' && mode !== 'EDITING' && !isSubmitting) {
			handleManualEntry();
		} else if (modeParam === 'scan' && mode !== 'SELECTION') {
			mode = 'SELECTION';
		}
	}

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

	const handleFileDrop = (e: CustomEvent<File>) => {
		processFile(e.detail);
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

	const handleTwoShotDrop = (e: CustomEvent<File>) => {
		processTwoShotFile(e.detail);
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

	// Validation
	$: isFormValid =
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
				twoShotImage));

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
				<TicketImagePreview
					{image}
					onChangePhoto={() => fileInputRef.click()}
					on:drop={handleFileDrop}
				/>
			</div>

			<!-- FORM -->
			<TicketForm
				bind:formData
				bind:isSubmitting
				bind:isFormValid
				bind:showTwoShot
				bind:twoShotImage
				on:click={handleFormSubmit}
				on:photoClick={() => twoShotInputRef.click()}
				on:drop={handleTwoShotDrop}
			/>
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
