<script lang="ts">
	import { page } from '$app/stores';
	import { Ticket, Plus, User } from 'lucide-svelte';
	import { userProfile, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import NavLogo from '$lib/components/navigation/NavLogo.svelte';
	import NavPills from '$lib/components/navigation/NavPills.svelte';

	const { t } = useTranslation();

	/* Loading State */
	let mounted = false;

	onMount(() => {
		mounted = true;
	});

	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded);
	
	let lastScrollY = 0;
	let isHidden = false;
	const threshold = 10;

	function handleScroll() {
		const currentScrollY = window.scrollY;
		const delta = Math.abs(currentScrollY - lastScrollY);

		if (delta < threshold) return;

		if (currentScrollY > lastScrollY && currentScrollY > 80) {
			isHidden = true;
		} else {
			isHidden = false;
		}
		lastScrollY = currentScrollY;
	}

	// Navigation items
	$: navItems = [
		{ label: $t('nav.dashboard'), href: '/' },
		{ label: $t('nav.theater'), href: '/theater/events', activeHref: '/theater' },
		{ label: $t('nav.achievements'), href: '/achievements' },
		{ label: $t('nav.journal'), href: '/journal' },
		{ label: $t('nav.memories'), href: '/memories' },
		{ label: $t('nav.history'), href: '/history' }
	];
</script>

<svelte:window on:scroll={handleScroll} />

<header
	class="bg-white/95 dark:bg-zinc-950/95 backdrop-blur-xl border-b border-gray-200 dark:border-zinc-800 sticky top-0 z-50 transition-transform duration-300 ease-in-out {isHidden ? '-translate-y-full' : 'translate-y-0'}"
>
	<div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
		<!-- Left: Logo -->
		<a href="/" class="flex items-center gap-3 cursor-pointer">
			<NavLogo tagline={$t('header.tagline')} />
		</a>

		<!-- Center: Desktop Navigation -->
		<NavPills
			items={navItems}
			currentPath={$page.url.pathname}
			className="hidden md:flex max-w-2xl"
		/>

		<!-- Right: Actions & Profile -->
		<div class="flex items-center gap-3">
			<!-- Desktop New Ticket Button -->
			<div class="hidden md:block">
				<a
					href="/upload"
					class="idol-gradient text-white px-6 py-2 rounded-full font-black text-[11px] uppercase tracking-widest shadow-xl shadow-red-500/20 hover:shadow-red-500/40 hover:-translate-y-0.5 transition-all flex items-center gap-2 group"
				>
					<Plus class="w-3.5 h-3.5 group-hover:rotate-90 transition-transform" />
					{$t('nav.newTicket')}
				</a>
			</div>

			<!-- Profile Icon Button -->
			<a
				href="/profile"
				class={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 relative overflow-hidden group
            ${
							$page.url.pathname === '/profile'
								? 'ring-2 ring-red-600 shadow-lg scale-105'
								: 'ring-1 ring-gray-200 dark:ring-gray-700 hover:ring-red-400'
						}`}
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
					class={`absolute inset-0 bg-red-500/20 transition-opacity ${$page.url.pathname === '/profile' ? 'opacity-0' : 'opacity-0 group-hover:opacity-100'}`}
				></div>
			</a>
		</div>
	</div>
</header>
