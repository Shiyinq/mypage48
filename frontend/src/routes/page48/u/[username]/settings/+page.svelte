<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import SEO from '$lib/components/SEO.svelte';
	import { SettingsSections } from '$lib/components/settings';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	let username = $derived($page.params.username ?? '');
	let ownUsername = $derived(userProfile.data?.username ?? null);

	onMount(() => {
		// Gives the Page48 navbar its back arrow, like the profile it came from.
		page48NavbarStore.pageType = 'user-profile';
	});

	// These settings only ever edit the signed-in user's own account, so anything
	// else (signed out, or somebody else's username) is sent to the right place.
	$effect(() => {
		if (!isAuthenticated.value) {
			goto('/login');
			return;
		}
		if (ownUsername && ownUsername !== username) {
			goto(`/page48/u/${ownUsername}/settings`, { replaceState: true });
		}
	});
</script>

<SEO
	title={`${t('settings.title')} · Page48`}
	path={`/page48/u/${username}/settings`}
	description={t('seo.settings')}
/>

<div
	class="max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	<div class="px-4 sm:px-6 py-4">
		<SettingsSections showExtras={false} />
	</div>
</div>
