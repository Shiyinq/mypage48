<script lang="ts">
	export let params: Record<string, string> | undefined = undefined;
	import { page } from '$app/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { AudioLines, Users, Calendar, ChevronRight, History } from 'lucide-svelte';
	import { getThemeStyles } from '$lib/constants/theaterTheme';

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
		{ labelKey: 'theater.subNav.members', href: '/theater/members', icon: Users, theme: 'pink' },
		{ labelKey: 'theater.subNav.events', href: '/theater/events', icon: Calendar, theme: 'blue' }
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
		<!-- Header & Sub Navigation Wrapper -->
		<div class="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6">
			<!-- Theater Header -->
			<div class="flex items-center gap-3">
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
			<div
				class="flex items-center gap-2 overflow-x-auto pb-2 -mx-4 px-4 md:mx-0 md:px-0 md:pb-0 scrollbar-hide"
			>
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

				<!-- Events sub-link (History) - only show when on events pages -->
				{#if currentPath.startsWith('/theater/events')}
					<div class="flex items-center text-gray-300 dark:text-gray-600">
						<ChevronRight class="w-4 h-4" />
					</div>

					<!-- Calendar Link -->
					{@const calendarTheme = getThemeStyles('blue')}
					<a
						href="/theater/events/calendar"
						class={`flex items-center gap-2 px-4 py-2.5 rounded-full text-sm font-bold transition-all duration-200 whitespace-nowrap ${
							currentPath === '/theater/events/calendar'
								? calendarTheme.navActive
								: `bg-white dark:bg-zinc-900 text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-700 ${calendarTheme.navInactive}`
						}`}
					>
						<Calendar class="w-4 h-4" />
						{$t('theater.events.calendar') || 'Calendar'}
					</a>

					{@const historyTheme = getThemeStyles('orange')}
					<a
						href="/theater/events/history"
						class={`flex items-center gap-2 px-4 py-2.5 rounded-full text-sm font-bold transition-all duration-200 whitespace-nowrap ${
							currentPath === '/theater/events/history'
								? historyTheme.navActive
								: `bg-white dark:bg-zinc-900 text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-700 ${historyTheme.navInactive}`
						}`}
					>
						<History class="w-4 h-4" />
						{$t('theater.eventHistory.title')}
					</a>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Page Content -->
	<slot />
</div>
