<script lang="ts">
	import '../app.css';
	import { isAuthenticated, toast, userProfile, isInitialDataLoaded } from '$lib/stores';
	import { locale, type Locale } from '$lib/i18n';
	import { initTheme } from '$lib/stores/theme';
	import { auth } from '$lib/apis/auth';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get } from 'svelte/store';
	import Header from '$lib/components/Header.svelte';
	import MobileHeader from '$lib/components/navigation/MobileHeader.svelte';
	import PlaygroundHeader from '$lib/components/playground/PlaygroundHeader.svelte';
	import MobileNav from '$lib/components/MobileNav.svelte';
	import { Check } from 'lucide-svelte';
	import SplashScreen from '$lib/components/SplashScreen.svelte';
	import LoadingBar from '$lib/components/LoadingBar.svelte';
	import { logger } from '$lib/utils/logger';
	import { validateEnv } from '$lib/utils/env';
	import ErrorFallback from '$lib/components/common/ErrorFallback.svelte';
	import CommandPalette from '$lib/components/CommandPalette.svelte';
	import ScrollToTop from '$lib/components/common/ScrollToTop.svelte';
	import LandingNavbar from '$lib/components/landing-page/LandingNavbar.svelte';
	import Footer from '$lib/components/landing-page/Footer.svelte';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';

	export let data: { locale?: string };

	// Hydrate locale from server cookie if available (SSR)
	if (data?.locale) {
		locale.set(data.locale as Locale);
	}

	// Flag to prevent duplicate fetches
	let hasFetchedInitialData = false;

	// Determine if current page is public (accessible without login)
	$: isPublicPage =
		$page.url.pathname === '/' ||
		$page.url.pathname === '/login' ||
		$page.url.pathname === '/register' ||
		$page.url.pathname === '/privacy' ||
		$page.url.pathname === '/terms' ||
		$page.url.pathname === '/cookies' ||
		$page.url.pathname === '/about' ||
		$page.url.pathname.startsWith('/auth/') ||
		$page.url.pathname.startsWith('/u/') ||
		[
			'/jkt48/members',
			'/jkt48/news',
			'/jkt48/events',
			'/jkt48/calendar',
			'/jkt48/event-history',
			'/jkt48/sorter',
			'/jkt48/live'
		].some((path) => $page.url.pathname.startsWith(path));

	// Determine if current page is strictly for guests (login/register pages)
	// Logged in users should be redirected AWAY from these pages
	$: isGuestRoute =
		$page.url.pathname === '/login' ||
		$page.url.pathname === '/register' ||
		$page.url.pathname.startsWith('/auth/');

	$: isFullScreenRoute = $page.url.pathname.includes('/live/multiview');
	$: isPlaygroundRoute = $page.url.pathname.startsWith('/playground');

	// Track if client has mounted - used to delay auth redirects
	let mounted = false;

	// Global Error Handling
	let appError: Error | null = null;

	function handleGlobalError(event: ErrorEvent) {
		// Don't catch 404s or other navigation errors which are handled by SvelteKit
		if (event.message.includes('Not found') || event.message.includes('404')) return;

		logger.error('Global unhandled error', event.error, { context: 'GlobalBoundary' });
		appError = event.error;
	}

	function handleUnhandledRejection(event: PromiseRejectionEvent) {
		logger.error('Unhandled promise rejection', event.reason, { context: 'GlobalBoundary' });
		// Optional: decide if unhandled rejections should crash the app.
		// Usually safer to just log them unless critical.
		// appError = event.reason instanceof Error ? event.reason : new Error(String(event.reason));
	}

	function resetError() {
		appError = null;
		window.location.reload();
	}

	onMount(() => {
		mounted = true;
		import('@lottiefiles/lottie-player');
		initTheme();
		validateEnv();

		window.addEventListener('error', handleGlobalError);
		window.addEventListener('unhandledrejection', handleUnhandledRejection);

		return () => {
			window.removeEventListener('error', handleGlobalError);
			window.removeEventListener('unhandledrejection', handleUnhandledRejection);
		};
	});

	// Reactively fetch initial data when user becomes authenticated
	// This handles the case when user logs in and layout is already mounted
	$: if (mounted && $isAuthenticated && !hasFetchedInitialData) {
		fetchInitialDataIfNeeded();
	}

	// Reset state when user logs out
	$: if (!$isAuthenticated) {
		hasFetchedInitialData = false;
		isInitialDataLoaded.set(false);
		userProfile.reset();
	}

	// Fetch profile when authenticated
	async function fetchInitialDataIfNeeded() {
		if (hasFetchedInitialData) return;

		hasFetchedInitialData = true;

		// Fetch profile if needed
		const currentProfile = get(userProfile).data;

		try {
			if (!currentProfile) {
				const fullResponse = await auth.getProfile();
				// Extract profile and add profile stats for profile page
				const profileWithStats = {
					...fullResponse.profile,
					oshi: fullResponse.oshi,
					profileRank: fullResponse.rank,
					profileStats: fullResponse.stats,
					profileOshiTwoShots: fullResponse.oshiTwoShots,
					profileRecentActivity: fullResponse.recentActivity
				};
				userProfile.set({ data: profileWithStats, error: null });
			}
		} catch (err) {
			logger.error('Failed to load initial data', err, { context: 'Layout' });
		} finally {
			isInitialDataLoaded.set(true);
		}
	}

	// Only check auth redirects after component is mounted (hydrated)
	// This prevents premature redirects during slow connections
	$: if (mounted && !$isAuthenticated && !isPublicPage) {
		goto('/login');
	}

	// Redirect logged-in users away from guest-only routes (login/register)
	// asking to view a public profile (/u/...) should NOT trigger this!
	$: if (mounted && $isAuthenticated && isGuestRoute) {
		goto('/');
	}

	// Redirect logged-in users away from public JKT48 routes to their theater counterparts
	$: if (
		mounted &&
		$isAuthenticated &&
		$page.url.pathname.startsWith('/jkt48/')
	) {
		let theaterPath = $page.url.pathname.replace('/jkt48/', '/theater/');
		// Special case for sub-routes that might have different structures
		if ($page.url.pathname === '/jkt48/event-history') {
			theaterPath = '/theater/events/history';
		} else if ($page.url.pathname === '/jkt48/calendar') {
			theaterPath = '/theater/events/calendar';
		}
		goto(theaterPath);
	}
</script>

{#if appError}
	<ErrorFallback error={appError} onRetry={resetError} />
{:else}
	<LoadingBar />
	{#if $isAuthenticated}
		<CommandPalette />
	{/if}
	<div
		class="min-h-screen flex flex-col relative overflow-x-hidden {$isAuthenticated ? 'selection:bg-red-500/20' : ''}"
	>
		{#if $isAuthenticated && !isFullScreenRoute}
			<AnimatedBackground hideDecorationsOnMobile={true} />
		{/if}
		{#if $toast}
			<div class="fixed top-4 left-0 right-0 z-[10000] flex justify-center pointer-events-none">
				<div
					class="bg-gray-900/90 backdrop-blur-md text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 font-medium text-sm border border-white/10 pointer-events-auto animate-[fadeInDown_0.3s_ease-out]"
				>
					<div
						class={$toast.type === 'error'
							? 'bg-red-500 rounded-full p-1'
							: 'bg-green-500 rounded-full p-1'}
					>
						{#if $toast.type === 'error'}
							<svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="3"
									d="M6 18L18 6M6 6l12 12"
								/>
							</svg>
						{:else}
							<Check class="w-3 h-3 text-white" />
						{/if}
					</div>
					{$toast.message}
				</div>
			</div>
		{/if}

		{#if isPublicPage && !isGuestRoute && !$isAuthenticated}
			<!-- Public non-auth pages (like /u/*): render immediately -->
			<slot />
		{:else if isGuestRoute}
			<!-- Guest routes (/login, /register, /auth/*): need auth check -->
			{#if !mounted}
				<SplashScreen />
			{:else if !$isAuthenticated}
				<!-- Not authenticated: show login/register page -->
				<slot />
			{/if}
			<!-- If mounted && $isAuthenticated && isGuestRoute: render nothing, redirect will happen -->
		{:else if !mounted}
			<SplashScreen />
		{:else if isPublicPage && !$isAuthenticated}
			<!-- Render public theater pages for unauthenticated users -->
			{#if $page.url.pathname === '/'}
				<slot />
			{:else}
				{#if !isFullScreenRoute}
					<LandingNavbar showLogin={false} />
				{/if}
				{@const isLivePublicDetailPage = $page.url.pathname.startsWith('/jkt48/live/') && $page.params.id}
				<div class={isFullScreenRoute ? 'w-full h-full' : isLivePublicDetailPage ? 'max-w-7xl mx-auto p-0 sm:p-2 sm:px-4 flex-1' : 'max-w-7xl mx-auto px-4 py-8 flex-1'}>
					<slot />
				</div>
				{#if !isFullScreenRoute}
					<Footer />
				{/if}
			{/if}
		{:else if $isAuthenticated}
			<!-- Protected pages: user authenticated, show full content -->
			{#if isPlaygroundRoute}
				<PlaygroundHeader />
			{:else if !isFullScreenRoute}
				<div class="hidden md:block">
					<Header />
				</div>
				<div class="block md:hidden">
					<MobileHeader />
				</div>
			{/if}
			<main class="flex-1 w-full relative">
				<slot />
			</main>
			{#if !isFullScreenRoute && !isPlaygroundRoute}
				<MobileNav />
			{/if}
		{:else}
			<!-- Fallback or Catch-all (should be handled by redirects above) -->
			<div class="hidden">Nothing to show</div>
		{/if}
		<!-- If mounted && !$isAuthenticated && !isPublicPage: render nothing, redirect will happen -->
		<ScrollToTop />
	</div>
{/if}
