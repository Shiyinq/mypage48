<script lang="ts">
	import '../app.css';
	import { isAuthenticated, toast, tickets, userProfile, isInitialDataLoaded } from '$lib/stores';
	import { locale, type Locale } from '$lib/i18n';
	import { initTheme } from '$lib/stores/theme';
	import { ticketsApi } from '$lib/apis/tickets';
	import { auth } from '$lib/apis/auth';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get } from 'svelte/store';
	import Header from '$lib/components/Header.svelte';
	import MobileNav from '$lib/components/MobileNav.svelte';
	import { Check } from 'lucide-svelte';

	export let data: { locale?: string };

	// Hydrate locale from server cookie if available (SSR)
	if (data?.locale) {
		locale.set(data.locale as Locale);
	}

	// Flag to prevent duplicate fetches
	let hasFetchedInitialData = false;

	// Determine if current page is public (accessible without login)
	$: isPublicPage =
		$page.url.pathname === '/login' ||
		$page.url.pathname === '/register' ||
		$page.url.pathname.startsWith('/auth/') ||
		$page.url.pathname.startsWith('/u/');

	// Determine if current page is strictly for guests (login/register pages)
	// Logged in users should be redirected AWAY from these pages
	$: isGuestRoute =
		$page.url.pathname === '/login' ||
		$page.url.pathname === '/register' ||
		$page.url.pathname.startsWith('/auth/');

	// Track if client has mounted - used to delay auth redirects
	let mounted = false;

	// Initialize theme and fetch initial data on mount
	onMount(() => {
		mounted = true;
		initTheme();
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
		tickets.set([]);
		userProfile.set(null);
	}

	// Fetch initial data only once if authenticated and data not in store
	async function fetchInitialDataIfNeeded() {
		if (hasFetchedInitialData) return;

		hasFetchedInitialData = true;

		// Only fetch if not already in store
		const currentTickets = get(tickets);
		const currentProfile = get(userProfile);

		try {
			// Fetch tickets and profile in parallel, but only if needed
			const promises = [];

			if (currentTickets.length === 0) {
				// Initialize with default first page
				promises.push(ticketsApi.getMyTickets().then((response) => tickets.set(response.data)));
			}

			if (!currentProfile) {
				promises.push(
					auth.getProfile().then((fullResponse) => {
						// Extract profile and add profile stats for profile page
						const profileWithStats = {
							...fullResponse.profile,
							oshi: fullResponse.oshi,
							profileRank: fullResponse.rank,
							profileStats: fullResponse.stats,
							profileOshiTwoShots: fullResponse.oshiTwoShots,
							profileRecentActivity: fullResponse.recentActivity
						};
						userProfile.set(profileWithStats);
					})
				);
			}

			await Promise.all(promises);
		} catch (err) {
			console.error('Failed to load initial data:', err);
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
</script>

<div class="min-h-screen flex flex-col relative">
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

	{#if !isPublicPage}
		<Header />
	{/if}

	<main class="flex-1 w-full relative">
		<slot />
	</main>

	{#if !isPublicPage}
		<MobileNav />
	{/if}
</div>
