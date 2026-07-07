<script lang="ts">
	import { page } from '$app/stores';
	import { Plus, User, LayoutDashboard } from 'lucide-svelte';
	import { userProfile, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { isImmersive } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';
	import NavLogo from '$lib/components/navigation/NavLogo.svelte';
	import NavPills from '$lib/components/navigation/NavPills.svelte';
	import { theaterNavItems } from '$lib/constants/theaterNav';
	import { journeyNavItems } from '$lib/constants/journeyNav';
	import { getThemeStyles } from '$lib/constants/theaterTheme';
	import { safeCrossfade } from '$lib/utils/transitions';
	import { cubicInOut } from 'svelte/easing';
	import { slide } from 'svelte/transition';
	import { OptimizedImage } from '$lib/components/common';

	const [send, receive] = safeCrossfade({
		duration: 300,
		easing: cubicInOut
	});

	function safeSlide(node: HTMLElement, params: any) {
		if (typeof window !== 'undefined' && window.getComputedStyle(node).display === 'none') {
			return { duration: 0 };
		}
		return slide(node, params);
	}

	const { t } = useTranslation();

	/* Loading State */
	let mounted = $state(false);

	onMount(() => {
		mounted = true;
	});

	let isLoading = $derived(!mounted || (isAuthenticated.value && !isInitialDataLoaded.value));

	let navItems = $derived([
		{ label: t('nav.dashboard'), href: '/' },
		{
			label: t('nav.theater'),
			href: '/theater/events',
			match: (path: string) =>
				path.startsWith('/theater') && !path.startsWith('/live') && !path.startsWith('/sorter')
		},
		{
			label: t('nav.journey') || 'Perjalanan',
			href: '/memories',
			match: (path: string) =>
				['/memories', '/top-2shot', '/journal', '/achievements', '/history'].some((p) =>
					path.startsWith(p)
				)
		},
		{ label: t('nav.live') || 'Live', href: '/live' },
		{ label: t('nav.sorter') || 'Sorter', href: '/sorter' }
	]);

	let currentPath = $derived($page.url.pathname);
	let isTheater = $derived(
		currentPath.startsWith('/theater') &&
			!currentPath.startsWith('/live') &&
			!currentPath.startsWith('/sorter')
	);
	let isJourney = $derived(
		['/memories', '/top-2shot', '/journal', '/achievements', '/history'].some((path) =>
			currentPath.startsWith(path)
		)
	);

	let theaterIsActive = $derived((href: string, exact: boolean = false) => {
		if (href === '/theater/events') {
			return (
				currentPath === href ||
				(currentPath.startsWith(href + '/') &&
					!currentPath.includes('/history') &&
					!currentPath.includes('/calendar'))
			);
		}
		if (href === '/theater') {
			const parts = currentPath.split('/').filter(Boolean);
			if (parts.length === 1 && parts[0] === 'theater') return true;
			if (parts.length === 2 && parts[0] === 'theater') {
				return !['members', 'news', 'events', 'live', 'sorter'].includes(parts[1]);
			}
			return false;
		}
		if (exact) {
			return currentPath === href;
		}
		return currentPath.startsWith(href);
	});

	/* Profile Dropdown State */
	let isProfileDropdownOpen = $state(false);
	let profileDropdownRef: HTMLDivElement | undefined = $state();

	function handleOutsideClick(event: MouseEvent) {
		if (
			isProfileDropdownOpen &&
			profileDropdownRef &&
			!profileDropdownRef.contains(event.target as Node)
		) {
			isProfileDropdownOpen = false;
		}
	}
</script>

<svelte:window onclick={handleOutsideClick} />

{#if !isImmersive.value}
	<div
		class="hidden md:block transition-all duration-300 {isTheater || isJourney
			? 'h-[104px]'
			: 'h-16'}"
	></div>
	<header
		class="bg-white/95 dark:bg-zinc-950/95 backdrop-blur-xl border-b border-gray-200 dark:border-zinc-800 fixed top-0 left-0 right-0 z-[50] transition-all duration-300"
	>
		<div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
			<!-- Left: Logo -->
			<a href="/" class="flex items-center gap-3 cursor-pointer">
				<NavLogo tagline={t('header.tagline')} />
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
						{t('nav.newTicket')}
					</a>
				</div>

				<!-- Profile Icon Button & Dropdown -->
				<div class="relative" bind:this={profileDropdownRef}>
					{#snippet profileContent()}
						{#if isLoading}
							<div class="w-full h-full bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
						{:else if userProfile.data?.profilePicture}
							<OptimizedImage
								src={userProfile.data.profilePicture}
								srcMedium={userProfile.data.profilePicture_medium}
								srcSmall={userProfile.data.profilePicture_small}
								blurHash={userProfile.data?.blurHash}
								alt="Profile"
								class="w-full h-full object-cover"
								sizes="40px"
							/>
						{:else}
							<div
								class="w-full h-full bg-gray-100 dark:bg-zinc-800 flex items-center justify-center"
							>
								<User class="w-5 h-5 text-gray-400 dark:text-gray-500" />
							</div>
						{/if}
						<div
							class={`absolute inset-0 bg-red-500/20 transition-opacity ${$page.url.pathname === '/profile' ? 'opacity-0' : 'opacity-0 group-hover:opacity-100'}`}
						></div>
					{/snippet}

					{#if userProfile.data?.isAdmin}
						<button
							onclick={() => (isProfileDropdownOpen = !isProfileDropdownOpen)}
							class={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 relative overflow-hidden group cursor-pointer
								${
									$page.url.pathname === '/profile' || isProfileDropdownOpen
										? 'ring-2 ring-red-600 shadow-lg scale-105'
										: 'ring-1 ring-gray-200 dark:ring-gray-700 hover:ring-red-400'
								}`}
						>
							{@render profileContent()}
						</button>
					{:else}
						<a
							href="/profile"
							class={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 relative overflow-hidden group cursor-pointer
								${
									$page.url.pathname === '/profile'
										? 'ring-2 ring-red-600 shadow-lg scale-105'
										: 'ring-1 ring-gray-200 dark:ring-gray-700 hover:ring-red-400'
								}`}
						>
							{@render profileContent()}
						</a>
					{/if}

					<!-- Dropdown Menu -->
					{#if isProfileDropdownOpen}
						<div
							class="absolute right-0 mt-2 w-48 bg-white dark:bg-zinc-900 rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.3)] border border-gray-100 dark:border-zinc-800 py-2 z-50"
						>
							<a
								href="/profile"
								class="flex items-center gap-3 px-4 py-3 text-[10px] font-black uppercase tracking-widest text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors rounded-t-xl"
								onclick={() => (isProfileDropdownOpen = false)}
							>
								<User class="w-3.5 h-3.5" strokeWidth={2.5} />
								<span>{t('nav.profile') || 'Profile'}</span>
							</a>

							{#if userProfile.data?.isAdmin}
								<div class="h-px bg-gray-100 dark:bg-zinc-800/80 my-1"></div>
								<a
									href="/admin"
									class="flex items-center gap-3 px-4 py-3 text-[10px] font-black uppercase tracking-widest text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors rounded-b-xl"
									onclick={() => (isProfileDropdownOpen = false)}
								>
									<LayoutDashboard class="w-3.5 h-3.5" strokeWidth={2.5} />
									<span>{t('nav.admin') || 'Admin Dashboard'}</span>
								</a>
							{/if}
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Sub Navigation -->
		{#if isTheater || isJourney}
			<div
				class="max-w-7xl mx-auto px-4 pb-2 hidden md:block"
				transition:safeSlide={{ duration: 300, axis: 'y' }}
			>
				<div
					class="flex items-center gap-1 bg-gray-50/50 dark:bg-zinc-900/30 backdrop-blur-md border border-gray-100 dark:border-zinc-800/50 p-1 rounded-full shadow-sm w-fit mx-auto"
				>
					{#if isTheater}
						{#each theaterNavItems as item (item.href)}
							{@const active = theaterIsActive(item.href, item.exact)}
							{@const itemTheme = getThemeStyles(item.theme || 'purple')}
							<a
								href={item.href}
								class="relative px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest transition-all duration-200 flex items-center justify-center whitespace-nowrap {active
									? 'text-white'
									: 'text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white hover:bg-white/80 dark:hover:bg-zinc-800'}"
							>
								{#if active}
									<div
										class="absolute inset-0 rounded-full shadow-lg z-0 {itemTheme.navActive}"
										in:receive={{ key: 'theater-nav-active' }}
										out:send={{ key: 'theater-nav-active' }}
									></div>
								{/if}
								<span class="relative z-10 flex items-center justify-center">
									<span>{t(item.labelKey) || item.labelDefault}</span>
								</span>
							</a>
						{/each}
					{:else if isJourney}
						{#each journeyNavItems as item (item.href)}
							{@const active = currentPath.startsWith(item.href)}
							{@const itemTheme = getThemeStyles(item.theme || 'purple')}
							<a
								href={item.href}
								class="relative px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest transition-all duration-200 flex items-center justify-center whitespace-nowrap {active
									? 'text-white'
									: 'text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white hover:bg-white/80 dark:hover:bg-zinc-800'}"
							>
								{#if active}
									<div
										class="absolute inset-0 rounded-full shadow-lg z-0 {itemTheme.navActive}"
										in:receive={{ key: 'journey-nav-active' }}
										out:send={{ key: 'journey-nav-active' }}
									></div>
								{/if}
								<span class="relative z-10 flex items-center justify-center">
									<span>{t(item.labelKey)}</span>
								</span>
							</a>
						{/each}
					{/if}
				</div>
			</div>
		{/if}
	</header>
{/if}
