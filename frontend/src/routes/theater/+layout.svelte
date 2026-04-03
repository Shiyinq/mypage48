<script lang="ts">
	import { page } from '$app/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		AudioLines,
		Users,
		Calendar,
		ChevronRight,
		History,
		Newspaper,
		ArrowUpDown,
		Tv
	} from 'lucide-svelte';
	import { getThemeStyles } from '$lib/constants/theaterTheme';
	import { crossfade } from 'svelte/transition';
	import { cubicInOut } from 'svelte/easing';

	const [send, receive] = crossfade({
		duration: 300,
		easing: cubicInOut
	});

	const { t } = useTranslation();

	$: currentPath = $page.url.pathname;

	// Check if on setlist detail page (UUID pattern in URL)
	$: isDetailPage =
		/^\/theater\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(currentPath);

	// Check if on live single detail or multiview page — hide header for immersive player
	$: isLiveDetailPage =
		/^\/theater\/live\/.+/.test(currentPath);

	// Dynamic Title, Subtitle & Theme
	$: pageInfo = (() => {
		if (currentPath.includes('/theater/news')) {
			return {
				title: $t('theater.news.title') || 'News',
				subtitle: $t('theater.news.subtitle') || 'Latest updates and announcements',
				icon: Newspaper,
				theme: 'red'
			};
		}
		if (currentPath.includes('/theater/members')) {
			return {
				title: $t('theater.members.title'),
				subtitle: $t('theater.members.subtitle'),
				icon: Users,
				theme: 'pink'
			};
		}
		if (currentPath.includes('/theater/sorter')) {
			return {
				title: $t('theater.sorter.title'),
				subtitle: $t('theater.sorter.subtitle'),
				icon: ArrowUpDown,
				theme: 'rose'
			};
		}
		if (currentPath.includes('/theater/events/history')) {
			return {
				title: $t('theater.eventHistory.title') || 'Event History',
				subtitle: $t('theater.eventHistory.subtitle') || 'Past events',
				icon: Calendar,
				theme: 'orange'
			};
		}
		if (currentPath.includes('/theater/events')) {
			return {
				title: $t('theater.events.title') || 'Events',
				subtitle: $t('theater.events.subtitle') || 'Browse theater events',
				icon: Calendar,
				theme: 'blue'
			};
		}
		if (currentPath.includes('/theater/live')) {
			return {
				title: 'JKT48 LIVE',
				subtitle: $t('theater.live.subtitle'),
				icon: Tv,
				theme: 'red'
			};
		}
		return {
			title: $t('theater.title'),
			subtitle: $t('theater.subtitle'),
			icon: AudioLines,
			theme: 'purple'
		};
	})();

	$: currentThemeStyles = getThemeStyles(pageInfo.theme);

	// Sub-navigation items
	$: subNavItems = [
		{
			labelKey: 'theater.subNav.theater',
			href: '/theater',
			icon: AudioLines,
			exact: true,
			theme: 'purple'
		},
		{
			labelKey: 'theater.subNav.members',
			href: '/theater/members',
			icon: Users,
			theme: 'pink'
		},
		{
			labelKey: 'theater.subNav.news',
			labelDefault: 'News',
			href: '/theater/news',
			icon: Newspaper,
			theme: 'red'
		},
		{
			labelKey: 'theater.subNav.events',
			href: '/theater/events',
			icon: Calendar,
			exact: true,
			theme: 'blue'
		},
		{
			labelKey: 'theater.subNav.calendar',
			labelDefault: 'Calendar',
			href: '/theater/events/calendar',
			icon: Calendar,
			theme: 'blue'
		},
		{
			labelKey: 'theater.subNav.history',
			labelDefault: 'History',
			href: '/theater/events/history',
			icon: History,
			theme: 'orange'
		},
		{
			labelKey: 'theater.subNav.sorter',
			labelDefault: 'Sorter',
			href: '/theater/sorter',
			icon: ArrowUpDown,
			theme: 'rose'
		},
		{
			labelKey: 'theater.subNav.live',
			labelDefault: 'Live',
			href: '/theater/live',
			icon: Tv,
			theme: 'red'
		}
	];

	// Check if current path matches nav item
	$: isActive = (href: string, exact: boolean = false) => {
		if (exact) {
			return currentPath === href;
		}
		return currentPath.startsWith(href);
	};
</script>

<div class="max-w-6xl mx-auto p-4 pb-24">
	{#if !isDetailPage && !isLiveDetailPage}
		<!-- Theater Header & Sub Navigation Wrapper -->
		<div class="flex flex-col lg:flex-row lg:items-start justify-between gap-6 mb-10">
			<!-- Theater Header -->
			<div class="flex items-center gap-4 flex-shrink-0">
				<div
					class={`p-3.5 rounded-2xl shadow-xl border-2 border-white dark:border-zinc-700 transform -rotate-6 transition-all duration-300 ${currentThemeStyles.headerIcon}`}
				>
					<svelte:component this={pageInfo.icon} class="w-7 h-7" />
				</div>
				<div class="flex flex-col">
					<h2
						class="text-3xl font-black tracking-tighter text-gray-900 dark:text-white leading-tight relative w-fit"
					>
						{pageInfo.title}
						<span
							class={`absolute -bottom-1 left-0 w-full h-2.5 -z-10 transform -skew-x-12 rounded-sm transition-colors duration-300 ${currentThemeStyles.titleLine}`}
						></span>
					</h2>
					<p class="text-[13px] font-medium text-themed-secondary mt-0.5">{pageInfo.subtitle}</p>
				</div>
			</div>

			<!-- Sub Navigation Tabs -->
			<div
				class="flex items-center gap-1 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md border border-gray-100 dark:border-zinc-800 p-1 rounded-full shadow-sm overflow-x-auto scrollbar-hide"
			>
				{#each subNavItems as item (item.href)}
					{@const active = isActive(item.href, item.exact)}
					{@const itemTheme = getThemeStyles(item.theme || 'purple')}
					<a
						href={item.href}
						class="relative px-4 py-1.5 rounded-full text-[11px] font-black uppercase tracking-widest transition-all duration-200 flex items-center justify-center whitespace-nowrap {active
							? 'text-white'
							: 'text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white hover:bg-white/80 dark:hover:bg-zinc-800'}"
					>
						{#if active}
							<div
								class="absolute inset-0 rounded-full shadow-lg z-0 {itemTheme.navActive}"
								in:receive={{ key: 'theater-nav-active' }}
								out:send={{ key: 'theater-nav-active' }}
							></div>
						{/if}
						<span class="relative z-10 flex items-center justify-center">
							<span>{$t(item.labelKey) || item.labelDefault}</span>
						</span>
					</a>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Page Content -->
	<slot />
</div>
