<script lang="ts">
	import { User, Camera, Heart, LoaderCircle, Sparkles } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { createEventDispatcher } from 'svelte';
	import type { PublicProfileData } from '$lib/types';
	import { getExternalMediaUrl } from '$lib/utils/media';

	interface Props {
		profile: PublicProfileData;
		isCurrentUser?: boolean;
		isUploading?: boolean;
	}

	let { profile, isCurrentUser = false, isUploading = false }: Props = $props();

	const { t } = useTranslation();
	const dispatch = createEventDispatcher();
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
	{#if profile.publicYear}
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
					{$t('profile.publicActivity.wrapped', { year: profile.publicYear })}
				</span>
			</div>
		</div>
	{/if}

	<!-- Avatar -->
	<div class="relative group mt-2 sm:mt-0">
		<div
			class="w-28 h-28 sm:w-32 sm:h-32 rounded-full border-4 border-white dark:border-zinc-800 shadow-xl overflow-hidden bg-gray-100 dark:bg-zinc-800 relative"
		>
			{#if profile.profilePicture}
				<img src={profile.profilePicture} alt={profile.name} class="w-full h-full object-cover" />
			{:else}
				<div class="w-full h-full flex items-center justify-center text-gray-400">
					<User class="w-10 h-10 sm:w-12 sm:h-12" />
				</div>
			{/if}

			<!-- Edit Overlay -->
			{#if isCurrentUser}
				<button
					class="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer disabled:cursor-not-allowed"
					onclick={() => dispatch('triggerUpload')}
					disabled={isUploading}
				>
					{#if isUploading}
						<LoaderCircle class="w-7 h-7 sm:w-8 sm:h-8 text-white animate-spin" />
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
					<img
						src={getExternalMediaUrl(profile.oshi.profilePicture)}
						alt={profile.oshi.name}
						class="w-full h-full object-cover"
					/>
				</div>
			</div>
		{/if}
	</div>

	<!-- Info -->
	<div class="relative z-10 text-center md:text-left">
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
					class="flex items-center gap-2 px-3 py-1.5 bg-pink-50 dark:bg-pink-900/20 rounded-full text-[10px] sm:text-xs font-bold text-pink-600 dark:text-pink-400"
				>
					<Heart class="w-3 h-3 sm:w-3.5 sm:h-3.5 fill-current" />
					Oshi: {profile.oshi.name}
				</div>
			</div>
		{/if}
	</div>
</div>
