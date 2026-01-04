<script lang="ts">
	import { User, Ticket, Camera, Heart, Loader2, Sparkles } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { createEventDispatcher } from 'svelte';
	import type { PublicProfileData } from '$lib/types';

	export let profile: PublicProfileData;
	export let isCurrentUser: boolean = false;
	export let isUploading: boolean = false;

	const { t } = useTranslation();
	const dispatch = createEventDispatcher();
</script>

<div
	class="bg-white/60 dark:bg-zinc-900/60 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-[2rem] p-6 relative overflow-hidden group flex flex-col md:flex-row items-center gap-6 mb-8 shadow-xl shadow-red-500/5"
	role="region"
>
	<!-- Background decoration -->
	<div
		class="absolute top-0 right-0 w-64 h-64 bg-red-500/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"
	></div>

	<!-- JKT48 Wrapped Badge (Top Right) -->
	{#if profile.publicYear}
		<div class="absolute top-4 right-4 z-20">
			<div
				class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/50 dark:bg-black/50 backdrop-blur-md border border-red-200/50 dark:border-red-900/30 shadow-sm hover:scale-105 transition-transform duration-300 cursor-default group/badge"
			>
				<Sparkles
					class="w-3.5 h-3.5 text-red-500 fill-red-500 dark:text-red-400 dark:fill-red-400 animate-pulse"
				/>
				<span
					class="text-xs font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-600 to-pink-600 dark:from-red-400 dark:to-pink-400 uppercase tracking-wider"
				>
					{$t('profile.publicActivity.wrapped', { year: profile.publicYear })}
				</span>
			</div>
		</div>
	{/if}

	<!-- Avatar -->
	<div class="relative group">
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
			{#if isCurrentUser}
				<button
					class="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer disabled:cursor-not-allowed"
					on:click={() => dispatch('triggerUpload')}
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

		{#if profile.oshi}
			<div class="flex flex-wrap justify-center md:justify-start gap-3">
				<div
					class="flex items-center gap-2 px-3 py-1.5 bg-pink-50 dark:bg-pink-900/20 rounded-full text-xs font-bold text-pink-600 dark:text-pink-400"
				>
					<Heart class="w-3.5 h-3.5 fill-current" />
					Oshi: {profile.oshi.name}
				</div>
			</div>
		{/if}
	</div>
</div>
