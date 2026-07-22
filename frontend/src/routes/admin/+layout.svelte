<script lang="ts">
	import { browser } from '$app/environment';
	import { page } from '$app/stores';
	import { userProfile, isInitialDataLoaded, isImmersive } from '$lib/stores';
	import NotFound from '$lib/components/NotFound.svelte';
	import {
		ShieldCheck,
		Users,
		Music,
		UserCheck,
		MessageSquare,
		Settings,
		X,
		ChevronRight,
		Menu
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { goto, afterNavigate } from '$app/navigation';
	import NavPills from '$lib/components/navigation/NavPills.svelte';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import { fade, fly } from 'svelte/transition';
	import type { UserWithProfileStats } from '$lib/types';
	import type { ComponentType } from 'svelte';
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	const { t } = useTranslation();

	// State: 'loading' | 'authorized' | 'unauthorized'
	let authState: 'loading' | 'authorized' | 'unauthorized' = $state('loading');

	function handleAuthCheck(
		isBrowser: boolean,
		loaded: boolean,
		profile: { data: UserWithProfileStats | null; error: string | null }
	) {
		if (!isBrowser) return;

		// If finished loading, we can check permissions
		if (loaded) {
			const profileData = profile.data;
			if (profileData?.isAdmin) {
				authState = 'authorized';
			} else {
				// If loaded and not admin -> unauthorized
				// But maybe we want to redirect?
				// Constructive approach: redirect to home if not admin
				goto('/');
			}
		}
	}

	// Watch for auth/profile changes
	$effect(() => {
		handleAuthCheck(browser, isInitialDataLoaded.value, {
			data: userProfile.data,
			error: userProfile.error
		});
	});
	// Navigation tabs
	let tabs = $derived([
		{
			href: '/admin',
			label: t('admin.dashboard.tabs.dashboard'),
			icon: ShieldCheck,
			exact: true,
			activeClass: 'bg-indigo-500 shadow-indigo-500/20'
		},
		{
			href: '/admin/users',
			label: t('admin.dashboard.tabs.users'),
			icon: UserCheck,
			exact: true,
			activeClass: 'bg-red-500 shadow-red-500/20'
		},
		{
			href: '/admin/members',
			label: t('admin.dashboard.tabs.members'),
			icon: Users,
			activeClass: 'bg-pink-500 shadow-pink-500/20'
		},
		{
			href: '/admin/setlists',
			label: t('admin.dashboard.tabs.setlists'),
			icon: Music,
			activeClass: 'bg-purple-500 shadow-purple-500/20'
		},
		{
			href: '/admin/feedback',
			label: t('admin.dashboard.tabs.feedback'),
			icon: MessageSquare,
			activeClass: 'bg-cyan-500 shadow-cyan-500/20'
		},
		{
			href: '/admin/settings',
			label: t('admin.dashboard.tabs.settings'),
			icon: Settings,
			activeClass: 'bg-slate-500 shadow-slate-500/20'
		}
	]);

	type MobileNavItem =
		| { isDrawer: true; icon: ComponentType; mobileLabel: string }
		| {
				isDrawer?: false;
				href: string;
				label: string;
				icon: ComponentType;
				exact?: boolean;
		  };

	let mobileNavItems = $derived<MobileNavItem[]>([
		{
			href: '/admin',
			label: t('admin.dashboard.tabs.dashboard'),
			icon: ShieldCheck,
			exact: true
		},
		{
			href: '/admin/users',
			label: t('admin.dashboard.tabs.users'),
			icon: UserCheck,
			exact: true
		},
		{
			href: '/admin/members',
			label: t('admin.dashboard.tabs.members'),
			icon: Users
		},
		{
			href: '/admin/setlists',
			label: t('admin.dashboard.tabs.setlists'),
			icon: Music
		},
		{ isDrawer: true, icon: Menu, mobileLabel: t('admin.dashboard.tabs.more') || 'Lainnya' }
	]);

	const moreDrawerLinks = $derived<
		{ href: string; label: string; icon: ComponentType; exact?: boolean }[]
	>([
		{
			href: '/admin/feedback',
			label: t('admin.dashboard.tabs.feedback'),
			icon: MessageSquare
		},
		{
			href: '/admin/settings',
			label: t('admin.dashboard.tabs.settings'),
			icon: Settings
		}
	]);

	let currentPath = $derived($page.url.pathname);

	let isMoreDrawerOpen = $state(false);

	function closeMoreDrawer() {
		isMoreDrawerOpen = false;
	}

	function toggleMoreDrawer() {
		isMoreDrawerOpen = !isMoreDrawerOpen;
	}

	afterNavigate(() => {
		closeMoreDrawer();
	});

	$effect(() => {
		isImmersive.set(true);
		return () => {
			isImmersive.set(false);
		};
	});
</script>

<svelte:head>
	<title>{authState === 'authorized' ? t('admin.dashboard.title') : 'Page'} | MyPage48</title>
</svelte:head>

{#if authState === 'authorized'}
	<div class="flex flex-col min-h-screen w-full relative bg-slate-50 dark:bg-zinc-950">
		<AppBackground hideDecorationsOnMobile={true} />
		<!-- Main Admin Navbar -->
		<div
			class="fixed top-0 left-0 right-0 w-full z-[100] border-b border-black/5 dark:border-white/5 bg-white/85 dark:bg-zinc-950/60 backdrop-blur-xl transition-all duration-300 ease-in-out"
		>
			<div
				class="max-w-7xl mx-auto w-full h-16 flex items-center justify-between px-4 sm:px-6 lg:px-8"
			>
				<div class="flex-1 min-w-0">
					<a
						href="/"
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
							>Dashboard <span class="text-red-600 italic">Admin</span></span
						>
					</a>
				</div>

				<div class="hidden md:flex items-center justify-center">
					<NavPills
						items={tabs}
						{currentPath}
						className="bg-gray-100/50 dark:bg-zinc-900/50 border-gray-200 dark:border-zinc-800 shadow-sm shrink-0"
					>
						{#snippet item({ item })}
							<div>
								<div class="flex items-center justify-center px-0.5">
									<span>{item.label}</span>
								</div>
							</div>
						{/snippet}
					</NavPills>
				</div>

				<!-- Right: Page Specific Actions -->
				<div class="flex-1 flex justify-end items-center">
					<!-- Optional right section -->
				</div>
			</div>
		</div>

		<!-- Content Area -->
		<div class="flex-1 relative pt-16 pb-20 md:pb-8">
			<div class="max-w-7xl mx-auto">
				<div class="mt-4 sm:mt-8 px-4">
					{@render children?.()}
				</div>
			</div>
		</div>

		<!-- Mobile Specific Admin Navbar (Bottom) -->
		<nav
			class="md:hidden fixed bottom-0 left-0 right-0 z-[102] pb-safe shadow-[0_-4px_20px_rgba(0,0,0,0.03)] dark:shadow-none transition-all duration-300 ease-in-out {isMoreDrawerOpen
				? 'bg-white dark:bg-zinc-950 border-t border-black/5 dark:border-white/5'
				: 'bg-white/85 dark:bg-zinc-950/60 backdrop-blur-xl border-t border-black/5 dark:border-white/5'}"
		>
			<div
				class="flex h-16 items-center justify-around w-full overflow-x-auto no-scrollbar px-2 max-w-[420px] mx-auto"
			>
				{#each mobileNavItems as item}
					{#if item.isDrawer}
						{@const isMoreActive =
							isMoreDrawerOpen ||
							moreDrawerLinks.some((link) =>
								link.exact ? currentPath === link.href : currentPath.startsWith(link.href)
							)}
						<button
							onclick={toggleMoreDrawer}
							class="flex flex-col items-center justify-center gap-0.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 active:scale-90 active:opacity-70 transition-all duration-200 group min-w-[60px] shrink-0"
						>
							<item.icon
								class="w-6 h-6 transition-all {isMoreActive
									? 'text-red-600 dark:text-red-400 scale-110'
									: ''}"
							/>
							<span
								class="text-[10px] sm:text-[11px] transition-all truncate w-full text-center font-medium {isMoreActive
									? 'text-red-600 dark:text-red-400 font-bold'
									: ''}"
							>
								{item.mobileLabel}
							</span>
						</button>
					{:else}
						{@const isActive = item.exact
							? currentPath === item.href
							: currentPath.startsWith(item.href)}
						<a
							href={item.href}
							class="flex flex-col items-center justify-center gap-0.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 active:scale-90 active:opacity-70 transition-all duration-200 group min-w-[60px] shrink-0"
						>
							<item.icon
								class={`w-6 h-6 transition-all ${isActive ? 'text-red-600 dark:text-red-400 scale-110' : ''}`}
							/>
							<span
								class={`text-[10px] sm:text-[11px] transition-all truncate w-full text-center ${isActive ? 'text-red-600 dark:text-red-400 font-bold' : 'font-medium'}`}
							>
								{item.label}
							</span>
						</a>
					{/if}
				{/each}
			</div>
		</nav>

		{#if isMoreDrawerOpen}
			<div
				role="presentation"
				class="md:hidden fixed inset-0 bg-black/40 backdrop-blur-sm z-[100]"
				onclick={closeMoreDrawer}
				onkeydown={() => {}}
				transition:fade={{ duration: 200 }}
			></div>
			<div
				class="md:hidden fixed bottom-16 left-0 right-0 bg-white dark:bg-zinc-900 rounded-t-3xl z-[101] shadow-2xl border-t border-gray-100 dark:border-white/5 overflow-hidden"
				transition:fly={{ y: 200, duration: 250, opacity: 0 }}
			>
				<div
					class="px-6 py-5 flex items-center justify-between border-b border-gray-100 dark:border-zinc-800"
				>
					<h3 class="text-lg font-bold text-gray-900 dark:text-white">
						{t('admin.dashboard.tabs.more') || 'Lainnya'}
					</h3>
					<button
						onclick={closeMoreDrawer}
						class="w-8 h-8 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
					>
						<X size={18} class="text-gray-500 dark:text-gray-400" />
					</button>
				</div>
				<div class="p-3 max-h-[calc(100dvh-12rem)] overflow-y-auto">
					{#each moreDrawerLinks as link}
						{@const isActive = link.exact
							? currentPath === link.href
							: currentPath.startsWith(link.href)}
						<a
							href={link.href}
							onclick={closeMoreDrawer}
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
{:else if authState === 'unauthorized'}
	<!-- Show 404 page for unauthorized users - no skeleton shown -->
	<NotFound />
{:else}
	<!-- Loading - render nothing until auth check completes -->
{/if}
