<script lang="ts">
	import type { PageData } from './$types';
	import { SEO, TheaterSeatMap } from '$lib/components';
	import { Ticket } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { auth } from '$lib/apis/auth';
	import { userProfile } from '$lib/stores';
	import PublicProfileHeader from '$lib/components/public-profile/PublicProfileHeader.svelte';
	import PublicProfileStats from '$lib/components/public-profile/PublicProfileStats.svelte';
	import PublicProfileRecentActivity from '$lib/components/public-profile/PublicProfileRecentActivity.svelte';
	import ProfilePictureUploadModal from '$lib/components/public-profile/ProfilePictureUploadModal.svelte';

	export let data: PageData;

	const { t } = useTranslation();
	$: ({ profile } = data);

	let fileInput: HTMLInputElement | undefined;
	let isUploading = false;

	// Preview modal state
	let showPreviewModal = false;
	let previewImage: string | null = null;

	async function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

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
			console.error('Failed to read file:', error);
			alert('Failed to read file.');
		} finally {
			// Reset input so the same file can be selected again
			if (fileInput) fileInput.value = '';
		}
	}

	function closePreviewModal() {
		showPreviewModal = false;
		previewImage = null;
	}

	async function confirmUpload() {
		if (!previewImage) return;

		// Validate file size (10MB max) - base64 is ~33% larger than original
		const base64Size = previewImage.length * 0.75; // approximate original size
		if (base64Size > 10 * 1024 * 1024) {
			alert($t('profile.profilePicture.fileTooLarge'));
			return;
		}

		isUploading = true;
		try {
			// Upload to server
			await auth.updateProfilePicture(previewImage);

			// Update profile picture locally
			profile.profilePicture = previewImage;

			// Update global store if it's currently logged in user
			if ($userProfile && $userProfile.username === profile.username) {
				userProfile.update((u) => (u ? { ...u, profilePicture: previewImage } : null));
			}

			// Close modal on success
			closePreviewModal();
		} catch (error) {
			console.error('Failed to upload profile picture:', error);
			alert('Failed to upload profile picture.');
		} finally {
			isUploading = false;
		}
	}

	// Prepare data for Seat Map
	let rowStats = { counts: {}, maxCount: 0, uniqueVisited: 0 };
	let seatStats = {};

	$: if (profile?.stats) {
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
</script>

<SEO
	title={`${profile.name} (@${profile.username})`}
	description={`Check out ${profile.name}'s JKT48 theater journey!`}
/>

<div class="max-w-4xl mx-auto p-4 pb-24 animate-fade-in">
	<!-- Hidden File Input -->
	<input
		type="file"
		accept="image/*"
		class="hidden"
		bind:this={fileInput}
		on:change={handleFileSelect}
	/>

	<!-- Header -->
	<PublicProfileHeader
		{profile}
		isCurrentUser={!!($userProfile && $userProfile.username === profile.username)}
		{isUploading}
		on:triggerUpload={() => fileInput?.click()}
	/>

	<!-- Stats -->
	{#if profile.stats}
		<!-- Main Content Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
			<!-- Left Column: Stats Grid -->
			<PublicProfileStats stats={profile.stats} />

			<!-- Right Column: Recent Activity -->
			<PublicProfileRecentActivity recentActivity={profile.stats.recentActivity} />
		</div>

		<!-- Theater Map -->
		<TheaterSeatMap {rowStats} {seatStats} showSubtitle={false} compact={true} />
	{/if}

	<!-- Call to Action (if not logged in) or other info -->
	<div class="text-center mt-12 mb-8">
		<p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">Powered by</p>

		<!-- Logo Section (matching navbar style) -->
		<a href="/" class="inline-flex items-center gap-3 mb-4 group cursor-pointer">
			<div
				class="w-9 h-9 rounded-full idol-gradient flex items-center justify-center text-white shadow-red-200 dark:shadow-red-900/50 shadow-lg ring-2 ring-white dark:ring-gray-800"
			>
				<Ticket class="w-5 h-5" />
			</div>
			<div class="flex flex-col text-left">
				<span
					class="text-xl font-black tracking-tight text-gray-900 dark:text-gray-100 leading-none"
				>
					MyPage<span class="text-red-600 dark:text-red-500">48</span>
				</span>
				<span class="text-[10px] font-semibold text-gray-400 tracking-wide"
					>{$t('header.tagline')}</span
				>
			</div>
		</a>

		<p class="text-xs font-bold text-gray-400">
			<a
				href="/"
				class="text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 underline underline-offset-2 cursor-pointer"
				>Get your own theater tracker</a
			>
		</p>
	</div>
</div>

<!-- Profile Picture Preview Modal -->
{#if showPreviewModal && previewImage}
	<ProfilePictureUploadModal
		{previewImage}
		{isUploading}
		on:close={closePreviewModal}
		on:save={confirmUpload}
	/>
{/if}
