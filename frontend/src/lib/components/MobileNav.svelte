<script lang="ts">
	import { page } from '$app/stores';
	import {
		LayoutDashboard,
		AudioLines,
		Plus,
		Image as ImageIcon,
		History,
		Menu,
		BookOpen,
		Trophy,
		Settings,
		ChevronRight,
		X
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { fade, slide, fly } from 'svelte/transition';

	const { t } = useTranslation();
	let isMenuOpen = false;

	let lastScrollY = 0;
	let isHidden = false;
	const threshold = 10;

	function handleScroll() {
		// Only hide on mobile devices (consistent with md:hidden)
		if (window.innerWidth >= 768) return;
		
		const currentScrollY = window.scrollY;
		const delta = Math.abs(currentScrollY - lastScrollY);

		if (delta < threshold) return;

		// If user scrolls down, hide. If user scrolls up, show.
		if (currentScrollY > lastScrollY && currentScrollY > 80) {
			isHidden = true;
		} else {
			isHidden = false;
		}
		lastScrollY = currentScrollY;
	}

	const secondaryLinks = [
		{ href: '/memories', icon: ImageIcon, label: 'nav.memories', color: 'text-pink-500' },
		{ href: '/journal', icon: BookOpen, label: 'nav.journal', color: 'text-green-500' },
		{ href: '/achievements', icon: Trophy, label: 'nav.achievements', color: 'text-amber-500' }
	];

	function toggleMenu() {
		isMenuOpen = !isMenuOpen;
	}

	function closeMenu() {
		isMenuOpen = false;
	}
</script>

<!-- Menu Drawer Overlay -->
{#if isMenuOpen}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div
		class="md:hidden fixed inset-0 bg-black/40 backdrop-blur-sm z-[60]"
		on:click={closeMenu}
		transition:fade={{ duration: 200 }}
	></div>

	<div
		class="md:hidden fixed bottom-16 left-0 right-0 bg-white dark:bg-zinc-900 rounded-t-3xl z-[70] shadow-2xl border-t border-gray-100 dark:border-white/5 pb-8 overflow-hidden"
		transition:fly={{ y: 300, duration: 300 }}
	>
		<div class="px-6 py-5 flex items-center justify-between border-b border-gray-50 dark:border-white/5">
			<h3 class="text-lg font-bold text-gray-900 dark:text-white">{$t('nav.more') || 'Lainnya'}</h3>
			<button class="p-2 text-gray-400 hover:text-gray-600" on:click={closeMenu}>
				<X class="w-6 h-6" />
			</button>
		</div>
		<div class="p-4 grid grid-cols-1 gap-2">
			{#each secondaryLinks as link}
				<a
					href={link.href}
					class="flex items-center justify-between p-4 rounded-2xl hover:bg-gray-50 dark:hover:bg-white/5 transition-colors group"
					on:click={closeMenu}
				>
					<div class="flex items-center gap-4">
						<div class={`p-3 rounded-xl bg-gray-50 dark:bg-white/5 ${link.color} group-hover:scale-110 transition-transform`}>
							<svelte:component this={link.icon} class="w-6 h-6" />
						</div>
						<span class="font-bold text-gray-700 dark:text-gray-200">{$t(link.label)}</span>
					</div>
					<ChevronRight class="w-5 h-5 text-gray-300" />
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
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 group min-w-[64px]"
		>
			<LayoutDashboard
				class={`w-6 h-6 transition-all ${$page.url.pathname === '/' ? 'text-red-600 dark:text-red-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all truncate w-full text-center ${$page.url.pathname === '/' ? 'text-red-600 dark:text-red-400' : ''}`}
				>{$t('nav.home')}</span
			>
		</a>

		<a
			href="/theater/events"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 group min-w-[64px]"
		>
			<AudioLines
				class={`w-6 h-6 transition-all ${$page.url.pathname.startsWith('/theater') ? 'text-purple-600 dark:text-purple-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all truncate w-full text-center ${$page.url.pathname.startsWith('/theater') ? 'text-purple-600 dark:text-purple-400' : ''}`}
				>{$t('nav.theater')}</span
			>
		</a>

		<!-- Floating Action Button (FAB) -->
		<div class="relative -top-5 flex justify-center px-1">
			<a
				href="/upload"
				class="flex justify-center w-12 h-12 rounded-full idol-gradient text-white shadow-lg shadow-red-300 dark:shadow-red-900/50 border-4 border-gray-50 dark:border-zinc-950 items-center transform transition-transform active:scale-90 hover:scale-105"
			>
				<Plus class="w-7 h-7" />
			</a>
		</div>

		<a
			href="/history"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 group min-w-[64px]"
		>
			<History
				class={`w-6 h-6 transition-all ${$page.url.pathname === '/history' ? 'text-blue-600 dark:text-blue-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all truncate w-full text-center ${$page.url.pathname === '/history' ? 'text-blue-600 dark:text-blue-400' : ''}`}
				>{$t('nav.history')}</span
			>
		</a>

		<button
			on:click={toggleMenu}
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 group min-w-[64px]"
		>
			<Menu
				class={`w-6 h-6 transition-all ${isMenuOpen ? 'text-indigo-600 dark:text-indigo-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all truncate w-full text-center ${isMenuOpen ? 'text-indigo-600 dark:text-indigo-400' : ''}`}
				>{$t('nav.more') || 'Menu'}</span
			>
		</button>
	</div>
</nav>
