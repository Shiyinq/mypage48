<script lang="ts">
	import { goto } from '$app/navigation';
	import { fade } from 'svelte/transition';
	import { ArrowLeft } from 'lucide-svelte';
	import { page48Api, type PostUserItem } from '$lib/api/page48';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import UserListItem from '$lib/components/page48/UserListItem.svelte';
	import PostActivityRowsSkeleton from '$lib/components/page48/PostActivityRowsSkeleton.svelte';
	import { ErrorState } from '$lib/components';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		username: string;
		mode: 'followers' | 'following';
	}

	let { username, mode }: Props = $props();

	const { t } = useTranslation();

	const PAGE_SIZE = 20;

	let users = $state<PostUserItem[]>([]);
	let loading = $state(true);
	let failed = $state(false);
	let loadingMore = $state(false);
	let hasMore = $state(false);
	let nextCursor = $state<string | null>(null);

	/** Bumped on every reload so stale responses are ignored. */
	let token = 0;

	let title = $derived(
		mode === 'followers' ? t('page48.userPage.followersTitle') : t('page48.userPage.followingTitle')
	);
	let emptyText = $derived(
		mode === 'followers' ? t('page48.userPage.emptyFollowers') : t('page48.userPage.emptyFollowing')
	);

	$effect(() => {
		// These lists are only served to signed-in users, so send guests to sign in.
		if (!isAuthenticated.value) {
			void goto('/login');
			return;
		}
		const name = username;
		const which = mode;
		if (!name) return;
		void load(name, which);
	});

	async function load(name: string, which: 'followers' | 'following') {
		const current = ++token;
		loading = true;
		failed = false;
		try {
			const res =
				which === 'followers'
					? await page48Api.getFollowers(name, PAGE_SIZE, null)
					: await page48Api.getFollowing(name, PAGE_SIZE, null);
			if (current !== token) return;
			users = res.data;
			hasMore = res.meta.hasMore;
			nextCursor = res.meta.nextCursor;
		} catch {
			if (current !== token) return;
			users = [];
			failed = true;
		} finally {
			if (current === token) loading = false;
		}
	}

	async function loadMore() {
		if (loadingMore || !hasMore || !nextCursor || loading) return;
		try {
			loadingMore = true;
			const res =
				mode === 'followers'
					? await page48Api.getFollowers(username, PAGE_SIZE, nextCursor)
					: await page48Api.getFollowing(username, PAGE_SIZE, nextCursor);
			users = [...users, ...res.data];
			hasMore = res.meta.hasMore;
			nextCursor = res.meta.nextCursor;
		} catch (err) {
			console.error(err);
		} finally {
			loadingMore = false;
		}
	}

	/** Back always lands on the profile these lists belong to. */
	function goBack() {
		void goto(`/page48/u/${username}`);
	}
</script>

<div
	class="max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	<div class="flex items-center gap-3 px-5 pb-1 pt-5 sm:px-6">
		<button
			class="-ml-1.5 cursor-pointer rounded-full p-1.5 text-gray-600 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-zinc-800"
			onclick={goBack}
			aria-label={t('page48.userPage.back')}
			title={t('page48.userPage.back')}
		>
			<ArrowLeft size={18} />
		</button>
		<h1 class="text-[16px] font-bold text-gray-900 dark:text-gray-100">{title}</h1>
	</div>

	{#if loading}
		<PostActivityRowsSkeleton kind="users" count={6} />
	{:else if failed}
		<div class="p-6">
			<ErrorState
				title={t('page48.activity.error')}
				description={t('page48.userPage.listErrorText')}
				onRetry={() => load(username, mode)}
			/>
		</div>
	{:else if users.length === 0}
		<div class="p-12 text-center text-[13px] font-medium text-gray-400 dark:text-gray-500">
			{emptyText}
		</div>
	{:else}
		<div
			class="flex flex-col divide-y divide-gray-200/60 dark:divide-white/10"
			in:fade={{ duration: 200 }}
		>
			{#each users as user (user.userId)}
				<UserListItem {user} showFollow />
			{/each}

			{#if loadingMore}
				<div class="flex justify-center p-4">
					<Page48Spinner />
				</div>
			{:else if hasMore}
				<div class="p-4 flex justify-center">
					<button
						class="rounded-full px-4 py-2 text-[13px] font-semibold text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors cursor-pointer"
						onclick={loadMore}
					>
						{t('page48.userPage.loadMore')}
					</button>
				</div>
			{/if}
		</div>
	{/if}
</div>
