<script lang="ts">
	import {
		User,
		Camera,
		Heart,
		LoaderCircle,
		Sparkles,
		PencilLine,
		Check,
		X,
		Quote
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { PublicProfileData } from '$lib/types';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { OptimizedImage } from '$lib/components/common';
	import { userProfile, showToast } from '$lib/stores';

	interface Props {
		profile: PublicProfileData;
		isCurrentUser?: boolean;
		isUploading?: boolean;
		ontriggerUpload?: () => void;
	}

	let { profile, isCurrentUser = false, isUploading = false, ontriggerUpload }: Props = $props();

	const { t } = useTranslation();

	let isEditingBio = $state(false);
	let isBioExpanded = $state(false);
	let bioValue = $state('');
	let isSavingBio = $state(false);

	$effect(() => {
		if (!isEditingBio) {
			bioValue = profile.bio || '';
		}
	});

	async function saveBio() {
		if (isSavingBio) return;
		isSavingBio = true;
		try {
			await userProfile.updateProfile({ bio: bioValue });
			profile.bio = bioValue;
			isEditingBio = false;
			showToast(t('settings.publicProfile.updateSuccess'), 'success');
		} catch (_e) {
			showToast(t('settings.publicProfile.updateError'), 'error');
		} finally {
			isSavingBio = false;
		}
	}

	function cancelEdit() {
		bioValue = profile.bio || '';
		isEditingBio = false;
	}
</script>

<div
	class="bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] p-5 sm:p-6 relative overflow-hidden group flex flex-col md:flex-row items-center gap-6 mb-6 sm:mb-8 shadow-2xl shadow-red-500/10 dark:shadow-red-950/40 transition-all duration-300 hover:shadow-red-500/15"
	role="region"
>
	<!-- Background decoration -->
	<div
		class="absolute top-0 right-0 w-64 h-64 bg-red-500/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"
	></div>

	<!-- JKT48 Wrapped Badge (Top Right) -->
	<div class="absolute top-3 right-3 sm:top-4 sm:right-4 z-20">
		<div
			class="inline-flex items-center gap-1.5 px-2.5 py-1 sm:px-3 sm:py-1.5 rounded-full bg-white/50 dark:bg-black/50 backdrop-blur-md border border-red-200/50 dark:border-red-900/30 shadow-sm hover:scale-105 transition-transform duration-300 cursor-default group/badge"
		>
			<Sparkles
				class="w-3 h-3 sm:w-3.5 sm:h-3.5 text-red-500 fill-red-500 dark:text-red-400 dark:fill-red-400 animate-pulse"
			/>
			<span
				class="text-[10px] sm:text-xs font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-600 to-pink-600 dark:from-red-400 dark:to-pink-400 uppercase tracking-wider"
			>
				{#if profile.publicYear}
					{t('profile.publicActivity.wrapped', { year: profile.publicYear })}
				{:else}
					{t('profile.publicActivity.allTime')}
				{/if}
			</span>
		</div>
	</div>

	<!-- Avatar -->
	<div class="relative group mt-2 sm:mt-0">
		<div
			class="w-28 h-28 sm:w-32 sm:h-32 rounded-full border-4 border-white dark:border-zinc-800 shadow-xl overflow-hidden bg-gray-100 dark:bg-zinc-800 relative"
		>
			{#if profile.profilePicture}
				<OptimizedImage
					src={profile.profilePicture}
					srcMedium={profile.profilePicture_medium}
					srcSmall={profile.profilePicture_small}
					alt={profile.name}
					blurHash={profile.blurHash}
					sizes="128px"
					class="w-full h-full object-cover"
				/>
			{:else}
				<div class="w-full h-full flex items-center justify-center text-gray-400">
					<User class="w-10 h-10 sm:w-12 sm:h-12" />
				</div>
			{/if}

			<!-- Edit Overlay -->
			{#if isCurrentUser}
				<button
					class="absolute inset-0 bg-black/50 flex items-center justify-center transition-opacity cursor-pointer disabled:cursor-not-allowed {isUploading
						? 'opacity-100'
						: 'opacity-0 group-hover:opacity-100'}"
					onclick={() => ontriggerUpload?.()}
					disabled={isUploading}
				>
					{#if isUploading}
						<div class="flex flex-col items-center gap-1.5">
							<LoaderCircle class="w-7 h-7 sm:w-8 sm:h-8 text-white animate-spin" />
							<span class="text-[8px] sm:text-[10px] text-white font-bold uppercase tracking-widest"
								>{t('common.loading')}</span
							>
						</div>
					{:else}
						<Camera class="w-7 h-7 sm:w-8 sm:h-8 text-white" />
					{/if}
				</button>
			{/if}
		</div>
		{#if profile.oshi}
			<div
				class="absolute -bottom-1 -right-1 sm:-bottom-2 sm:-right-2 bg-white dark:bg-zinc-800 rounded-full p-1 sm:p-1.5 shadow-md border border-gray-100 dark:border-zinc-700 tooltip-container"
			>
				<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full overflow-hidden border-2 border-pink-400">
					<OptimizedImage
						src={getExternalMediaUrl(profile.oshi.profilePicture)}
						srcMedium={getExternalMediaUrl(profile.oshi.profilePicture_medium)}
						srcSmall={getExternalMediaUrl(profile.oshi.profilePicture_small)}
						alt={profile.oshi.name}
						blurHash={profile.oshi.blurHash}
						sizes="40px"
						class="w-full h-full object-cover"
					/>
				</div>
			</div>
		{/if}
	</div>

	<!-- Info & Bio Container -->
	<div
		class="flex-1 flex flex-col md:flex-row items-center md:items-start justify-between gap-6 md:gap-12 min-w-0 w-full md:w-auto"
	>
		<!-- Left: User Info -->
		<div class="relative z-10 text-center md:text-left flex-shrink-0">
			<h1
				class="text-2xl sm:text-3xl font-black text-gray-900 dark:text-white leading-tight mb-1 sm:mb-2"
			>
				{profile.name}
			</h1>
			<p class="text-purple-600 dark:text-purple-400 font-bold mb-3 sm:mb-4 text-sm sm:text-base">
				@{profile.username}
			</p>

			{#if profile.oshi}
				<div class="flex flex-wrap justify-center md:justify-start gap-3">
					<div
						class="flex items-center gap-2 px-3 py-1.5 bg-pink-50 dark:bg-pink-900/20 rounded-full text-[10px] sm:text-xs font-bold text-pink-600 dark:text-pink-400 border border-pink-100/50 dark:border-pink-900/30"
					>
						<Heart class="w-3 h-3 sm:w-3.5 sm:h-3.5 fill-current" />
						Oshi: {profile.oshi.name}
					</div>
				</div>
			{/if}
		</div>

		<!-- Right: Bio (Quote Style) -->
		<div class="flex-1 w-full max-w-xl md:mt-12">
			{#if isEditingBio}
				<div class="flex flex-col gap-2">
					<div class="relative">
						<textarea
							bind:value={bioValue}
							class="w-full px-4 py-3 text-sm rounded-2xl border border-gray-200 dark:border-zinc-700 bg-white/50 dark:bg-zinc-800/50 text-gray-900 dark:text-white focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none resize-none transition-all duration-300"
							placeholder={t('settings.publicProfile.bioPlaceholder')}
							rows="3"
							maxlength="300"
						></textarea>
						<div
							class="absolute bottom-2 right-3 text-[10px] font-bold {bioValue.length >= 300
								? 'text-red-500'
								: 'text-gray-400'}"
						>
							{bioValue.length}/300
						</div>
					</div>
					<div class="flex items-center gap-2 justify-end">
						<button
							class="flex items-center gap-1.5 px-4 py-1.5 bg-red-500 hover:bg-red-600 text-white rounded-xl text-xs font-bold transition-all duration-300 disabled:opacity-50 shadow-lg shadow-red-500/20 cursor-pointer"
							onclick={saveBio}
							disabled={isSavingBio}
						>
							{#if isSavingBio}
								<LoaderCircle class="w-3.5 h-3.5 animate-spin" />
							{:else}
								<Check class="w-3.5 h-3.5" />
							{/if}
							{t('common.save')}
						</button>
						<button
							class="flex items-center gap-1.5 px-4 py-1.5 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 text-gray-600 dark:text-gray-400 rounded-xl text-xs font-bold transition-all duration-300 cursor-pointer"
							onclick={cancelEdit}
							disabled={isSavingBio}
						>
							<X class="w-3.5 h-3.5" />
							{t('common.cancel')}
						</button>
					</div>
				</div>
			{:else}
				<div class="relative group/bio">
					{#if profile.bio}
						<!-- svelte-ignore a11y_click_events_have_key_events -->
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<div
							class="relative px-8 py-2 md:py-0 cursor-pointer md:cursor-auto"
							onclick={() => (isBioExpanded = !isBioExpanded)}
						>
							<Quote
								class="absolute top-0 left-0 w-6 h-6 text-red-500/20 dark:text-red-400/10 -mt-2 -ml-1"
							/>
							<p
								class="text-sm sm:text-base text-gray-600 dark:text-gray-400 italic font-medium leading-relaxed whitespace-pre-wrap transition-all duration-500 {isBioExpanded
									? 'line-clamp-none'
									: 'line-clamp-4 md:group-hover/bio:line-clamp-none'}"
							>
								{profile.bio}
							</p>
							<Quote
								class="absolute bottom-0 right-0 w-6 h-6 text-red-500/20 dark:text-red-400/10 rotate-180 -mb-2 -mr-1"
							/>
						</div>
					{:else if isCurrentUser}
						<p class="text-sm text-gray-400 italic font-medium px-8 py-2 md:py-0">
							{t('settings.publicProfile.noBio')}
						</p>
					{/if}

					{#if isCurrentUser}
						<button
							class="absolute -top-6 right-0 p-1.5 text-gray-400 hover:text-red-500 md:opacity-0 md:group-hover/bio:opacity-100 transition-all duration-300 bg-white/50 dark:bg-zinc-800/50 rounded-full backdrop-blur-sm border border-gray-100 dark:border-zinc-700 cursor-pointer"
							onclick={() => (isEditingBio = true)}
							title="Edit Bio"
						>
							<PencilLine class="w-3.5 h-3.5" />
						</button>
					{/if}
				</div>
			{/if}
		</div>
	</div>
</div>
