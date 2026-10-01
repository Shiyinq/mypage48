<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import FollowUserList from '$lib/components/page48/FollowUserList.svelte';

	const { t } = useTranslation();

	let username = $derived($page.params.username ?? '');

	onMount(() => {
		page48NavbarStore.pageType = 'user-profile';
	});
</script>

<SEO
	title={`${t('page48.userPage.followingTitle')} · @${username}`}
	path={`/page48/u/${username}/following`}
	description={t('page48.seo.userDesc')}
/>

<FollowUserList {username} mode="following" />
