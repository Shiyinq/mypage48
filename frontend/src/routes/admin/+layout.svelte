<script lang="ts">
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { page } from '$app/stores';
	import { userProfile, isInitialDataLoaded } from '$lib/stores';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import TableSkeleton from '$lib/components/skeletons/TableSkeleton.svelte';
	import { ShieldCheck, Users, Music, UserCheck } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	let isAuthorized = false;

	// Auth Check
	$: handleAuthCheck(browser, $isInitialDataLoaded, $userProfile);

	function handleAuthCheck(isBrowser: boolean, loaded: boolean, profile: typeof $userProfile) {
		if (!isBrowser || !loaded) return;
		if (!profile?.isAdmin) {
			goto('/404-not-found', { replaceState: true });
		} else {
			isAuthorized = true;
		}
	}

	// Navigation tabs with theme colors
	$: tabs = [
		{
			path: '/admin',
			label: $t('admin.dashboard.tabs.users'),
			icon: UserCheck,
			activeClass:
				'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 border border-transparent',
			inactiveClass:
				'bg-white dark:bg-zinc-800 text-gray-600 dark:text-gray-300 border border-gray-100 dark:border-zinc-700 hover:bg-red-50 hover:text-red-600 hover:border-red-100 dark:hover:bg-red-900/20'
		},
		{
			path: '/admin/members',
			label: $t('admin.dashboard.tabs.members'),
			icon: Users,
			activeClass:
				'bg-pink-100 text-pink-600 dark:bg-pink-900/30 dark:text-pink-400 border border-transparent',
			inactiveClass:
				'bg-white dark:bg-zinc-800 text-gray-600 dark:text-gray-300 border border-gray-100 dark:border-zinc-700 hover:bg-pink-50 hover:text-pink-600 hover:border-pink-100 dark:hover:bg-pink-900/20'
		},
		{
			path: '/admin/setlists',
			label: $t('admin.dashboard.tabs.setlists'),
			icon: Music,
			activeClass:
				'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400 border border-transparent',
			inactiveClass:
				'bg-white dark:bg-zinc-800 text-gray-600 dark:text-gray-300 border border-gray-100 dark:border-zinc-700 hover:bg-purple-50 hover:text-purple-600 hover:border-purple-100 dark:hover:bg-purple-900/20'
		}
	];

	$: currentPath = $page.url.pathname;
</script>

<svelte:head>
	<title>{isAuthorized ? $t('admin.dashboard.title') : 'Page'} | MyPage48</title>
</svelte:head>

{#if isAuthorized}
	<div class="max-w-7xl mx-auto p-4 pb-24">
		<PageHeader
			title={$t('admin.dashboard.title')}
			subtitle={$t('admin.dashboard.subtitle')}
			icon={ShieldCheck}
			theme="red"
		>
			<div slot="actions" class="flex items-center gap-2">
				{#each tabs as tab}
					<a
						href={tab.path}
						class="px-4 py-2.5 rounded-full font-bold text-sm transition-all shadow-sm flex items-center gap-2 cursor-pointer {currentPath ===
						tab.path
							? tab.activeClass
							: tab.inactiveClass}"
					>
						<svelte:component this={tab.icon} class="w-4 h-4" />
						{tab.label}
					</a>
				{/each}
			</div>
		</PageHeader>

		<div class="mt-8">
			<slot />
		</div>
	</div>
{:else}
	<!-- Page Loading Skeleton -->
	<div class="max-w-7xl mx-auto p-4 pb-24">
		<PageHeader
			title={$t('admin.dashboard.title')}
			subtitle={$t('admin.dashboard.subtitle')}
			icon={ShieldCheck}
			theme="red"
		>
			<div slot="actions" class="flex items-center gap-2">
				{#each [1, 2, 3] as _}
					<div class="w-24 h-10 bg-gray-200 dark:bg-zinc-800/50 rounded-full animate-pulse"></div>
				{/each}
			</div>
		</PageHeader>

		<div class="mt-8">
			<TableSkeleton
				rows={10}
				columns={[
					$t('admin.users.table.userInfo'),
					$t('admin.users.table.email'),
					$t('admin.users.table.status'),
					$t('admin.users.table.created')
				]}
			/>
		</div>
	</div>
{/if}
