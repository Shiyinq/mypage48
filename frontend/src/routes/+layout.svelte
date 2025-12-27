<script>
	import '../app.css';
	import { isAuthenticated, toast, tickets } from '$lib/stores';
	import { theater } from '$lib/apis/theater';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import Header from '$lib/components/Header.svelte';
	import MobileNav from '$lib/components/MobileNav.svelte';
	import { Check } from 'lucide-svelte';

	$: isPublicPage =
		$page.url.pathname === '/login' ||
		$page.url.pathname === '/register' ||
		$page.url.pathname.startsWith('/auth/');

	$: if (typeof window !== 'undefined' && !$isAuthenticated && !isPublicPage) {
		goto('/login');
	}

	$: if (typeof window !== 'undefined' && $isAuthenticated && isPublicPage) {
		goto('/');
	}

	// Fetch tickets whenever authentication status changes to true
	$: if (typeof window !== 'undefined' && $isAuthenticated) {
		theater
			.getMyTickets()
			.then((data) => tickets.set(data))
			.catch((err) => console.error('Failed to load tickets:', err));
	}
</script>

<div class="min-h-screen bg-gray-50 flex flex-col relative">
	{#if $toast}
		<div class="fixed top-4 left-0 right-0 z-[10000] flex justify-center pointer-events-none">
			<div
				class="bg-gray-900/90 backdrop-blur-md text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 font-medium text-sm border border-white/10 pointer-events-auto animate-[fadeInDown_0.3s_ease-out]"
			>
				<div class="bg-green-500 rounded-full p-1">
					<Check class="w-3 h-3 text-white" />
				</div>
				{$toast.message}
			</div>
		</div>
	{/if}

	{#if $isAuthenticated && !isPublicPage}
		<Header />
	{/if}

	<main class="flex-1 w-full relative">
		<slot />
	</main>

	{#if $isAuthenticated && !isPublicPage}
		<MobileNav />
	{/if}
</div>
