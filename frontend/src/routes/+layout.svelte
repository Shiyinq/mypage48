<script lang="ts">
	import '../app.css';
	import {
		isAuthenticated,
		toast,
		userProfile,
		isInitialDataLoaded,
		isImmersive
	} from '$lib/stores';
	import { locale, type Locale } from '$lib/i18n';
	import { initTheme } from '$lib/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
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
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import ReloadPrompt from '$lib/components/ReloadPrompt.svelte';
	import OfflinePage from './offline/+page.svelte';
	import ErrorPage from './+error.svelte';

	interface Props {
		data: { locale?: string };
		children?: import('svelte').Snippet;
	}

	let { data, children }: Props = $props();

	// Hydrate locale from server cookie if available (SSR)
	$effect(() => {
		if (data?.locale) {
			locale.set(data.locale as Locale);
		}
	});

	// Flag to prevent duplicate fetches
	let hasFetchedInitialData = $state(false);

	// Track if client has mounted - used to delay auth redirects
	let mounted = $state(false);

	// Track offline status globally
	let isOffline = $state(false);

	// Track forced 404s for unauthorized routes
	let force404 = $state(false);

	// Global Error Handling
	let appError: Error | null = $state(null);

	function handleGlobalError(event: ErrorEvent) {
		// Don't catch 404s or other navigation errors which are handled by SvelteKit
		if (event.message?.includes('404') || event.message?.includes('Not Found')) return;

		appError = event.error;
		logger.error('Global unhandled error:', event.error, { context: 'Layout' });
	}

	function handleUnhandledRejection(event: PromiseRejectionEvent) {
		const reason = event.reason;
		const message =
			reason instanceof Error ? reason.message : typeof reason === 'string' ? reason : '';
		const stack = reason instanceof Error ? reason.stack || '' : '';
		const fullText = `${message} ${stack}`;

		// Ignore Service Worker registration errors (expected in crawlers like Googlebot)
		// Googlebot WRS throws Error("Rejected") with serviceWorker only in the stack trace
		if (
			fullText.includes('serviceWorker') ||
			fullText.includes('ServiceWorker') ||
			fullText.includes('SW registration')
		) {
			logger.warn('Ignored SW registration rejection (non-fatal):', message, {
				context: 'Layout'
			});
			return;
		}

		appError = reason;
		logger.error('Unhandled promise rejection:', reason, { context: 'Layout' });
	}

	function resetError() {
		appError = null;
		window.location.reload();
	}

	onMount(() => {
		mounted = true;
		validateEnv();
		initTheme();

		// Add global error listeners
		window.addEventListener('error', handleGlobalError);
		window.addEventListener('unhandledrejection', handleUnhandledRejection);
		window.addEventListener('online', () => (isOffline = false));
		window.addEventListener('offline', () => (isOffline = true));
		isOffline = !navigator.onLine;

		return () => {
			window.removeEventListener('error', handleGlobalError);
			window.removeEventListener('unhandledrejection', handleUnhandledRejection);
			window.removeEventListener('online', () => (isOffline = false));
			window.removeEventListener('offline', () => (isOffline = true));
		};
	});

	// Fetch profile when authenticated
	async function fetchInitialDataIfNeeded() {
		if (hasFetchedInitialData) return;
		hasFetchedInitialData = true;

		// Fetch profile if needed
		const currentProfile = userProfile.data;

		try {
			if (!currentProfile) {
				await userProfile.load();
			}
		} catch (err) {
			logger.error('Failed to load initial data', err, { context: 'Layout' });
		} finally {
			isInitialDataLoaded.value = true;
		}
	}

	// Determine if current page is public (accessible without login)
	let isPublicPage = $derived(
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
			].some((path) => $page.url.pathname.startsWith(path))
	);
	// Determine if current page is strictly for guests (login/register pages)
	// Logged in users should be redirected AWAY from these pages
	let isGuestRoute = $derived(
		$page.url.pathname === '/login' ||
			$page.url.pathname === '/register' ||
			$page.url.pathname.startsWith('/auth/')
	);
	let isFullScreenRoute = $derived($page.url.pathname.includes('/live/multiview'));
	let isLiveRoute = $derived($page.url.pathname.startsWith('/live'));
	let isPlaygroundRoute = $derived($page.url.pathname.startsWith('/playground'));
	// Reset state when user logs out
	$effect(() => {
		if (!isAuthenticated.value) {
			hasFetchedInitialData = false;
			isInitialDataLoaded.value = false;
			userProfile.reset();
		}
	});
	// Reactively fetch initial data when user becomes authenticated
	// This handles the case when user logs in and layout is already mounted
	$effect(() => {
		if (mounted && isAuthenticated.value && !hasFetchedInitialData) {
			fetchInitialDataIfNeeded();
		}
	});
	// Centralized Auth Redirect Logic
	$effect(() => {
		if (!mounted) return;

		force404 = false;

		if ($page.status === 404) return; // Prevent redirecting on typo/unmatched routes
		const path = $page.url.pathname;
		const isAuth = isAuthenticated.value;

		if (isAuth && isGuestRoute) {
			goto('/');
		} else if (isAuth && path.startsWith('/jkt48/')) {
			const map: Record<string, string> = {
				'/jkt48/event-history': '/theater/events/history',
				'/jkt48/calendar': '/theater/events/calendar'
			};
			if (map[path]) goto(map[path]);
			else if (/^\/jkt48\/(live|sorter)/.test(path)) goto(path.replace('/jkt48/', '/'));
			else goto(path.replace('/jkt48/', '/theater/'));
		} else if (!isAuth && !isPublicPage) {
			const map: Record<string, string> = {
				'/theater/events/history': '/jkt48/event-history',
				'/theater/events/calendar': '/jkt48/calendar'
			};
			if (map[path]) goto(map[path]);
			else if (/^\/theater\/(events|live|members|news|sorter)/.test(path))
				goto(path.replace('/theater/', '/jkt48/'));
			else if (/^\/(live|sorter)/.test(path)) goto(`/jkt48${path}`);
			else {
				force404 = true;
			}
		}
	});
</script>

{#if force404}
	<ErrorPage overrideStatus={404} overrideMessage="Not Found" />
{:else if appError}
	<ErrorFallback error={appError} onRetry={resetError} />
{:else}
	<LoadingBar />
	{#if isAuthenticated.value}
		<CommandPalette />
	{/if}
	<div
		class="min-h-screen flex flex-col relative overflow-x-hidden {isAuthenticated.value
			? 'selection:bg-red-500/20'
			: ''}"
	>
		{#if isAuthenticated.value && !isFullScreenRoute && !isImmersive.value}
			<AppBackground hideDecorationsOnMobile={true} />
		{/if}
		{#if toast.current}
			<div class="fixed top-4 left-0 right-0 z-[99999] flex justify-center pointer-events-none">
				<div
					class="bg-gray-900/90 backdrop-blur-md text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 font-medium text-sm border border-white/10 pointer-events-auto animate-[fadeInDown_0.3s_ease-out]"
				>
					<div
						class={toast.current.type === 'error'
							? 'bg-red-500 rounded-full p-1'
							: 'bg-green-500 rounded-full p-1'}
					>
						{#if toast.current.type === 'error'}
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
					{toast.current.message}
				</div>
			</div>
		{/if}

		{#if isPublicPage && !isGuestRoute && !isAuthenticated.value}
			<!-- Public non-auth pages (like /u/*): render immediately -->
			{#if isOffline}
				<OfflinePage />
			{:else}
				{@render children?.()}
			{/if}
		{:else if isGuestRoute}
			<!-- Guest routes (/login, /register, /auth/*): need auth check -->
			{#if !mounted}
				<SplashScreen />
			{:else if !isAuthenticated.value}
				<!-- Not authenticated: show login/register page -->
				<main class="flex-1 w-full relative flex flex-col">
					{#if isOffline}
						<OfflinePage />
					{:else}
						{@render children?.()}
					{/if}
				</main>
			{/if}
			<!-- If mounted && $isAuthenticated && isGuestRoute: render nothing, redirect will happen -->
		{:else if !mounted}
			<SplashScreen />
		{:else if isPublicPage && !isAuthenticated.value}
			<!-- Render public theater pages for unauthenticated users -->
			{#if $page.url.pathname === '/'}
				<main class="flex-1 w-full relative flex flex-col">
					{#if isOffline}
						<OfflinePage />
					{:else}
						{@render children?.()}
					{/if}
				</main>
			{:else}
				{#if !isFullScreenRoute && !isImmersive.value && !isLiveRoute}
					<LandingNavbar showLogin={false} />
				{/if}
				{@const isLivePublicDetailPage =
					$page.url.pathname.startsWith('/jkt48/live/') && $page.params.id}
				<div
					class="relative {isFullScreenRoute || isImmersive.value
						? 'w-full h-full'
						: isLivePublicDetailPage
							? 'max-w-7xl mx-auto p-0 sm:p-2 sm:px-4 flex-1'
							: 'max-w-7xl mx-auto px-4 py-8 flex-1'}"
				>
					{#if isOffline}
						<OfflinePage />
					{:else}
						{@render children?.()}
					{/if}
				</div>
				{#if !isFullScreenRoute && !isImmersive.value && !isLiveRoute}
					<Footer />
				{/if}
			{/if}
		{:else if isAuthenticated.value}
			<!-- Protected pages: user authenticated, show full content -->
			{#if isPlaygroundRoute}
				<PlaygroundHeader />
			{:else if !isFullScreenRoute && !isImmersive.value && !isLiveRoute}
				<div class="hidden md:block">
					<Header />
				</div>
				<div class="block md:hidden">
					<MobileHeader />
				</div>
			{/if}
			<main class="flex-1 w-full relative">
				{#if isOffline}
					<OfflinePage />
				{:else}
					{@render children?.()}
				{/if}
			</main>
			{#if !isLiveRoute && !isFullScreenRoute && !isPlaygroundRoute && !isImmersive.value}
				<MobileNav />
			{/if}
		{:else if $page.status === 404}
			<main class="flex-1 w-full relative flex flex-col h-full">
				{#if isOffline}
					<OfflinePage />
				{:else}
					{@render children?.()}
				{/if}
			</main>
		{:else}
			<!-- Fallback or Catch-all (should be handled by redirects above) -->
			<div class="hidden">Nothing to show</div>
		{/if}
		<!-- If mounted && !$isAuthenticated && !isPublicPage: render nothing, redirect will happen -->
		<ScrollToTop />
		<ReloadPrompt />
	</div>
{/if}
