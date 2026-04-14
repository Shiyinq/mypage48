<script lang="ts">
	import { page } from '$app/stores';
	import { ArrowRight, Menu, X, Sparkles } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import LanguageToggle from './LanguageToggle.svelte';
	import LandingPageThemeToggle from './ThemeToggle.svelte';
	import { isAuthenticated } from '$lib/stores';
	import { fade, fly } from 'svelte/transition';
	import { liveStore, liveList } from '$lib/stores/live.svelte';
	import { onMount } from 'svelte';
	import RadioEngine from './radio-player/RadioEngine.svelte';
	import RadioWidget from './radio-player/RadioWidget.svelte';
	import MobileRadioWidget from './radio-player/MobileRadioWidget.svelte';
	import NavLogo from '$lib/components/navigation/NavLogo.svelte';
	import NavPills from '$lib/components/navigation/NavPills.svelte';

	const { t } = useTranslation();

	interface Props {
		showLogin?: boolean;
		mouse?: { x: number; y: number };
	}

	let { showLogin = true, mouse = { x: 0, y: 0 } }: Props = $props();

	let isMenuOpen = $state(false);
	let lastScrollY = 0;
	let isHidden = $state(false);
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

	onMount(() => {
		liveStore.loadLiveList();
	});

	let navItems = $derived([
		{ label: $t('landing.nav.news'), href: '/jkt48/news' },
		{ label: $t('landing.nav.members'), href: '/jkt48/members' },
		{ label: $t('landing.nav.events'), href: '/jkt48/events' },
		{ label: $t('landing.nav.calendar'), href: '/jkt48/calendar' },
		{ label: $t('landing.nav.sorter'), href: '/jkt48/sorter' },
		{ label: $t('landing.nav.live'), href: '/jkt48/live', id: 'live' }
	]);

	function toggleMenu() {
		isMenuOpen = !isMenuOpen;
		if (isMenuOpen) {
			document.body.style.overflow = 'hidden';
		} else {
			document.body.style.overflow = '';
		}
	}

	function closeMenu() {
		isMenuOpen = false;
		document.body.style.overflow = '';
	}
</script>

<svelte:window onscroll={handleScroll} />

<nav
	class="sticky top-0 z-[100] flex justify-between items-center px-6 py-3 max-w-7xl mx-auto pointer-events-none transition-transform duration-300 ease-in-out {isHidden
		? '-translate-y-full'
		: 'translate-y-0'}"
>
	<!-- Left: Logo -->
	<div class="flex-1 flex items-center justify-start">
		<a href="/" class="flex items-center gap-3 group pointer-events-auto" onclick={closeMenu}>
			<NavLogo tagline={$t('landing.nav.subtitle')} {mouse} />
		</a>
	</div>

	<!-- Center: Public Navigation (Desktop) -->
	<NavPills
		items={navItems}
		currentPath={$page.url.pathname}
		className="hidden lg:flex pointer-events-auto"
	>
		{#snippet item({ item, isActive })}
			{item.label}
			{#if item.id === 'live' && (liveList.value?.length ?? 0) > 0}
				<span class="relative flex h-2 w-2">
					<span
						class="animate-ping absolute inline-flex h-full w-full rounded-full {isActive
							? 'bg-white/70'
							: 'bg-red-400 opacity-75'}"
					></span>
					<span
						class="relative inline-flex rounded-full h-2 w-2 {isActive ? 'bg-white' : 'bg-red-500'}"
					></span>
				</span>
			{/if}
		{/snippet}
	</NavPills>

	<!-- Right: Actions -->
	<div class="flex-1 flex items-center justify-end gap-2 sm:gap-3 pointer-events-auto">
		<RadioWidget />
		<div class="hidden sm:flex items-center gap-2 sm:gap-3">
			<LanguageToggle />
			<LandingPageThemeToggle />
		</div>

		{#if isAuthenticated.value}
			<a
				href="/"
				class="flex px-4 sm:px-6 py-2 rounded-full bg-slate-100 dark:bg-zinc-800 text-slate-900 dark:text-white font-bold text-xs sm:text-sm hover:bg-slate-200 dark:hover:bg-zinc-700 transition-all items-center gap-2 group"
			>
				{$t('nav.dashboard')}
				<ArrowRight size={14} class="group-hover:translate-x-1 transition-transform" />
			</a>
		{:else if showLogin}
			<a
				href="/login"
				class="flex px-4 sm:px-6 py-2 rounded-full bg-red-600 text-white font-bold text-xs sm:text-sm shadow-xl shadow-red-500/30 hover:shadow-red-500/50 hover:-translate-y-0.5 transition-all items-center gap-2 group"
			>
				{$t('auth.login.signIn')}
				<ArrowRight size={14} class="group-hover:translate-x-1 transition-transform" />
			</a>
		{/if}

		<!-- Mobile Menu Toggle -->
		<button
			class="lg:hidden p-2.5 rounded-full bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 text-slate-900 dark:text-white shadow-sm transition-all active:scale-95 cursor-pointer"
			onclick={toggleMenu}
			aria-label="Toggle Menu"
		>
			{#if isMenuOpen}
				<X size={20} />
			{:else}
				<Menu size={20} />
			{/if}
		</button>
	</div>
</nav>

<!-- Mobile Menu Overlay -->
{#if isMenuOpen}
	<div class="fixed inset-0 z-[90] lg:hidden" transition:fade={{ duration: 200 }}>
		<!-- Backdrop -->
		<button
			class="absolute inset-0 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-xl cursor-default w-full h-full border-none p-0"
			onclick={closeMenu}
			aria-label="Close Menu"
		></button>

		<!-- Menu Content -->
		<div
			class="absolute inset-x-0 top-0 pt-24 pb-12 px-6 bg-white dark:bg-zinc-950 border-b border-gray-100 dark:border-zinc-900 shadow-2xl"
			transition:fly={{ y: -20, duration: 300 }}
		>
			<div class="flex flex-col gap-2">
				{#each navItems as item, i}
					{@const isActive = $page.url.pathname.startsWith(item.href)}
					<a
						href={item.href}
						onclick={closeMenu}
						class="flex items-center justify-between p-4 rounded-2xl transition-all {isActive
							? 'bg-red-600 text-white shadow-xl shadow-red-500/20'
							: 'text-slate-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-zinc-900'}"
						transition:fly={{ y: 10, delay: i * 50, duration: 300 }}
					>
						<div class="flex items-center gap-3">
							<span class="text-sm font-black uppercase tracking-[0.2em]">{item.label}</span>
							{#if item.id === 'live' && (liveList.value?.length ?? 0) > 0}
								<span class="relative flex h-2.5 w-2.5">
									<span
										class="animate-ping absolute inline-flex h-full w-full rounded-full {isActive
											? 'bg-white/70'
											: 'bg-red-400 opacity-75'}"
									></span>
									<span
										class="relative inline-flex rounded-full h-2.5 w-2.5 {isActive
											? 'bg-white'
											: 'bg-red-500'}"
									></span>
								</span>
							{/if}
						</div>
						{#if isActive}
							<Sparkles size={16} />
						{:else}
							<ArrowRight size={16} class="opacity-50" />
						{/if}
					</a>
				{/each}

				<div class="h-px bg-gray-100 dark:bg-zinc-900 my-4"></div>

				<div class="flex items-center justify-between px-2">
					<div class="flex items-center gap-4">
						<MobileRadioWidget />
						<LanguageToggle />
						<LandingPageThemeToggle />
					</div>

					{#if !isAuthenticated.value && showLogin}
						<a
							href="/login"
							onclick={closeMenu}
							class="px-6 py-2.5 rounded-full bg-red-600 text-white font-black text-xs uppercase tracking-widest shadow-xl shadow-red-500/20"
						>
							{$t('auth.login.signIn')}
						</a>
					{:else if isAuthenticated.value}
						<a
							href="/"
							onclick={closeMenu}
							class="px-6 py-2.5 rounded-full bg-slate-100 dark:bg-zinc-800 text-slate-900 dark:text-white font-black text-xs uppercase tracking-widest shadow-sm"
						>
							{$t('nav.dashboard')}
						</a>
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- Persistent Audio Engine -->
<RadioEngine />
