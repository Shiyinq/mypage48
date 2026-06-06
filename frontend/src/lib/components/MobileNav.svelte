<script lang="ts">
	import { page } from '$app/stores';
	import { afterNavigate } from '$app/navigation';
	import {
		LayoutDashboard,
		AudioLines,
		Plus,
		Image as ImageIcon,
		History,
		Menu,
		BookOpen,
		Trophy,
		ChevronRight,
		X,
		User,
		Crown
	} from 'lucide-svelte';
	import { theaterNavItems } from '$lib/constants/theaterNav';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { fade, fly } from 'svelte/transition';

	const { t } = useTranslation();
	let isMenuOpen = $state(false);
	let isTheaterMenuOpen = $state(false);

	const secondaryLinks = [
		{ href: '/memories', icon: ImageIcon, label: 'nav.memories', color: 'text-pink-500' },
		{ href: '/top-2shot', icon: Crown, label: 'nav.top2shot', color: 'text-indigo-500' },
		{ href: '/journal', icon: BookOpen, label: 'nav.journal', color: 'text-green-500' },
		{ href: '/achievements', icon: Trophy, label: 'nav.achievements', color: 'text-amber-500' },
		{ href: '/history', icon: History, label: 'nav.history', color: 'text-blue-500' }
	];

	function toggleMenu() {
		isMenuOpen = !isMenuOpen;
		if (isMenuOpen) isTheaterMenuOpen = false;
	}

	function toggleTheaterMenu() {
		isTheaterMenuOpen = !isTheaterMenuOpen;
		if (isTheaterMenuOpen) isMenuOpen = false;
	}

	function closeAllMenus() {
		isMenuOpen = false;
		isTheaterMenuOpen = false;
	}

	afterNavigate(() => {
		closeAllMenus();
	});

	let isRouteMore = $derived(
		secondaryLinks.some((link) => $page.url.pathname.startsWith(link.href))
	);
	let isRouteTheater = $derived($page.url.pathname.startsWith('/theater'));
</script>

<!-- Menu Drawer Overlay -->
{#if isMenuOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="md:hidden fixed inset-0 bg-black/40 backdrop-blur-sm z-[60]"
		onclick={closeAllMenus}
		transition:fade={{ duration: 200 }}
	></div>

	<div
		class="md:hidden fixed bottom-16 left-0 right-0 bg-white dark:bg-zinc-900 rounded-t-3xl z-[70] shadow-2xl border-t border-gray-100 dark:border-white/5 pb-8 overflow-hidden"
		transition:fly={{ y: 300, duration: 300 }}
	>
		<div
			class="px-6 py-5 flex items-center justify-between border-b border-gray-50 dark:border-white/5"
		>
			<h3 class="text-lg font-bold text-gray-900 dark:text-white">
				{t('nav.journey') || 'Journey'}
			</h3>
			<button class="p-2 text-gray-400 hover:text-gray-600" onclick={closeAllMenus}>
				<X class="w-6 h-6" />
			</button>
		</div>
		<div class="p-3 grid grid-cols-1 gap-1.5 max-h-[75vh] overflow-y-auto">
			{#each secondaryLinks as link}
				{@const isActive = $page.url.pathname.startsWith(link.href)}
				<a
					href={link.href}
					class={`flex items-center justify-between p-3 rounded-2xl transition-all group ${isActive ? 'bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-100 dark:border-indigo-500/20 shadow-sm' : 'hover:bg-gray-50 dark:hover:bg-white/5'}`}
					onclick={closeAllMenus}
				>
					<div class="flex items-center gap-3">
						<div
							class={`p-2.5 rounded-xl transition-transform ${isActive ? 'bg-white dark:bg-zinc-800 shadow-sm scale-110 ' + link.color : 'bg-gray-50 dark:bg-white/5 ' + link.color} group-hover:scale-110`}
						>
							<link.icon class="w-5 h-5" />
						</div>
						<span
							class={`font-bold transition-colors ${isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-700 dark:text-gray-200'}`}
							>{t(link.label)}</span
						>
					</div>
					<ChevronRight
						class={`w-4 h-4 transition-all ${isActive ? 'text-indigo-500 transform translate-x-1' : 'text-gray-300'}`}
					/>
				</a>
			{/each}
		</div>
	</div>
{/if}

<!-- Theater Menu Drawer -->
{#if isTheaterMenuOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="md:hidden fixed inset-0 bg-black/40 backdrop-blur-sm z-[60]"
		onclick={closeAllMenus}
		transition:fade={{ duration: 200 }}
	></div>

	<div
		class="md:hidden fixed bottom-16 left-0 right-0 bg-white dark:bg-zinc-900 rounded-t-3xl z-[70] shadow-2xl border-t border-gray-100 dark:border-white/5 pb-8 overflow-hidden"
		transition:fly={{ y: 300, duration: 300 }}
	>
		<div
			class="px-6 py-5 flex items-center justify-between border-b border-gray-50 dark:border-white/5"
		>
			<h3 class="text-lg font-bold text-gray-900 dark:text-white">
				{t('nav.theater') || 'Theater'}
			</h3>
			<button class="p-2 text-gray-400 hover:text-gray-600" onclick={closeAllMenus}>
				<X class="w-6 h-6" />
			</button>
		</div>
		<div class="p-3 grid grid-cols-1 gap-1.5 max-h-[75vh] overflow-y-auto pb-4 relative">
			{#each theaterNavItems as link}
				{@const isActive = link.exact
					? $page.url.pathname === link.href
					: $page.url.pathname.startsWith(link.href)}
				<a
					href={link.href}
					class={`flex items-center justify-between p-3 rounded-2xl transition-all group ${isActive ? 'bg-purple-50 dark:bg-purple-500/10 border border-purple-100 dark:border-purple-500/20 shadow-sm' : 'hover:bg-gray-50 dark:hover:bg-white/5'}`}
					onclick={closeAllMenus}
				>
					<div class="flex items-center gap-3">
						<div
							class={`p-2.5 rounded-xl transition-transform ${isActive ? 'bg-white dark:bg-zinc-800 shadow-sm scale-110 ' + link.color : 'bg-gray-50 dark:bg-white/5 ' + link.color} group-hover:scale-110`}
						>
							<link.icon class="w-5 h-5" />
						</div>
						<span
							class={`font-bold transition-colors ${isActive ? 'text-purple-600 dark:text-purple-400' : 'text-gray-700 dark:text-gray-200'}`}
							>{t(link.labelKey) || link.labelDefault}</span
						>
					</div>
					<ChevronRight
						class={`w-4 h-4 transition-all ${isActive ? 'text-purple-500 transform translate-x-1' : 'text-gray-300'}`}
					/>
				</a>
			{/each}
		</div>
	</div>
{/if}

<nav
	class="md:hidden fixed bottom-0 left-0 right-0 bg-white/95 dark:bg-zinc-950/95 backdrop-blur-xl border-t border-gray-200 dark:border-zinc-800 z-[80] pb-safe shadow-[0_-4px_20px_rgba(0,0,0,0.05)] dark:shadow-none transition-transform duration-300 ease-in-out"
>
	<div class="flex h-16 items-center justify-around max-w-[420px] mx-auto px-4">
		<a
			href="/"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 group min-w-[56px]"
		>
			<LayoutDashboard
				class={`w-6 h-6 transition-all ${$page.url.pathname === '/' ? 'text-red-600 dark:text-red-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all truncate w-full text-center ${$page.url.pathname === '/' ? 'text-red-600 dark:text-red-400' : ''}`}
				>{t('nav.home')}</span
			>
		</a>

		<button
			onclick={toggleTheaterMenu}
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 group min-w-[56px]"
		>
			<AudioLines
				class={`w-6 h-6 transition-all ${isTheaterMenuOpen || isRouteTheater ? 'text-purple-600 dark:text-purple-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all truncate w-full text-center ${isTheaterMenuOpen || isRouteTheater ? 'text-purple-600 dark:text-purple-400' : ''}`}
				>{t('nav.theater')}</span
			>
		</button>

		<!-- Floating Action Button (FAB) -->
		<div class="relative -top-5 flex justify-center px-1">
			<a
				href="/upload"
				class="flex justify-center w-12 h-12 rounded-full idol-gradient text-white shadow-lg shadow-red-300 dark:shadow-red-900/50 border-4 border-gray-50 dark:border-zinc-950 items-center transform transition-transform active:scale-90 hover:scale-105"
			>
				<Plus class="w-7 h-7" />
			</a>
		</div>

		<button
			onclick={toggleMenu}
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 group min-w-[56px]"
		>
			<Menu
				class={`w-6 h-6 transition-all ${isMenuOpen || isRouteMore ? 'text-indigo-600 dark:text-indigo-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all truncate w-full text-center ${isMenuOpen || isRouteMore ? 'text-indigo-600 dark:text-indigo-400' : ''}`}
				>{t('nav.journey') || 'Journey'}</span
			>
		</button>

		<a
			href="/profile"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-zinc-600 dark:hover:text-zinc-300 group min-w-[56px]"
		>
			<User
				class={`w-6 h-6 transition-all ${$page.url.pathname === '/profile' ? 'text-zinc-700 dark:text-white scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all truncate w-full text-center ${$page.url.pathname === '/profile' ? 'text-zinc-700 dark:text-white' : ''}`}
				>{t('nav.profile') || 'Profile'}</span
			>
		</a>
	</div>
</nav>
