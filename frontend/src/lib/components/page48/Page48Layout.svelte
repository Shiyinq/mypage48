<script lang="ts">
	import { isImmersive } from '$lib/stores';
	import {
		ArrowLeft,
		Home,
		User,
		TrendingUp,
		Hash,
		Plus,
		Image as ImageIcon,
		Video,
		X
	} from 'lucide-svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import NavPills from '$lib/components/navigation/NavPills.svelte';
	import PostComposerModal from '$lib/components/page48/PostComposerModal.svelte';
	import type { ComponentType, Snippet } from 'svelte';
	import { AppBackground } from '$lib/components/common';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		children: Snippet;
		basePath: string;
	}

	let { children, basePath }: Props = $props();

	let composerOpen = $state(false);

	let profileHref = $derived(
		isAuthenticated.value && userProfile.data?.username
			? `/page48/u/${userProfile.data.username}`
			: '/login'
	);
	let profileAvatar = $derived(
		userProfile.data?.profilePicture_small || userProfile.data?.profilePicture || null
	);

	interface NavItem {
		label: string;
		mobileLabel: string;
		href: string;
		exact: boolean;
		icon: ComponentType;
		mobileOnly?: boolean;
	}

	const navItems = $derived.by((): NavItem[] => {
		return [
			{
				label: t('page48.nav.home'),
				mobileLabel: t('page48.nav.home'),
				href: basePath,
				exact: true,
				icon: Home
			},
			{
				label: t('page48.nav.photos'),
				mobileLabel: t('page48.nav.photos'),
				href: `${basePath}/photos`,
				exact: false,
				icon: ImageIcon
			},
			{
				label: t('page48.nav.videos'),
				mobileLabel: t('page48.nav.videos'),
				href: `${basePath}/videos`,
				exact: false,
				icon: Video
			},
			{
				label: t('page48.nav.trending'),
				mobileLabel: t('page48.nav.trending'),
				href: `${basePath}/trending`,
				exact: false,
				icon: TrendingUp,
				mobileOnly: true
			},
			{
				label: t('page48.nav.members'),
				mobileLabel: t('page48.nav.members'),
				href: `${basePath}/members`,
				exact: false,
				icon: Hash,
				mobileOnly: true
			}
		];
	});

	// Desktop shows the sidebars instead, so only mobile-specific menus are added there.
	const desktopNavItems = $derived(navItems.filter((item) => !item.mobileOnly));

	$effect(() => {
		isImmersive.set(true);
		return () => {
			isImmersive.set(false);
		};
	});

	const isBackIcon = $derived(
		page48NavbarStore.pageType === 'post-detail' ||
			page48NavbarStore.pageType === 'user-profile' ||
			page48NavbarStore.pageType === 'trending' ||
			page48NavbarStore.pageType === 'members'
	);

	// Immersive video mode: hide the top navbar on mobile so the clip fills the screen.
	let isVideoMode = $derived($page.url.pathname.startsWith('/page48/videos'));

	function handleBackClick(e: MouseEvent) {
		if (isBackIcon) {
			e.preventDefault();
			window.history.back();
		} else {
			goto('/');
		}
	}
</script>

<div
	class="flex flex-col min-h-screen w-full relative bg-[#f0f2f5] dark:bg-zinc-950 transition-colors"
>
	<AppBackground hideDecorationsOnMobile={true} />

	<!-- Main Page48 Navbar (hidden on mobile in immersive video mode) -->
	<div
		class={`fixed top-0 left-0 right-0 w-full z-[50] border-b border-black/5 dark:border-white/5 bg-white/85 dark:bg-zinc-950/60 backdrop-blur-xl ${isVideoMode ? 'hidden xl:block' : ''}`}
	>
		<div
			class="max-w-7xl mx-auto w-full h-16 flex items-center justify-between px-4 sm:px-6 lg:px-8"
		>
			<div class="flex-1 min-w-0">
				<a
					href="/"
					onclick={handleBackClick}
					class="flex items-center gap-2 sm:gap-3 text-slate-900 dark:text-white hover:text-red-600 transition-colors cursor-pointer inline-flex group"
				>
					<div
						class="w-8 h-8 flex items-center justify-center rounded-full bg-white dark:bg-zinc-900 shadow-sm border border-gray-200 dark:border-zinc-800 group-hover:border-red-200 dark:group-hover:border-red-900/50 group-hover:shadow-md transition-all"
					>
						{#if isBackIcon}
							<ArrowLeft
								size={16}
								class="shrink-0 text-slate-500 dark:text-slate-400 group-hover:text-red-600 dark:group-hover:text-red-600"
							/>
						{:else}
							<X
								size={16}
								class="shrink-0 text-slate-500 dark:text-slate-400 group-hover:text-red-600 dark:group-hover:text-red-600"
							/>
						{/if}
					</div>
					<span class="font-extrabold tracking-tight text-lg whitespace-nowrap inline-block"
						>Page<span class="text-red-600 italic">48</span></span
					>
				</a>
			</div>

			<div class="hidden xl:flex items-center justify-center">
				<NavPills
					items={desktopNavItems}
					currentPath={$page.url.pathname}
					className="bg-white/50 dark:bg-zinc-900/50 border-gray-200 dark:border-zinc-800 shadow-sm shrink-0"
				/>
			</div>

			<div class="flex-1 flex justify-end items-center gap-2">
				{#if isAuthenticated.value}
					<!-- New post -->
					<button
						onclick={() => (composerOpen = true)}
						aria-label={t('page48.composer.submit')}
						title={t('page48.composer.newPost')}
						class="h-9 px-3.5 rounded-full flex items-center gap-1.5 bg-red-600 hover:bg-red-700 text-white text-[13px] font-bold shadow-sm transition-colors shrink-0 cursor-pointer"
					>
						<Plus size={16} />
						{t('page48.composer.submit')}
					</button>
				{/if}

				<!-- Profile / account -->
				<a
					href={profileHref}
					aria-label={t('page48.aria.profile')}
					class="w-9 h-9 rounded-full overflow-hidden bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors shrink-0 ring-2 ring-white dark:ring-zinc-900 shadow-sm"
				>
					{#if isAuthenticated.value && profileAvatar}
						<img
							src={profileAvatar}
							alt={t('page48.aria.profile')}
							class="w-full h-full object-cover"
							onerror={(e) => {
								(e.target as HTMLImageElement).src =
									`https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile.data?.name || '')}&background=fca5a5&color=fff`;
							}}
						/>
					{:else}
						<User size={18} class="text-zinc-600 dark:text-zinc-400" />
					{/if}
				</a>
			</div>
		</div>
	</div>

	<!-- Content Area -->
	<div
		class={`flex-1 relative w-full ${isVideoMode ? 'pt-0 xl:pt-16 pb-0' : 'pt-16 pb-16 xl:pb-0'}`}
	>
		{@render children()}
	</div>

	<!-- Mobile/tablet bottom navbar (desktop shows pills + sidebars) -->
	<nav
		class="xl:hidden fixed bottom-0 left-0 right-0 z-[50] backdrop-blur-xl border-t pb-safe shadow-[0_-4px_20px_rgba(0,0,0,0.03)] dark:shadow-none transition-all duration-300 ease-in-out bg-white/85 dark:bg-zinc-950/60 border-black/5 dark:border-white/5"
	>
		<div
			class="flex h-16 items-center justify-around w-full overflow-x-auto no-scrollbar px-2 max-w-[420px] mx-auto"
		>
			{#each navItems as item}
				{@const isActive = item.exact
					? $page.url.pathname === item.href
					: $page.url.pathname.startsWith(item.href)}
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
						{item.mobileLabel || item.label}
					</span>
				</a>
			{/each}
		</div>
	</nav>

	{#if composerOpen}
		<PostComposerModal onClose={() => (composerOpen = false)} />
	{/if}
</div>
