<script lang="ts">
	import type { PageData } from './$types';
	import { invalidateAll } from '$app/navigation';
	import { SEO } from '$lib/components';
	import { Ticket } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { spring } from 'svelte/motion';
	import AppBackground from '$lib/components/common/AppBackground.svelte';

	import { userProfile, showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import {
		validateImageFile,
		validateBase64Image,
		getValidationErrorI18nKey
	} from '$lib/utils/fileValidation';
	import { getErrorMessage } from '$lib/utils/api';
	import ValidationAlertModal from '$lib/components/ValidationAlertModal.svelte';
	import PublicProfileHeader from '$lib/components/public-profile/PublicProfileHeader.svelte';
	import PublicProfileStats from '$lib/components/public-profile/PublicProfileStats.svelte';
	import PublicProfileTopTwoShot from '$lib/components/public-profile/PublicProfileTopTwoShot.svelte';
	import PublicProfileTopSetlists from '$lib/components/public-profile/PublicProfileTopSetlists.svelte';
	import PublicProfileSeatMap from '$lib/components/public-profile/PublicProfileSeatMap.svelte';
	import ImageCropperModal from '$lib/components/common/ImageCropperModal.svelte';
	import { HeatmapCalendar } from '$lib/components/dashboard';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const { t } = useTranslation();
	let { profile } = $derived(data);

	let fileInput: HTMLInputElement | undefined = $state();

	// Preview modal state
	let showPreviewModal = $state(false);
	let previewImage: string | null = $state(null);

	// Validation alert modal state
	let showValidationAlert = $state(false);
	let validationAlertMessage = $state('');

	async function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		// Validate file before processing
		const validation = validateImageFile(file);
		if (!validation.valid) {
			validationAlertMessage = t(getValidationErrorI18nKey(validation.error));
			showValidationAlert = true;
			if (fileInput) fileInput.value = '';
			return;
		}

		try {
			// Read file as base64 using Promise
			const base64 = await new Promise<string>((resolve, reject) => {
				const reader = new FileReader();
				reader.onload = () => resolve(reader.result as string);
				reader.onerror = () => reject(new Error('Failed to read file'));
				reader.readAsDataURL(file);
			});

			// Show preview modal
			previewImage = base64;
			showPreviewModal = true;
		} catch (error) {
			logger.error('Failed to read file', error, { context: 'PublicProfilePage' });
			validationAlertMessage = t('publicProfile.uploadError');
			showValidationAlert = true;
		} finally {
			// Reset input so the same file can be selected again
			if (fileInput) fileInput.value = '';
		}
	}

	function closePreviewModal() {
		showPreviewModal = false;
		previewImage = null;
	}

	async function confirmUpload(croppedBase64: string) {
		if (!croppedBase64) return;

		// Validate base64 image (type and size)
		const validation = validateBase64Image(croppedBase64);
		if (!validation.valid) {
			validationAlertMessage = t(getValidationErrorI18nKey(validation.error));
			showValidationAlert = true;
			return;
		}

		// Close modal immediately so user sees the loading state on the avatar
		closePreviewModal();

		try {
			// Update avatar using the store (handles upload and profile update)
			await userProfile.updateAvatar(croppedBase64);

			// Refresh page data to show new avatar
			await invalidateAll();

			showToast(t('settings.publicProfile.uploadSuccess'), 'success');
		} catch (error: unknown) {
			logger.error('Failed to upload profile picture', error, { context: 'PublicProfilePage' });
			const errorMessage = getErrorMessage(error);
			showToast(errorMessage || t('settings.publicProfile.uploadError'), 'error');
		}
	}

	// Prepare data for Seat Map
	let rowStats = $state({ counts: {}, maxCount: 0, uniqueVisited: 0 });
	let seatStats = $state({});

	$effect(() => {
		if (profile?.stats) {
			const counts = profile.stats.rowCounts || {};
			const maxCount = Math.max(...Object.values(counts).map(Number), 0);
			const uniqueVisited = Object.keys(counts).length;

			rowStats = {
				counts,
				maxCount,
				uniqueVisited
			};
			seatStats = profile.stats.seatCounts || {};
		}
	});

	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));
	let scrollY = $state(0);
</script>

<SEO
	title={`${profile.name} (@${profile.username})`}
	description={`Check out ${profile.name}'s JKT48 theater journey!`}
/>

<svelte:window bind:scrollY />

<div
	class="min-h-screen relative overflow-hidden bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 selection:bg-red-500/20"
>
	<AppBackground hideDecorationsOnMobile={true} interactive={true} bind:mouse bind:scrollY />

	<div class="relative max-w-6xl mx-auto p-4 md:p-8 pb-24 z-10 animate-fade-in space-y-8">
		<!-- Hidden File Input -->
		<input
			type="file"
			accept="image/*"
			class="hidden"
			bind:this={fileInput}
			onchange={handleFileSelect}
		/>

		<!-- Header Section -->
		<PublicProfileHeader
			{profile}
			isCurrentUser={!!(userProfile.data && userProfile.data.username === profile.username)}
			isUploading={userProfile.isUpdatingAvatar}
			ontriggerUpload={() => fileInput?.click()}
		/>

		<!-- Stats Section -->
		{#if profile.stats}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 lg:gap-6 items-stretch">
				<PublicProfileStats stats={profile.stats} year={profile.publicYear} />
				<PublicProfileTopTwoShot topTwoShots={profile.stats.topTwoShots} />
				<div class="md:col-span-2 lg:col-span-1">
					<PublicProfileTopSetlists showCounts={profile.stats.showCounts} />
				</div>
			</div>

			<!-- Theater Seat Map -->
			<div class="animate-on-scroll">
				<PublicProfileSeatMap {rowStats} {seatStats} />
			</div>

			<!-- Heatmap -->
			{#if profile.stats.heatmapData && Object.keys(profile.stats.heatmapData).length > 0}
				{@const heatmapYears = Array.from(
					new Set(Object.keys(profile.stats.heatmapData).map((d) => parseInt(d.substring(0, 4))))
				).sort((a, b) => b - a)}
				<div class="animate-on-scroll flex flex-col gap-6">
					{#each heatmapYears.length > 0 ? heatmapYears : [new Date().getFullYear()] as year}
						<HeatmapCalendar
							{year}
							data={profile.stats.heatmapData}
							isLoading={false}
							variant="public"
						/>
					{/each}
				</div>
			{/if}
		{/if}

		<!-- Footer / Watermark -->
		<div class="text-center mt-16 pb-8 opacity-60 hover:opacity-100 transition-opacity">
			<a href="/" class="inline-flex flex-col items-center gap-2 group cursor-pointer">
				<div
					class="w-10 h-10 rounded-xl idol-gradient flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform duration-300"
				>
					<Ticket class="w-5 h-5" />
				</div>
				<div class="flex flex-col">
					<span class="text-xs font-bold uppercase tracking-wider text-gray-400">Generated by</span>
					<span class="text-lg font-black tracking-tight text-gray-900 dark:text-white">
						MyPage<span class="text-red-500">48</span>
					</span>
				</div>
			</a>
		</div>
	</div>
</div>

<!-- Profile Picture Preview Modal -->
{#if showPreviewModal && previewImage}
	<ImageCropperModal imageUrl={previewImage} onClose={closePreviewModal} onSave={confirmUpload} />
{/if}

<!-- Validation Alert Modal -->
<ValidationAlertModal
	show={showValidationAlert}
	title={t('validation.alert.title')}
	message={validationAlertMessage}
	onClose={() => (showValidationAlert = false)}
/>
