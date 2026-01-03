<script lang="ts">
	import { page } from '$app/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Mic2, Users, Calendar, ChevronRight, History } from 'lucide-svelte';

	const { t } = useTranslation();

	$: currentPath = $page.url.pathname;

	// Check if on setlist detail page (UUID pattern in URL)
	$: isDetailPage =
		/^\/theater\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(currentPath);

	// Dynamic Title, Subtitle & Theme
	$: pageInfo = (() => {
		if (currentPath.includes('/theater/members')) {
			return {
				title: $t('theater.members.title'),
				subtitle: $t('theater.members.subtitle'),
				icon: Users,
				theme: 'pink'
			};
		}
		if (currentPath.includes('/theater/shows/history')) {
			return {
				title: $t('theater.showHistory.title') || 'Show History',
				subtitle: $t('theater.showHistory.subtitle') || 'Past performances',
				icon: Calendar,
				theme: 'orange'
			};
		}
		if (currentPath.includes('/theater/shows')) {
			return {
				title: $t('theater.shows.title') || 'Shows',
				subtitle: $t('theater.shows.subtitle') || 'Browse theater shows',
				icon: Calendar,
				theme: 'blue'
			};
		}
		return {
			title: $t('theater.title'),
			subtitle: $t('theater.subtitle'),
			icon: Mic2,
			theme: 'purple'
		};
	})();

	// Theme configuration
	const getThemeStyles = (theme: string) => {
		const styles = {
			pink: {
				navActive:
					'bg-pink-100 dark:bg-pink-500/20 text-pink-600 dark:text-pink-400 shadow-sm ring-1 ring-pink-200 dark:ring-pink-500/30',
				navInactive:
					'hover:text-pink-600 dark:hover:text-pink-400 hover:bg-pink-50 dark:hover:bg-pink-900/20 border-gray-100 dark:border-zinc-700',
				headerIcon:
					'bg-pink-50 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 shadow-pink-100 dark:shadow-pink-900/20',
				titleLine: 'bg-pink-200/60 dark:bg-pink-500/30'
			},
			blue: {
				navActive:
					'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 shadow-sm ring-1 ring-blue-200 dark:ring-blue-500/30',
				navInactive:
					'hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 border-gray-100 dark:border-zinc-700',
				headerIcon:
					'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 shadow-blue-100 dark:shadow-blue-900/20',
				titleLine: 'bg-blue-200/60 dark:bg-blue-500/30'
			},
			orange: {
				navActive:
					'bg-orange-100 dark:bg-orange-500/20 text-orange-600 dark:text-orange-400 shadow-sm ring-1 ring-orange-200 dark:ring-orange-500/30',
				navInactive:
					'hover:text-orange-600 dark:hover:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20 border-gray-100 dark:border-zinc-700',
				headerIcon:
					'bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 shadow-orange-100 dark:shadow-orange-900/20',
				titleLine: 'bg-orange-200/60 dark:bg-orange-500/30'
			},
			purple: {
				navActive:
					'bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 shadow-sm ring-1 ring-purple-200 dark:ring-purple-500/30',
				navInactive:
					'hover:text-purple-600 dark:hover:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 border-gray-100 dark:border-zinc-700',
				headerIcon:
					'bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 shadow-purple-100 dark:shadow-purple-900/20',
				titleLine: 'bg-purple-200/60 dark:bg-purple-500/30'
			}
		};
		return styles[theme as keyof typeof styles] || styles.purple;
	};

	$: currentThemeStyles = getThemeStyles(pageInfo.theme);

	// Sub-navigation items
	$: subNavItems = [
		{
			labelKey: 'theater.subNav.theater',
			href: '/theater',
			icon: Mic2,
			exact: true,
			theme: 'purple'
		},
		{ labelKey: 'theater.subNav.members', href: '/theater/members', icon: Users, theme: 'pink' },
		{ labelKey: 'theater.subNav.shows', href: '/theater/shows', icon: Calendar, theme: 'blue' }
	];

	// Check if current path matches nav item
	$: isActive = (href: string, exact: boolean = false) => {
		if (exact) {
			return currentPath === href;
		}
		return currentPath.startsWith(href);
	};
</script>

<div class="max-w-6xl mx-auto p-4 pb-24 animate-fade-in">
	{#if !isDetailPage}
		<!-- Theater Header -->
		<div class="flex items-center gap-3 mb-6">
			<div
				class={`p-3 rounded-2xl shadow-lg border-2 border-white dark:border-zinc-700 transform -rotate-6 transition-colors duration-300 ${currentThemeStyles.headerIcon}`}
			>
				<svelte:component this={pageInfo.icon} class="w-6 h-6" />
			</div>
			<div>
				<h2 class="text-2xl font-bold text-themed w-fit relative">
					{pageInfo.title}
					<span
						class={`absolute -bottom-1 left-0 w-full h-2 -z-10 transform -skew-x-12 rounded-sm transition-colors duration-300 ${currentThemeStyles.titleLine}`}
					></span>
				</h2>
				<p class="text-sm text-themed-secondary">{pageInfo.subtitle}</p>
			</div>
		</div>

		<!-- Sub Navigation Tabs -->
		<div class="flex items-center gap-2 mb-6 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
			{#each subNavItems as item}
				{@const active = isActive(item.href, item.exact)}
				{@const itemTheme = getThemeStyles(item.theme || 'purple')}
				<a
					href={item.href}
					class={`flex items-center gap-2 px-4 py-2.5 rounded-full text-sm font-bold transition-all duration-200 whitespace-nowrap ${
						active
							? itemTheme.navActive
							: `bg-white dark:bg-zinc-900 text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-700 ${itemTheme.navInactive}`
					}`}
				>
					<svelte:component this={item.icon} class="w-4 h-4" />
					{$t(item.labelKey)}
				</a>
			{/each}

			<!-- Shows sub-link (History) - only show when on shows pages -->
			{#if currentPath.startsWith('/theater/shows')}
				<div class="flex items-center text-gray-300 dark:text-gray-600">
					<ChevronRight class="w-4 h-4" />
				</div>
				{@const historyTheme = getThemeStyles('orange')}
				<a
					href="/theater/shows/history"
					class={`flex items-center gap-2 px-4 py-2.5 rounded-full text-sm font-bold transition-all duration-200 whitespace-nowrap ${
						currentPath === '/theater/shows/history'
							? historyTheme.navActive
							: `bg-white dark:bg-zinc-900 text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-700 ${historyTheme.navInactive}`
					}`}
				>
					<History class="w-4 h-4" />
					{$t('theater.showHistory.title')}
				</a>
			{/if}
		</div>
	{/if}

	<!-- Page Content -->
	<slot />
</div>
