<script lang="ts">
	import { browser } from '$app/environment';
	import { page } from '$app/stores';
	import { userProfile, isInitialDataLoaded } from '$lib/stores';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import NotFound from '$lib/components/NotFound.svelte';
	import { ShieldCheck, Users, Music, UserCheck, MessageSquare } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { goto } from '$app/navigation';
	import NavPills from '$lib/components/navigation/NavPills.svelte';
	import type { UserWithProfileStats } from '$lib/types';
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
		}
	]);
	let currentPath = $derived($page.url.pathname);
</script>

<svelte:head>
	<title>{authState === 'authorized' ? t('admin.dashboard.title') : 'Page'} | MyPage48</title>
</svelte:head>

{#if authState === 'authorized'}
	<div class="max-w-7xl mx-auto pt-4 sm:pt-6 pb-24">
		<PageHeader
			title={t('admin.dashboard.title')}
			subtitle={t('admin.dashboard.subtitle')}
			icon={ShieldCheck}
			theme="red"
		>
			{#snippet actions()}
				<div class="hidden sm:block">
					<NavPills items={tabs} {currentPath}>
						{#snippet item({ item })}
							<div>
								<div class="flex items-center justify-center px-0.5">
									<span>{item.label}</span>
								</div>
							</div>
						{/snippet}
					</NavPills>
				</div>
			{/snippet}
		</PageHeader>

		<div class="mt-2 sm:mt-8 px-4">
			{@render children?.()}
		</div>
	</div>
{:else if authState === 'unauthorized'}
	<!-- Show 404 page for unauthorized users - no skeleton shown -->
	<NotFound />
{:else}
	<!-- Loading - render nothing until auth check completes -->
{/if}
