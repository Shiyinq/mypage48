<script lang="ts">
	import type { PageData } from './$types';
	import SEO from '$lib/components/SEO.svelte';
	import TheaterSeatMap from '$lib/components/TheaterSeatMap.svelte';
	import { User, Calendar, Ticket, Camera, Heart, Armchair, Loader2, X } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { auth } from '$lib/apis/auth';
	import { userProfile } from '$lib/stores';

	export let data: PageData;

	const { t } = useTranslation();
	$: ({ profile } = data);

	let fileInput: HTMLInputElement;
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
	<!-- Header -->

	<div
		class="glass-panel p-6 rounded-3xl relative overflow-hidden group flex flex-col md:flex-row items-center gap-6 mb-6"
		role="region"
	>
		<!-- Background decoration -->
		<div
			class="absolute top-0 right-0 w-64 h-64 bg-red-500/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"
		></div>

		<!-- Avatar -->
		<div class="relative group">
			<input
				type="file"
				accept="image/*"
				class="hidden"
				bind:this={fileInput}
				on:change={handleFileSelect}
			/>

			<div
				class="w-32 h-32 rounded-full border-4 border-white dark:border-zinc-800 shadow-xl overflow-hidden bg-gray-100 dark:bg-zinc-800 relative"
			>
				{#if profile.profilePicture}
					<img src={profile.profilePicture} alt={profile.name} class="w-full h-full object-cover" />
				{:else}
					<div class="w-full h-full flex items-center justify-center text-gray-400">
						<User class="w-12 h-12" />
					</div>
				{/if}

				<!-- Edit Overlay -->
				{#if $userProfile && $userProfile.username === profile.username}
					<button
						class="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer disabled:cursor-not-allowed"
						on:click={() => fileInput?.click()}
						disabled={isUploading}
					>
						{#if isUploading}
							<Loader2 class="w-8 h-8 text-white animate-spin" />
						{:else}
							<Camera class="w-8 h-8 text-white" />
						{/if}
					</button>
				{/if}
			</div>
			{#if profile.oshi}
				<div
					class="absolute -bottom-2 -right-2 bg-white dark:bg-zinc-800 rounded-full p-1.5 shadow-md border border-gray-100 dark:border-zinc-700 tooltip-container"
				>
					<div class="w-10 h-10 rounded-full overflow-hidden border-2 border-pink-400">
						<img
							src={profile.oshi.profilePicture}
							alt={profile.oshi.name}
							class="w-full h-full object-cover"
						/>
					</div>
				</div>
			{/if}
		</div>

		<!-- Info -->
		<div class="relative z-10 text-center md:text-left">
			<h1 class="text-3xl font-black text-gray-900 dark:text-white leading-tight mb-2">
				{profile.name}
			</h1>
			<p class="text-purple-600 dark:text-purple-400 font-bold mb-4">@{profile.username}</p>

			<div class="flex flex-wrap justify-center md:justify-start gap-3">
				{#if profile.oshi}
					<div
						class="flex items-center gap-2 px-3 py-1.5 bg-pink-50 dark:bg-pink-900/20 rounded-full text-xs font-bold text-pink-600 dark:text-pink-400"
					>
						<Heart class="w-3.5 h-3.5 fill-current" />
						Oshi: {profile.oshi.name}
					</div>
				{/if}
				{#if profile.publicYear}
					<div
						class="flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-full text-xs font-bold text-blue-700 dark:text-blue-300"
					>
						<Ticket class="w-3.5 h-3.5" />
						{$t('profile.publicActivity.yearBadge', { year: profile.publicYear })}
					</div>
				{/if}
			</div>
		</div>
	</div>

	<!-- Stats -->
	{#if profile.stats}
		<!-- Main Content Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
			<!-- Left Column: Stats Grid -->
			<div class="lg:col-span-2 grid grid-cols-2 gap-4">
				<!-- Show Count -->
				<div
					class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
				>
					<div
						class="w-10 h-10 rounded-2xl bg-red-50 dark:bg-red-900/20 text-red-500 flex items-center justify-center mb-1"
					>
						<Ticket class="w-5 h-5" />
					</div>
					<span class="text-5xl font-black text-gray-900 dark:text-white"
						>{profile.stats.totalShows}</span
					>
					<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
						>{$t('profile.stats.totalShows')}</span
					>
				</div>

				<!-- 2-Shot Count -->
				<div
					class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
				>
					<div
						class="w-10 h-10 rounded-2xl bg-pink-50 dark:bg-pink-900/20 text-pink-500 flex items-center justify-center mb-1"
					>
						<Camera class="w-5 h-5" />
					</div>
					<span class="text-5xl font-black text-gray-900 dark:text-white"
						>{profile.stats.totalTwoShots}</span
					>
					<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
						>{$t('dashboard.twoShot.twoShotTitle')}</span
					>
				</div>

				<!-- Top Row -->
				<div
					class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
				>
					<div
						class="w-10 h-10 rounded-2xl bg-purple-50 dark:bg-purple-900/20 text-purple-500 flex items-center justify-center mb-1"
					>
						<Armchair class="w-5 h-5" />
					</div>
					<span class="text-5xl font-black text-gray-900 dark:text-white"
						>{profile.stats.topRow || '-'}</span
					>
					{#if profile.stats.topRowCount}
						<span class="text-lg font-extrabold text-gray-500 dark:text-gray-400 mt-1">
							{profile.stats.topRowCount}
							{$t('dashboard.theater.times')}
						</span>
					{/if}
					<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
						>{$t('dashboard.theater.topRow')}</span
					>
				</div>

				<!-- Top Show (Replaced Spent) -->
				<div
					class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
				>
					<div
						class="w-10 h-10 rounded-2xl bg-yellow-50 dark:bg-yellow-900/20 text-yellow-500 flex items-center justify-center mb-1"
					>
						<Heart class="w-5 h-5" />
					</div>
					<span
						class="font-black text-gray-900 dark:text-white line-clamp-2 leading-tight px-2 {(
							profile.stats.topShow || ''
						).length > 25
							? 'text-sm'
							: (profile.stats.topShow || '').length > 15
								? 'text-lg'
								: 'text-2xl sm:text-3xl'}">{profile.stats.topShow || '-'}</span
					>
					{#if profile.stats.topShowCount}
						<span class="text-lg font-extrabold text-gray-500 dark:text-gray-400 mt-2">
							{profile.stats.topShowCount}
							{$t('dashboard.theater.times')}
						</span>
					{/if}
					<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
						>{$t('dashboard.theater.topShow')}</span
					>
				</div>
			</div>

			<!-- Right Column: Recent Activity -->
			<div class="glass-panel p-6 rounded-3xl flex flex-col h-full">
				<h3 class="font-black text-xl tracking-tight text-gray-900 dark:text-white mb-6">
					{$t('profile.recentActivity.title')}
				</h3>

				<div class="flex-1 overflow-y-auto pr-2 custom-scrollbar">
					{#if profile.stats.recentActivity && profile.stats.recentActivity.length > 0}
						<div class="flex flex-col">
							{#each profile.stats.recentActivity as activity}
								<div class="flex items-stretch gap-4 group">
									<!-- Timeline Column -->
									<div class="flex-shrink-0 relative w-4 flex flex-col items-center">
										<!-- Line -->
										<div
											class="absolute top-2 bottom-0 w-0.5 bg-gray-300 dark:bg-zinc-700 -z-10 group-last:hidden"
										></div>

										<!-- Dot -->
										<div class="mt-1.5 relative z-10 bg-white dark:bg-gray-900 rounded-full">
											{#if activity.type === '2-Shot'}
												<div
													class="w-2.5 h-2.5 rounded-full bg-pink-500 ring-4 ring-pink-50 dark:ring-pink-900/20"
												></div>
											{:else}
												<div
													class="w-2.5 h-2.5 rounded-full bg-red-600 ring-4 ring-red-50 dark:ring-red-900/20"
												></div>
											{/if}
										</div>
									</div>

									<!-- Content Column -->
									<div
										class="flex-1 min-w-0 pb-6 border-b border-gray-100 dark:border-zinc-800/50 group-last:border-0 group-last:pb-0"
									>
										<p class="text-sm font-bold text-gray-900 dark:text-white line-clamp-1">
											{activity.title}
										</p>
										<p class="text-xs text-gray-400 font-medium mt-0.5">
											{new Date(activity.date).toLocaleDateString(undefined, {
												day: 'numeric',
												month: 'short',
												year: 'numeric'
											})}
										</p>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div
							class="h-full flex flex-col items-center justify-center text-center text-gray-400 py-8"
						>
							<Calendar class="w-8 h-8 mb-2 opacity-50" />
							<p class="text-xs">{$t('profile.recentActivity.noActivity')}</p>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Theater Map -->
		<TheaterSeatMap {rowStats} {seatStats} showSubtitle={false} />
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
	<div
		class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
		role="presentation"
		on:click={closePreviewModal}
		on:keydown={(e) => e.key === 'Escape' && closePreviewModal()}
	>
		<div
			class="bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl max-w-md w-full overflow-hidden animate-[fadeIn_0.2s_ease-out]"
			on:click|stopPropagation
			on:keydown|stopPropagation
			role="dialog"
			aria-modal="true"
			aria-labelledby="preview-modal-title"
			tabindex="-1"
		>
			<!-- Header -->
			<div
				class="flex items-center justify-between p-4 border-b border-gray-100 dark:border-zinc-800"
			>
				<h3 id="preview-modal-title" class="text-lg font-bold text-gray-900 dark:text-white">
					{$t('profile.profilePicture.previewTitle')}
				</h3>
				<button
					class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
					on:click={closePreviewModal}
				>
					<X class="w-5 h-5 text-gray-500" />
				</button>
			</div>

			<!-- Preview Image -->
			<div class="p-6 flex justify-center">
				<div
					class="w-48 h-48 rounded-full overflow-hidden border-4 border-gray-200 dark:border-zinc-700 shadow-lg"
				>
					<img src={previewImage} alt="Preview" class="w-full h-full object-cover" />
				</div>
			</div>

			<!-- Actions -->
			<div class="flex gap-3 p-4 border-t border-gray-100 dark:border-zinc-800">
				<button
					class="flex-1 py-3 px-4 rounded-xl font-bold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 transition-colors cursor-pointer disabled:cursor-not-allowed"
					on:click={closePreviewModal}
					disabled={isUploading}
				>
					{$t('common.cancel')}
				</button>
				<button
					class="flex-1 py-3 px-4 rounded-xl font-bold text-white bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 transition-all disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed flex items-center justify-center gap-2"
					on:click={confirmUpload}
					disabled={isUploading}
				>
					{#if isUploading}
						<Loader2 class="w-5 h-5 animate-spin" />
						{$t('common.loading')}
					{:else}
						{$t('common.save')}
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}
