<script lang="ts">
	import { page } from '$app/stores';
	import { Home, User } from 'lucide-svelte';
	import { userProfile, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import NavLogo from '$lib/components/navigation/NavLogo.svelte';

	const { t } = useTranslation();

	/* Loading State */
	let mounted = false;

	onMount(() => {
		mounted = true;
	});

	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded);
</script>

<header
	class="bg-white/95 dark:bg-zinc-950/95 backdrop-blur-xl border-b border-gray-100 dark:border-zinc-800 sticky top-0 z-50 h-16"
>
	<div class="max-w-full mx-auto px-6 h-full flex items-center justify-between">
		<!-- Left: Logo + Title -->
		<div class="flex items-center gap-6">
			<a href="/" class="flex items-center gap-3 cursor-pointer group">
				<NavLogo tagline={$t('playground.tagline')} />
			</a>
			
			<div class="hidden md:flex items-center gap-2 px-3 py-1 bg-gray-100 dark:bg-zinc-800 rounded-lg border border-gray-200 dark:border-white/5">
				<span class="text-[10px] font-black uppercase tracking-widest text-red-500">v1.0</span>
				<div class="w-1 h-1 rounded-full bg-emerald-500 animate-pulse"></div>
				<span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Stable</span>
			</div>
		</div>

		<!-- Right: Actions & Profile -->
		<div class="flex items-center gap-4">
			<!-- Back to Dashboard -->
			<a
				href="/"
				class="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-white/5 text-xs font-bold text-gray-600 dark:text-gray-400 hover:text-red-500 dark:hover:text-red-400 hover:bg-white dark:hover:bg-zinc-800 transition-all shadow-sm group"
			>
				<Home class="w-3.5 h-3.5 group-hover:-translate-y-0.5 transition-transform" />
				<span class="hidden sm:inline">{$t('playground.backToDashboard')}</span>
			</a>

			<!-- Profile Icon Button -->
			<a
				href="/profile"
				class={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 relative overflow-hidden group ring-1 ring-gray-200 dark:ring-gray-700 hover:ring-red-400`}
			>
				{#if isLoading}
					<div class="w-full h-full bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
				{:else if $userProfile?.data?.oshi?.profilePicture || $userProfile?.data?.profilePicture}
					<img
						src={$userProfile?.data?.oshi?.profilePicture
							? getExternalMediaUrl($userProfile.data.oshi.profilePicture)
							: $userProfile?.data?.profilePicture}
						alt="Profile"
						class="w-full h-full object-cover"
					/>
				{:else}
					<div class="w-full h-full bg-gray-100 dark:bg-zinc-800 flex items-center justify-center">
						<User class="w-5 h-5 text-gray-400 dark:text-gray-500" />
					</div>
				{/if}
				<div
					class="absolute inset-0 bg-red-500/10 transition-opacity opacity-0 group-hover:opacity-100"
				></div>
			</a>
		</div>
	</div>
</header>
