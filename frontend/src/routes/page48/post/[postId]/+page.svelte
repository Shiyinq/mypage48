<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import type { Page48Post } from '$lib/api/page48';
	import PostDetailContent from '$lib/components/page48/PostDetailContent.svelte';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';

	const { t } = useTranslation();

	let postId = $derived($page.params.postId ?? '');
	// Exposed by PostDetailContent so the SEO tags can follow the loaded post.
	let focused = $state<Page48Post | null>(null);

	let seoTitle = $derived(focused ? `@${focused.username} · Page48` : t('page48.seo.postTitle'));
	let seoDescription = $derived(
		focused?.content?.trim() ? focused.content.trim().slice(0, 160) : t('page48.seo.postDesc')
	);
	let seoImage = $derived(focused?.images?.[0]?.url ?? undefined);

	onMount(() => {
		page48NavbarStore.pageType = 'post-detail';
	});
</script>

<SEO
	title={seoTitle}
	path={`/page48/post/${postId}`}
	description={seoDescription}
	image={seoImage}
	keywords="Page48, JKT48, postingan JKT48, komunitas JKT48"
/>

<div
	class="max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	<PostDetailContent {postId} bind:focused onDeleted={() => void goto('/page48')} />
</div>
