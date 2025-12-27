<script lang="ts">
	import { page } from '$app/stores';
	import { Ticket, Plus, User } from 'lucide-svelte';
	import { onMount } from 'svelte';
	import { isAuthenticated, userProfile } from '$lib/stores';
	import { auth } from '$lib/apis/auth';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	// Navigation items with translation keys
	$: navItems = [
		{ labelKey: 'nav.dashboard', href: '/' },
		{ labelKey: 'nav.setlists', href: '/shows' },
		{ labelKey: 'nav.achievements', href: '/achievements' },
		{ labelKey: 'nav.memories', href: '/memories' },
		{ labelKey: 'nav.history', href: '/history' }
	];

	onMount(async () => {
		if ($isAuthenticated && !$userProfile) {
			try {
				const profile = await auth.getProfile();
				userProfile.set(profile);
			} catch (error) {
				console.error('Failed to fetch user profile:', error);
			}
		}
	});
</script>

<header class="bg-white/90 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
	<div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
		<!-- Left: Logo -->
		<a href="/" class="flex items-center gap-3 cursor-pointer">
			<div
				class="w-9 h-9 rounded-full idol-gradient flex items-center justify-center text-white shadow-red-200 shadow-lg ring-2 ring-white"
			>
				<Ticket class="w-5 h-5" />
			</div>
			<div class="flex flex-col">
				<h1 class="text-xl font-black tracking-tight text-gray-900 leading-none">
					MyPage<span class="text-red-600">48</span>
				</h1>
				<span class="text-[10px] font-semibold text-gray-400 tracking-wide hidden sm:block"
					>{$t('header.tagline')}</span
				>
			</div>
		</a>

		<!-- Center: Desktop Navigation -->
		<div
			class="hidden md:flex items-center gap-1 bg-white border border-gray-100 p-1.5 rounded-full shadow-sm overflow-x-auto max-w-xl"
		>
			{#each navItems as item}
				<a
					href={item.href}
					class={`px-4 py-2 rounded-full text-sm font-bold transition-all duration-200 ${
						$page.url.pathname === item.href ||
						($page.url.pathname === '/' && item.href === '/' && $page.url.pathname === item.href) // Simple matching
							? 'bg-red-50 text-red-600 shadow-sm ring-1 ring-red-100'
							: 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
					}`}
					class:bg-red-50={$page.url.pathname === item.href}
				>
					{$t(item.labelKey)}
				</a>
			{/each}
		</div>

		<!-- Right: Actions & Profile -->
		<div class="flex items-center gap-3">
			<!-- Desktop New Ticket Button -->
			<div class="hidden md:block">
				<a
					href="/upload"
					class="idol-gradient text-white px-5 py-2.5 rounded-full font-bold text-sm shadow-lg shadow-red-200 hover:shadow-red-300 hover:scale-105 transition-all flex items-center gap-2"
				>
					<Plus class="w-4 h-4" />
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
								: 'ring-1 ring-gray-200 hover:ring-red-400'
						}`}
			>
				<img
					src={$userProfile?.oshi?.profilePicture ||
						$userProfile?.profilePicture ||
						'https://jkt48.com/profile/oline_manuel.jpg'}
					alt="Profile"
					class="w-full h-full object-cover"
				/>
				<div
					class={`absolute inset-0 bg-red-500/20 transition-opacity ${$page.url.pathname === '/profile' ? 'opacity-0' : 'opacity-0 group-hover:opacity-100'}`}
				></div>
			</a>
		</div>
	</div>
</header>
