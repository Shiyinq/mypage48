<script lang="ts">
	import { isImmersive } from '$lib/stores';
	import {
		X,
		Tv,
		LayoutGrid,
		Globe,
		History,
		Image as ImageIcon,
		RotateCcw,
		ChevronRight
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { page } from '$app/stores';
	import { afterNavigate } from '$app/navigation';
	import NavPills from '$lib/components/navigation/NavPills.svelte';
	import { liveNavbarStore } from '$lib/stores/liveNavbar.svelte';
	import { fade, fly } from 'svelte/transition';
	import type { Snippet } from 'svelte';

	const { t } = useTranslation();

	interface Props {
		children: Snippet;
		basePath: string;
		backPath: string;
	}

	let { children, basePath, backPath }: Props = $props();

	const isLiveRoom = $derived(
		!!($page.params.platform && $page.params.id) ||
			($page.url.pathname.includes('/replay/') && $page.params.id)
	);

	const navItems = $derived([
		{
			label: t('nav.live'),
			mobileLabel: t('nav.live'),
			href: basePath,
			exact: true,
			icon: Tv
		},
		{
			label: t('nav.switchMultiview') || 'Multi-View',
			mobileLabel: t('nav.multiview') || 'Multi',
			href: `${basePath}/multiview`,
			exact: true,
			icon: LayoutGrid
		},
		{
			label: t('replay.nav') || 'Replay',
			mobileLabel: t('replay.nav') || 'Replay',
			href: `${basePath}/replay`,
			match: (path: string) => path.startsWith(`${basePath}/replay`),
			icon: RotateCcw
		},
		{
			label: t('nav.liveHistory') || 'Riwayat Live',
			mobileLabel: t('nav.history') || 'History',
			href: `${basePath}/history`,
			match: (path: string) =>
				path === `${basePath}/history` || path.startsWith(`${basePath}/history/members`),
			icon: Globe
		},
		{
			label: t('nav.watchHistory') || 'Riwayat Menonton',
			mobileLabel: t('nav.watched') || 'Watched',
			href: `${basePath}/history/watched`,
			match: (path: string) => path.startsWith(`${basePath}/history/watched`),
			icon: History
		},
		{
			label: t('nav.pcLive') || 'PC Live',
			mobileLabel: t('nav.pcLive') || 'PC Live',
			href: `${basePath}/pc`,
			activeHref: `${basePath}/pc`,
			exact: false,
			icon: ImageIcon
		}
	]);

	let isHistoryDrawerOpen = $state(false);

	const historyDrawerLinks = $derived([
		{
			label: t('nav.liveHistory') || 'Riwayat Live',
			href: `${basePath}/history`,
			match: (path: string) =>
				path === `${basePath}/history` || path.startsWith(`${basePath}/history/members`),
			icon: Globe
		},
		{
			label: t('nav.watchHistory') || 'Riwayat Menonton',
			href: `${basePath}/history/watched`,
			match: (path: string) => path.startsWith(`${basePath}/history/watched`),
			icon: History
		}
	]);

	type MobileNavItem =
		| { isDrawer: true; icon: typeof Globe; mobileLabel: string }
		| {
				isDrawer?: false;
				label: string;
				mobileLabel: string;
				href: string;
				exact?: boolean;
				match?: (path: string) => boolean;
				activeHref?: string;
				icon: typeof Globe;
		  };

	const mobileNavItems = $derived<MobileNavItem[]>([
		{
			label: t('nav.live'),
			mobileLabel: t('nav.live'),
			href: basePath,
			exact: true,
			icon: Tv
		},
		{
			label: t('nav.switchMultiview') || 'Multi-View',
			mobileLabel: t('nav.multiview') || 'Multi',
			href: `${basePath}/multiview`,
			exact: true,
			icon: LayoutGrid
		},
		{
			label: t('replay.nav') || 'Replay',
			mobileLabel: t('replay.nav') || 'Replay',
			href: `${basePath}/replay`,
			match: (path: string) => path.startsWith(`${basePath}/replay`),
			icon: RotateCcw
		},
		{ isDrawer: true, icon: Globe, mobileLabel: t('nav.history') || 'History' },
		{
			label: t('nav.pcLive') || 'PC Live',
			mobileLabel: t('nav.pcLive') || 'PC Live',
			href: `${basePath}/pc`,
			activeHref: `${basePath}/pc`,
			exact: false,
			icon: ImageIcon
		}
	]);

	function closeHistoryDrawer() {
		isHistoryDrawerOpen = false;
	}

	function toggleHistoryDrawer() {
		isHistoryDrawerOpen = !isHistoryDrawerOpen;
	}

	afterNavigate(() => {
		closeHistoryDrawer();
	});

	$effect(() => {
		isImmersive.set(true);
		document.body.style.overflow = 'hidden';
		return () => {
			isImmersive.set(false);
			document.body.style.overflow = '';
		};
	});
</script>

<div class="flex flex-col h-screen w-full relative overflow-hidden bg-slate-50 dark:bg-zinc-950">
	{#if !isLiveRoom}
		<!-- Main Live Navbar -->
		<div
			class="fixed top-0 left-0 right-0 w-full z-[10000] border-b border-black/5 dark:border-white/5 bg-white/85 dark:bg-zinc-950/60 backdrop-blur-xl transition-all duration-300 ease-in-out"
		>
			<div
				class="max-w-7xl mx-auto w-full h-16 flex items-center justify-between px-4 sm:px-6 lg:px-8"
			>
				<div class="flex-1 min-w-0">
					<a
						href={backPath}
						class="flex items-center gap-2 sm:gap-3 text-slate-900 dark:text-white hover:text-red-600 transition-colors cursor-pointer inline-flex group"
					>
						<div
							class="w-8 h-8 flex items-center justify-center rounded-full bg-white dark:bg-zinc-800 shadow-sm border border-gray-200 dark:border-zinc-700 group-hover:border-red-200 dark:group-hover:border-red-900 group-hover:shadow-md transition-all"
						>
							<X
								size={16}
								class="shrink-0 text-slate-500 dark:text-slate-400 group-hover:text-red-600 dark:group-hover:text-red-500"
							/>
						</div>
						<span class="font-extrabold tracking-tight text-lg whitespace-nowrap"
							>JKT48 <span class="text-red-600 italic">LIVE</span></span
						>
					</a>
				</div>

				<div class="hidden md:flex items-center justify-center">
					<NavPills
						items={navItems}
						currentPath={$page.url.pathname}
						className="bg-gray-100/50 dark:bg-zinc-900/50 border-gray-200 dark:border-zinc-800 shadow-sm shrink-0"
					>
						{#snippet item({ item, isActive })}
							{#if item.label === 'LIVE'}
								<span
									class="font-extrabold tracking-tight whitespace-nowrap normal-case text-[11px]"
									>{item.label}</span
								>
							{:else}
								<span>{item.label}</span>
							{/if}
							{#if item.showBadge}
								<span
									class="px-1.5 py-0.5 rounded-full {isActive
										? 'bg-white/20 text-white'
										: 'bg-slate-200 text-slate-600 dark:bg-zinc-700 dark:text-zinc-300'} font-black text-[9px]"
									>{item.badgeValue}</span
								>
							{/if}
						{/snippet}
					</NavPills>
				</div>

				<!-- Right: Page Specific Actions -->
				<div class="flex-1 flex justify-end items-center">
					{#if liveNavbarStore.rightSnippet}
						{@render liveNavbarStore.rightSnippet()}
					{/if}
				</div>
			</div>
		</div>
	{/if}

	<!-- Content Area -->
	<div class="flex-1 relative overflow-hidden pt-12 sm:pt-16">
		{@render children()}
	</div>

	<!-- Mobile Specific Live Navbar (Bottom) -->
	{#if !isLiveRoom}
		<nav
			class="md:hidden fixed bottom-0 left-0 right-0 z-[10002] pb-safe shadow-[0_-4px_20px_rgba(0,0,0,0.03)] dark:shadow-none transition-all duration-300 ease-in-out {isHistoryDrawerOpen
				? 'bg-white dark:bg-zinc-950 border-t border-black/5 dark:border-white/5'
				: 'bg-white/85 dark:bg-zinc-950/60 backdrop-blur-xl border-t border-black/5 dark:border-white/5'}"
		>
			<div
				class="flex h-16 items-center justify-around w-full overflow-x-auto no-scrollbar px-2 max-w-[420px] mx-auto"
			>
				{#each mobileNavItems as item}
					{#if item.isDrawer}
						<button
							onclick={toggleHistoryDrawer}
							class="flex flex-col items-center justify-center gap-0.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 active:scale-90 active:opacity-70 transition-all duration-200 group min-w-[60px] shrink-0"
						>
							<Globe
								class="w-5 h-5 sm:w-6 sm:h-6 transition-all {isHistoryDrawerOpen
									? 'text-red-600 dark:text-red-400 scale-110'
									: ''}"
							/>
							<span
								class="text-[10px] sm:text-[11px] transition-all truncate w-full text-center font-medium {isHistoryDrawerOpen
									? 'text-red-600 dark:text-red-400 font-bold'
									: ''}"
							>
								{item.mobileLabel}
							</span>
						</button>
					{:else}
						{@const isActive = item.match
							? item.match($page.url.pathname)
							: item.exact
								? $page.url.pathname === (item.activeHref || item.href)
								: (item.activeHref || item.href) === '/'
									? $page.url.pathname === '/'
									: $page.url.pathname.startsWith(item.activeHref || item.href)}
						<a
							href={item.href}
							class="flex flex-col items-center justify-center gap-0.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 active:scale-90 active:opacity-70 transition-all duration-200 group min-w-[60px] shrink-0"
						>
							<item.icon
								class={`w-5 h-5 sm:w-6 sm:h-6 transition-all ${isActive ? 'text-red-600 dark:text-red-400 scale-110' : ''}`}
							/>
							<span
								class={`text-[10px] sm:text-[11px] transition-all truncate w-full text-center ${isActive ? 'text-red-600 dark:text-red-400 font-bold' : 'font-medium'}`}
							>
								{item.mobileLabel || item.label}
							</span>
						</a>
					{/if}
				{/each}
			</div>
		</nav>
	{/if}

	{#if !isLiveRoom && isHistoryDrawerOpen}
		<div
			role="presentation"
			class="md:hidden fixed inset-0 bg-black/40 backdrop-blur-sm z-[10000]"
			onclick={closeHistoryDrawer}
			onkeydown={() => {}}
			transition:fade={{ duration: 200 }}
		></div>
		<div
			class="md:hidden fixed bottom-16 left-0 right-0 bg-white dark:bg-zinc-900 rounded-t-3xl z-[10001] shadow-2xl border-t border-gray-100 dark:border-white/5 overflow-hidden"
			transition:fly={{ y: 200, duration: 250, opacity: 0 }}
		>
			<div
				class="px-6 py-5 flex items-center justify-between border-b border-gray-100 dark:border-zinc-800"
			>
				<h3 class="text-lg font-bold text-gray-900 dark:text-white">
					{t('nav.history') || 'History'}
				</h3>
				<button
					onclick={closeHistoryDrawer}
					class="w-8 h-8 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
				>
					<X size={18} class="text-gray-500 dark:text-gray-400" />
				</button>
			</div>
			<div class="p-3 max-h-[calc(100dvh-12rem)] overflow-y-auto">
				{#each historyDrawerLinks as link}
					{@const isActive = link.match($page.url.pathname)}
					<a
						href={link.href}
						onclick={closeHistoryDrawer}
						class="flex items-center gap-4 px-4 py-3.5 rounded-2xl transition-all {isActive
							? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'
							: 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-800'}"
					>
						<div
							class="w-10 h-10 rounded-xl flex items-center justify-center {isActive
								? 'bg-red-100 dark:bg-red-900/30'
								: 'bg-gray-100 dark:bg-zinc-800'} shrink-0"
						>
							<link.icon size={20} />
						</div>
						<span class="font-bold text-sm flex-1">{link.label}</span>
						<ChevronRight size={18} class="text-gray-400 shrink-0" />
					</a>
				{/each}
			</div>
		</div>
	{/if}
</div>
