<script lang="ts">
	import { ImagePlus, Scissors } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { dragDrop } from '$lib/actions/dragDrop';
	import { OptimizedImage } from '$lib/components/common';
	import ImageCropperModal from '$lib/components/common/ImageCropperModal.svelte';
	import { validateImageFile, getValidationErrorI18nKey } from '$lib/utils/fileValidation';
	import ValidationAlertModal from '$lib/components/ValidationAlertModal.svelte';

	interface Props {
		image: string | null;
		label?: string;
		aspectRatio?: string;
		onSelect: (base64: string) => void;
	}

	let { image, label, aspectRatio = 'aspect-[4/5]', onSelect }: Props = $props();

	const { t } = useTranslation();

	let isDragging = $state(false);
	let fileInputRef: HTMLInputElement | undefined = $state();
	let showCropper = $state(false);
	let imageToCrop = $state<string | null>(null);

	// Validation alert modal state
	let showValidationAlert = $state(false);
	let validationAlertMessage = $state('');

	const processFile = (file: File) => {
		const validation = validateImageFile(file);
		if (!validation.valid) {
			validationAlertMessage = t(getValidationErrorI18nKey(validation.error));
			showValidationAlert = true;
			return;
		}

		const reader = new FileReader();
		reader.onloadend = () => {
			imageToCrop = reader.result as string;
			showCropper = true;
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

	const handleCropSave = (croppedBase64: string) => {
		onSelect(croppedBase64);
		showCropper = false;
		imageToCrop = null;
	};

	const handleCropCancel = () => {
		showCropper = false;
		imageToCrop = null;
	};

	const handleEdit = () => {
		if (image) {
			imageToCrop = image;
			showCropper = true;
		}
	};
</script>

<div class="flex flex-col gap-2">
	{#if label}
		<span class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1">{label}</span>
	{/if}

	<div
		class="relative"
		role="region"
		aria-label="Image Upload Dropzone"
		use:dragDrop={{
			onDrop: (file) => processFile(file),
			onDragChange: (state) => (isDragging = state)
		}}
	>
		{#if image}
			<div
				class="relative rounded-3xl overflow-hidden border shadow-lg group transition-all duration-200 {aspectRatio}
				{isDragging
					? 'border-red-500 bg-red-50 dark:bg-red-900/10 ring-4 ring-red-500/20 scale-[1.01]'
					: 'border-gray-200 dark:border-zinc-700 bg-gray-100 dark:bg-zinc-800'}"
			>
				<OptimizedImage src={image} alt="Preview" class="w-full h-full p-2" objectFit="contain" />
				<div
					class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-4"
				>
					<button
						type="button"
						onclick={() => fileInputRef?.click()}
						class="p-3 bg-white/20 hover:bg-white/40 backdrop-blur-md rounded-2xl text-white transition-all transform hover:scale-110"
						title="Change Image"
					>
						<ImagePlus class="w-6 h-6" />
					</button>
					<button
						type="button"
						onclick={handleEdit}
						class="p-3 bg-white/20 hover:bg-white/40 backdrop-blur-md rounded-2xl text-white transition-all transform hover:scale-110"
						title="Crop Image"
					>
						<Scissors class="w-6 h-6" />
					</button>
				</div>
			</div>
		{:else}
			<button
				type="button"
				onclick={() => fileInputRef?.click()}
				class="w-full rounded-3xl border-3 border-dashed transition-all cursor-pointer flex flex-col items-center justify-center {aspectRatio}
				{isDragging
					? 'border-red-500 bg-red-50 dark:bg-red-900/10 text-red-500 scale-[1.01] ring-4 ring-red-500/20'
					: 'border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 hover:bg-red-50 dark:hover:bg-red-900/20 hover:border-red-200 dark:hover:border-red-500/50 text-gray-400 dark:text-gray-500 hover:text-red-500'}"
			>
				<div
					class="p-4 rounded-full shadow-sm mb-4 {isDragging
						? 'bg-red-100 dark:bg-red-900/20 text-red-500'
						: 'bg-white dark:bg-zinc-700'}"
				>
					<ImagePlus class="w-8 h-8" />
				</div>
				<p class="font-bold text-lg">{t('forms.uploadPhoto')}</p>
				<p class="{isDragging ? 'text-red-400' : 'text-gray-400 dark:text-gray-500'} text-xs mt-1">
					{t('forms.dragAndDrop')}
				</p>
			</button>
		{/if}
	</div>
</div>

<input
	id="admin-image-upload-input"
	name="image"
	type="file"
	bind:this={fileInputRef}
	class="hidden"
	accept="image/*"
	onchange={handleFileChange}
/>

{#if showCropper && imageToCrop}
	<ImageCropperModal imageUrl={imageToCrop} onClose={handleCropCancel} onSave={handleCropSave} />
{/if}

<ValidationAlertModal
	show={showValidationAlert}
	title={t('validation.alert.title')}
	message={validationAlertMessage}
	onClose={() => (showValidationAlert = false)}
/>
