<script lang="ts">
	import { userProfile, showToast } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		User,
		Mail,
		AtSign,
		BadgeCheck,
		ShieldCheck,
		LoaderCircle,
		Info,
		Pencil,
		X,
		Camera,
		IdCard,
		Eye,
		EyeOff
	} from 'lucide-svelte';
	import { logger } from '$lib/utils/logger';
	import { fade, slide } from 'svelte/transition';
	import { ErrorState, EmptyState } from '$lib/components';
	import { OptimizedImage } from '$lib/components/common';
	import ImageCropperModal from '$lib/components/common/ImageCropperModal.svelte';
	import { getErrorMessage } from '$lib/utils/api';
	import { maskEmail } from '$lib/utils/formatting';

	const { t } = useTranslation();

	let isSaving = $state(false);
	let isEditing = $state(false);
	let showCropper = $state(false);
	let previewImage = $state<string | null>(null);
	let showEmail = $state(false);

	// Form state
	let name = $state(userProfile.data?.name || '');
	let username = $state(userProfile.data?.username || '');
	let email = $state(userProfile.data?.email || '');
	let bio = $state(userProfile.data?.bio || '');

	// Reset form when store data changes or when canceling
	$effect(() => {
		if (userProfile.data && !isEditing) {
			name = userProfile.data.name || '';
			username = userProfile.data.username || '';
			email = userProfile.data.email || '';
			bio = userProfile.data.bio || '';
		}
	});

	const handleSave = async () => {
		if (isSaving) return;

		isSaving = true;
		try {
			const payload: { name?: string; username?: string; email?: string; bio?: string } = {};
			if (name !== userProfile.data?.name) payload.name = name;
			if (username !== userProfile.data?.username) payload.username = username;
			if (email !== userProfile.data?.email) payload.email = email;
			if (bio !== userProfile.data?.bio) payload.bio = bio;

			if (Object.keys(payload).length === 0) {
				isEditing = false;
				return;
			}

			await userProfile.updateProfile(payload);
			showToast(t('settings.account.saveSuccess'), 'success');
			isEditing = false;
		} catch (e: unknown) {
			logger.error('Failed to update account settings', e, { context: 'AccountSettings' });
			const errorMessage = getErrorMessage(e);
			showToast(errorMessage || t('settings.account.saveError'), 'error');
		} finally {
			isSaving = false;
		}
	};

	const toggleEdit = () => {
		if (isEditing) {
			// Cancel
			name = userProfile.data?.name || '';
			username = userProfile.data?.username || '';
			email = userProfile.data?.email || '';
			bio = userProfile.data?.bio || '';
		}
		isEditing = !isEditing;
	};

	const onFileSelected = (e: Event) => {
		const target = e.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			const reader = new FileReader();
			reader.onload = (re) => {
				previewImage = re.target?.result as string;
				showCropper = true;
			};
			reader.readAsDataURL(target.files[0]);
			// Reset input
			target.value = '';
		}
	};

	const onCropDone = async (base64: string) => {
		showCropper = false;
		try {
			await userProfile.updateAvatar(base64);
			showToast(t('settings.publicProfile.uploadSuccess'), 'success');
		} catch (err) {
			logger.error('Failed to upload profile picture', err);
			const errorMessage = getErrorMessage(err);
			showToast(errorMessage || t('settings.publicProfile.uploadError'), 'error');
		}
	};

	const formatDate = (dateStr: string | undefined) => {
		if (!dateStr) return '-';
		try {
			const date = new Date(dateStr);
			if (isNaN(date.getTime())) return '-';
			return date.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
		} catch {
			return '-';
		}
	};

	const retryFetch = async () => {
		try {
			await userProfile.load({ force: true });
		} catch (_e) {
			showToast(t('profile.errorTitle'), 'error');
		}
	};
</script>

{#if userProfile.isLoading && !userProfile.data}
	<!-- SKELETON LOADING -->
	<div class="glass-panel p-6 rounded-3xl animate-pulse space-y-8">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="w-10 h-10 rounded-xl bg-gray-200 dark:bg-zinc-800"></div>
				<div class="space-y-2">
					<div class="h-5 w-32 bg-gray-200 dark:bg-zinc-800 rounded"></div>
					<div class="h-3 w-48 bg-gray-200 dark:bg-zinc-800 rounded"></div>
				</div>
			</div>
			<div class="w-10 h-10 bg-gray-200 dark:bg-zinc-800 rounded-xl"></div>
		</div>

		<div class="flex flex-col sm:flex-row gap-8">
			<div class="w-24 h-24 sm:w-32 sm:h-32 bg-gray-200 dark:bg-zinc-800 rounded-3xl"></div>
			<div class="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6">
				{#each Array(3) as _}
					<div class="space-y-2">
						<div class="h-3 w-20 bg-gray-200 dark:bg-zinc-800 rounded"></div>
						<div class="h-10 w-full bg-gray-100 dark:bg-zinc-900 rounded-2xl"></div>
					</div>
				{/each}
			</div>
		</div>

		<div class="h-px bg-gray-100 dark:bg-zinc-800/50"></div>

		<div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
			{#each Array(4) as _}
				<div class="space-y-2">
					<div class="h-2 w-16 bg-gray-200 dark:bg-zinc-800 rounded"></div>
					<div class="h-4 w-24 bg-gray-100 dark:bg-zinc-900 rounded"></div>
				</div>
			{/each}
		</div>
	</div>
{:else if userProfile.error}
	<div class="glass-panel p-6 rounded-3xl">
		<ErrorState
			title={t('profile.errorTitle')}
			description={t('profile.errorDesc')}
			onRetry={retryFetch}
		/>
	</div>
{:else if !userProfile.data}
	<div class="glass-panel p-6 rounded-3xl">
		<EmptyState icon={User} title={t('common.noResults')} description={t('profile.errorDesc')} />
	</div>
{:else}
	<div class="glass-panel p-6 rounded-3xl relative" in:fade>
		<!-- Subtle background decoration -->
		<div class="absolute inset-0 overflow-hidden rounded-3xl pointer-events-none">
			<div
				class="absolute top-0 right-0 w-48 h-48 bg-blue-50 dark:bg-blue-900/5 rounded-full -mr-24 -mt-24 blur-3xl opacity-50"
			></div>
		</div>

		<!-- Header -->
		<div class="flex items-center justify-between mb-8 relative">
			<div class="flex items-center gap-3">
				<div
					class="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center shadow-sm"
				>
					<User class="w-5 h-5 text-blue-600 dark:text-blue-400" />
				</div>
				<div>
					<h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">
						{t('settings.account.title')}
					</h3>
					<p class="text-xs text-gray-500 dark:text-gray-400">
						{t('settings.account.subtitle')}
					</p>
				</div>
			</div>

			<div class="flex items-center gap-2">
				{#if !isEditing}
					<button
						onclick={toggleEdit}
						class="p-2.5 rounded-xl bg-gray-50 dark:bg-zinc-800 text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all active:scale-95 cursor-pointer"
						title={t('common.edit')}
					>
						<Pencil class="w-5 h-5" />
					</button>
				{:else}
					<button
						onclick={toggleEdit}
						class="p-2.5 rounded-xl bg-red-50 dark:bg-red-900/10 text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/20 transition-all active:scale-95 cursor-pointer"
						title={t('common.cancel')}
					>
						<X class="w-5 h-5" />
					</button>
				{/if}
			</div>
		</div>

		<div class="space-y-8 relative">
			<div class="flex flex-col sm:flex-row gap-8 items-start">
				<!-- LEFT: PROFILE PICTURE -->
				<div class="flex-shrink-0 mx-auto sm:mx-0">
					<div class="relative group">
						<div
							class="w-24 h-24 sm:w-32 sm:h-32 rounded-3xl overflow-hidden bg-gray-100 dark:bg-zinc-800 shadow-inner border-4 border-white dark:border-zinc-700 relative"
						>
							{#if userProfile.data.profilePicture}
								<OptimizedImage
									src={userProfile.data.profilePicture}
									srcMedium={userProfile.data.profilePicture_medium}
									srcSmall={userProfile.data.profilePicture_small}
									blurHash={userProfile.data.blurHash}
									alt={userProfile.data.name}
									class="w-full h-full object-cover transition-transform group-hover:scale-110"
									sizes="(max-width: 640px) 96px, 128px"
								/>
							{:else}
								<div class="w-full h-full flex items-center justify-center text-gray-400">
									<User class="w-10 h-10" />
								</div>
							{/if}

							<!-- Overlay on hover -->
							<label
								for="pfp-upload"
								class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
							>
								<div class="flex flex-col items-center gap-1">
									<Camera class="w-6 h-6 text-white" />
									<span class="text-[8px] text-white font-bold uppercase tracking-widest"
										>{t('common.edit')}</span
									>
								</div>
								<input
									id="pfp-upload"
									name="avatar"
									type="file"
									accept="image/*"
									class="hidden"
									onchange={onFileSelected}
									disabled={userProfile.isUpdatingAvatar}
								/>
							</label>

							<!-- Loading Indicator -->
							{#if userProfile.isUpdatingAvatar}
								<div
									class="absolute inset-0 bg-black/60 backdrop-blur-[2px] flex flex-col items-center justify-center z-10"
									in:fade={{ duration: 200 }}
								>
									<LoaderCircle class="w-8 h-8 text-white animate-spin mb-2" />
									<span class="text-[10px] text-white font-bold uppercase tracking-widest"
										>{t('common.loading')}</span
									>
								</div>
							{/if}
						</div>
					</div>
				</div>

				<!-- RIGHT: EDITABLE FIELDS -->
				<div class="flex-1 grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 w-full">
					<!-- Name -->
					<div class="space-y-1.5">
						<svelte:element
							this={isEditing ? 'label' : 'span'}
							for={isEditing ? 'acc-name' : undefined}
							class="text-[10px] font-black text-gray-400 dark:text-gray-500 uppercase tracking-[0.15em] pl-1"
						>
							{t('settings.account.fullName')}
						</svelte:element>
						{#if isEditing}
							<div class="relative group" in:slide={{ duration: 200 }}>
								<div
									class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400 group-focus-within:text-blue-500 transition-colors"
								>
									<User class="w-4 h-4" />
								</div>
								<input
									id="acc-name"
									type="text"
									bind:value={name}
									class="w-full pl-10 pr-4 py-3 bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-700 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all dark:text-white"
								/>
							</div>
						{:else}
							<div class="px-1" in:fade>
								<p class="text-base font-bold text-gray-800 dark:text-gray-200">
									{userProfile.data.name || '-'}
								</p>
							</div>
						{/if}
					</div>

					<!-- Username -->
					<div class="space-y-1.5">
						<svelte:element
							this={isEditing ? 'label' : 'span'}
							for={isEditing ? 'acc-username' : undefined}
							class="text-[10px] font-black text-gray-400 dark:text-gray-500 uppercase tracking-[0.15em] pl-1"
						>
							{t('settings.account.username')}
						</svelte:element>
						{#if isEditing}
							<div class="relative group" in:slide={{ duration: 200 }}>
								<div
									class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400 group-focus-within:text-blue-500 transition-colors"
								>
									<AtSign class="w-4 h-4" />
								</div>
								<input
									id="acc-username"
									type="text"
									bind:value={username}
									class="w-full pl-10 pr-4 py-3 bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-700 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all dark:text-white"
								/>
							</div>
						{:else}
							<div class="px-1" in:fade>
								<p class="text-base font-bold text-gray-800 dark:text-gray-200">
									@{userProfile.data.username || '-'}
								</p>
							</div>
						{/if}
					</div>

					<!-- Email -->
					<div class="space-y-1.5 md:col-span-2">
						<svelte:element
							this={isEditing ? 'label' : 'span'}
							for={isEditing ? 'acc-email' : undefined}
							class="text-[10px] font-black text-gray-400 dark:text-gray-500 uppercase tracking-[0.15em] pl-1"
						>
							{t('settings.account.email')}
						</svelte:element>
						{#if isEditing}
							<div class="space-y-2" in:slide={{ duration: 200 }}>
								<div class="relative group">
									<div
										class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400 group-focus-within:text-blue-500 transition-colors"
									>
										<Mail class="w-4 h-4" />
									</div>
									<input
										id="acc-email"
										type="email"
										bind:value={email}
										class="w-full pl-10 pr-4 py-3 bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-700 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all dark:text-white"
									/>
								</div>
								{#if email !== userProfile.data.email}
									<p
										class="text-[10px] text-amber-600 dark:text-amber-400 font-medium pl-1 flex items-center gap-1"
									>
										<Info class="w-3 h-3" />
										{t('settings.account.emailWarning')}
									</p>
								{/if}
							</div>
						{:else}
							<div class="px-1 flex items-center gap-2 min-w-0" in:fade>
								<p class="text-base font-bold text-gray-800 dark:text-gray-200 truncate">
									{showEmail ? userProfile.data.email || '-' : maskEmail(userProfile.data.email)}
								</p>
								<div class="flex items-center gap-1 shrink-0">
									<button
										type="button"
										onclick={() => (showEmail = !showEmail)}
										class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer"
										title={showEmail ? t('common.hide') : t('common.show')}
									>
										{#if showEmail}
											<EyeOff class="w-4 h-4" />
										{:else}
											<Eye class="w-4 h-4" />
										{/if}
									</button>
									<button
										type="button"
										class="relative group/tooltip focus:outline-none"
										tabindex="0"
									>
										{#if userProfile.data.isEmailVerified}
											<ShieldCheck
												class="w-4 h-4 text-blue-500 cursor-help group-focus/tooltip:text-blue-600 transition-colors"
											/>
											<div
												class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 dark:bg-zinc-800 text-white text-[10px] rounded-lg opacity-0 group-hover/tooltip:opacity-100 group-focus/tooltip:opacity-100 transition-all pointer-events-none whitespace-nowrap z-20 shadow-xl border border-white/10"
											>
												{t('settings.account.verified')}
												<div
													class="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-gray-900 dark:border-t-zinc-800"
												></div>
											</div>
										{:else}
											<Info
												class="w-4 h-4 text-amber-500 cursor-help group-focus/tooltip:text-amber-600 transition-colors"
											/>
											<div
												class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 dark:bg-zinc-800 text-white text-[10px] rounded-lg opacity-0 group-hover/tooltip:opacity-100 group-focus/tooltip:opacity-100 transition-all pointer-events-none whitespace-nowrap z-20 shadow-xl border border-white/10"
											>
												{t('settings.account.unverified')}
												<div
													class="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-gray-900 dark:border-t-zinc-800"
												></div>
											</div>
										{/if}
									</button>
								</div>
							</div>
						{/if}
					</div>

					<!-- Bio -->
					<div class="space-y-1.5 md:col-span-2">
						<svelte:element
							this={isEditing ? 'label' : 'span'}
							for={isEditing ? 'acc-bio' : undefined}
							class="text-[10px] font-black text-gray-400 dark:text-gray-500 uppercase tracking-[0.15em] pl-1"
						>
							{t('settings.account.bio')}
						</svelte:element>
						{#if isEditing}
							<div class="relative group" in:slide={{ duration: 200 }}>
								<textarea
									id="acc-bio"
									bind:value={bio}
									class="w-full px-4 py-3 bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-700 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all dark:text-white resize-none"
									rows="3"
									maxlength="300"
									placeholder={t('settings.publicProfile.bioPlaceholder')}
								></textarea>
								<div
									class="absolute bottom-3 right-4 text-[10px] font-bold {bio.length >= 300
										? 'text-red-500'
										: 'text-gray-400'}"
								>
									{bio.length}/300
								</div>
							</div>
						{:else}
							<div class="px-1" in:fade>
								<p
									class="text-base font-bold text-gray-800 dark:text-gray-200 whitespace-pre-wrap line-clamp-2"
								>
									{userProfile.data.bio || '-'}
								</p>
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- ACTION BUTTONS (Only when editing) -->
			{#if isEditing}
				<div class="pt-2 grid grid-cols-2 gap-3" transition:slide>
					<button
						onclick={toggleEdit}
						class="py-3 px-4 bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-gray-300 font-bold rounded-2xl hover:bg-gray-200 dark:hover:bg-zinc-700 transition-all active:scale-[0.98] cursor-pointer"
					>
						{t('common.cancel')}
					</button>
					<button
						onclick={handleSave}
						disabled={isSaving}
						class="py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-bold rounded-2xl shadow-lg shadow-blue-500/20 transition-all flex items-center justify-center gap-2 active:scale-[0.98] cursor-pointer"
					>
						{#if isSaving}
							<LoaderCircle class="w-5 h-5 animate-spin" />
						{:else}
							<span>{t('common.save')}</span>
						{/if}
					</button>
				</div>
			{/if}

			<!-- DIVIDER -->
			<div class="h-px bg-gray-100 dark:bg-zinc-800/50 w-full"></div>

			<!-- SYSTEM INFO -->
			<div class="space-y-6">
				<div class="flex items-center gap-3">
					<div
						class="w-8 h-8 rounded-lg bg-gray-50 dark:bg-zinc-800 flex items-center justify-center"
					>
						<IdCard class="w-4 h-4 text-gray-400" />
					</div>
					<h4 class="text-sm font-bold text-gray-700 dark:text-gray-300">
						{t('settings.account.systemInfo')}
					</h4>
				</div>

				<div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
					<!-- Member ID -->
					<div class="space-y-1">
						<p
							class="text-[9px] font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest pl-1"
						>
							{t('settings.account.memberId')}
						</p>
						<p class="text-xs font-mono font-bold text-gray-800 dark:text-gray-200 px-1">
							{userProfile.data.memberId || '-'}
						</p>
					</div>

					<!-- Joined Date -->
					<div class="space-y-1">
						<p
							class="text-[9px] font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest pl-1"
						>
							{t('settings.account.memberSince')}
						</p>
						<p class="text-xs font-bold text-gray-800 dark:text-gray-200 px-1">
							{formatDate(userProfile.data.createdAt)}
						</p>
					</div>

					<!-- OFC Status -->
					<div class="space-y-1">
						<p
							class="text-[9px] font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest pl-1"
						>
							{t('settings.account.ofcStatus')}
						</p>
						<div class="flex items-center gap-1.5 px-1">
							<div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
							<p class="text-xs font-bold text-emerald-600 dark:text-emerald-400">
								{userProfile.data.ofcStatus || 'Active'}
							</p>
						</div>
					</div>

					<!-- Account Type -->
					<div class="space-y-1">
						<p
							class="text-[9px] font-black {userProfile.data.isAdmin
								? 'text-amber-600/60 dark:text-amber-400/60'
								: 'text-gray-400 dark:text-gray-500'} uppercase tracking-widest pl-1"
						>
							{t('settings.account.type')}
						</p>
						<div class="flex items-center gap-1.5 px-1">
							{#if userProfile.data.isAdmin}
								<BadgeCheck class="w-3.5 h-3.5 text-amber-500" />
								<p class="text-xs font-black text-amber-600 dark:text-amber-400">
									{t('settings.account.admin')}
								</p>
							{:else}
								<User class="w-3.5 h-3.5 text-red-500" />
								<p class="text-xs font-black text-red-600 dark:text-red-400">
									{t('settings.account.wota')}
								</p>
							{/if}
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}

{#if showCropper && previewImage}
	<ImageCropperModal
		imageUrl={previewImage}
		onSave={onCropDone}
		onClose={() => (showCropper = false)}
	/>
{/if}
