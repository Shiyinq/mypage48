<script lang="ts">
	import { isImmersive } from '$lib/stores';
	import { X, Tv, LayoutGrid, Globe, History, Image as ImageIcon } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { page } from '$app/stores';
	import NavPills from '$lib/components/navigation/NavPills.svelte';
	import { liveNavbarStore } from '$lib/stores/liveNavbar.svelte';
	import type { Snippet } from 'svelte';

	const { t } = useTranslation();

	interface Props {
		children: Snippet;
		basePath: string;
		backPath: string;
	}

	let { children, basePath, backPath }: Props = $props();

	const isLiveRoom = $derived(!!$page.params.platform && !!$page.params.id);

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
			class="shrink-0 w-full z-[10000] border-b border-black/5 dark:border-white/5 bg-white/95 dark:bg-zinc-950/95 backdrop-blur-xl"
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
	<div class="flex-1 relative overflow-hidden">
		{@render children()}
	</div>

	<!-- Mobile Specific Live Navbar (Bottom) -->
	{#if !isLiveRoom}
		<nav
			class="md:hidden fixed bottom-0 left-0 right-0 backdrop-blur-xl border-t z-[10000] pb-safe shadow-[0_-4px_20px_rgba(0,0,0,0.03)] dark:shadow-none transition-all duration-300 ease-in-out bg-white/60 dark:bg-zinc-950/60 border-black/5 dark:border-white/5"
		>
			<div
				class="flex h-16 items-center justify-around w-full overflow-x-auto no-scrollbar px-2 max-w-[420px] mx-auto"
			>
				{#each navItems as item}
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
				{/each}
			</div>
		</nav>
	{/if}
</div>
