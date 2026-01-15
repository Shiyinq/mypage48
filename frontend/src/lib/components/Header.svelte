<script lang="ts">
	import { page } from '$app/stores';
	import { Ticket, Plus, User } from 'lucide-svelte';
	import { userProfile, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';

	const { t } = useTranslation();

	/* Loading State */
	let mounted = false;

	onMount(() => {
		mounted = true;
	});

	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded);

	// Navigation items with translation keys
	$: navItems = [
		{ labelKey: 'nav.dashboard', href: '/' },
		{ labelKey: 'nav.theater', href: '/theater' },
		{ labelKey: 'nav.achievements', href: '/achievements' },
		{ labelKey: 'nav.memories', href: '/memories' },
		{ labelKey: 'nav.history', href: '/history' }
	];
</script>

<header
	class="bg-white/95 dark:bg-zinc-950/95 backdrop-blur-xl border-b border-gray-200 dark:border-zinc-800 sticky top-0 z-50"
>
	<div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
		<!-- Left: Logo -->
		<a href="/" class="flex items-center gap-3 cursor-pointer">
			<div
				class="w-9 h-9 rounded-full idol-gradient flex items-center justify-center text-white shadow-red-200 dark:shadow-red-900/50 shadow-lg ring-2 ring-white dark:ring-gray-800"
			>
				<Ticket class="w-5 h-5" />
			</div>
			<div class="flex flex-col">
				<h1 class="text-xl font-black tracking-tight text-gray-900 dark:text-gray-100 leading-none">
					MyPage<span class="text-red-600 dark:text-red-500">48</span>
				</h1>
				<span class="text-[10px] font-semibold text-gray-400 tracking-wide hidden sm:block"
					>{$t('header.tagline')}</span
				>
			</div>
		</a>

		<!-- Center: Desktop Navigation -->
		<div
			class="hidden md:flex items-center gap-1 bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-700 p-1.5 rounded-full shadow-sm overflow-x-auto max-w-xl"
		>
			{#each navItems as item}
				{@const isActive =
					item.href === '/' ? $page.url.pathname === '/' : $page.url.pathname.startsWith(item.href)}
				<a
					href={item.href}
					class={`px-4 py-2 rounded-full text-sm font-bold transition-all duration-200 ${
						isActive
							? 'bg-red-50 dark:bg-red-500/20 text-red-600 dark:text-red-400 shadow-sm ring-1 ring-red-100 dark:ring-red-500/30'
							: 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700'
					}`}
					class:bg-red-50={isActive}
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
					class="idol-gradient text-white px-5 py-2.5 rounded-full font-bold text-sm shadow-lg shadow-red-200 dark:shadow-red-900/50 hover:shadow-red-300 dark:hover:shadow-red-800/50 hover:scale-105 transition-all flex items-center gap-2"
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
								: 'ring-1 ring-gray-200 dark:ring-gray-700 hover:ring-red-400'
						}`}
			>
				{#if isLoading}
					<div class="w-full h-full bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
				{:else if $userProfile?.data?.oshi?.profilePicture || $userProfile?.data?.profilePicture}
					<img
						src={$userProfile?.data?.oshi?.profilePicture || $userProfile?.data?.profilePicture}
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
