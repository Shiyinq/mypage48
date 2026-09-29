<script lang="ts">
	import { onMount } from 'svelte';
	import { Hash, ExternalLink } from 'lucide-svelte';
	import { members, type MemberXAccount } from '$lib/apis/members';
	import { ErrorState } from '$lib/components';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	let accounts = $state<MemberXAccount[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	onMount(() => {
		page48NavbarStore.pageType = 'members';
		load();
	});

	async function load() {
		try {
			loading = true;
			error = null;
			accounts = await members.getXAccounts();
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('page48.members.loadError');
		} finally {
			loading = false;
		}
	}

	function tagHref(username: string): string {
		return `/page48/tag/${username.toLowerCase()}`;
	}
</script>

<div
	class="max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	<div class="px-5 sm:px-6 pt-6 pb-4 border-b border-gray-100/60 dark:border-white/5">
		<div class="flex items-center gap-2">
			<Hash size={22} class="text-red-500" />
			<h1 class="text-xl font-bold text-gray-900 dark:text-gray-100">
				{t('page48.members.title')}
			</h1>
		</div>
		<p class="text-[13px] text-gray-500 dark:text-gray-400 mt-1">
			{t('page48.members.subtitle')}
		</p>
	</div>

	{#if loading}
		<div class="p-4 space-y-3 animate-pulse">
			{#each Array(10) as _}
				<div class="flex items-center justify-between">
					<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-2/3"></div>
					<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-10"></div>
				</div>
			{/each}
		</div>
	{:else if error}
		<div class="p-6">
			<ErrorState title={t('page48.members.loadError')} description={error} onRetry={load} />
		</div>
	{:else if accounts.length === 0}
		<div class="p-12 text-center text-[13px] font-medium text-gray-400 dark:text-gray-500">
			{t('page48.members.empty')}
		</div>
	{:else}
		<ul class="divide-y divide-gray-100 dark:divide-white/5">
			{#each accounts as account (account.memberId)}
				<li class="flex items-center hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
					<a
						href={tagHref(account.username)}
						class="flex-1 min-w-0 flex items-center gap-2 px-5 sm:px-6 py-3 cursor-pointer"
						title={account.name}
					>
						<span class="font-semibold text-[15px] text-red-500 truncate">
							#{account.username}
						</span>
						{#if account.nickname}
							<span class="text-[13px] text-gray-400 dark:text-gray-500 truncate">
								{account.nickname}
							</span>
						{/if}
					</a>
					<a
						href={account.url}
						target="_blank"
						rel="noopener noreferrer"
						class="px-4 py-3 text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors cursor-pointer"
						aria-label={t('page48.aria.openX', { username: account.username })}
						title={t('page48.aria.openX', { username: account.username })}
					>
						<ExternalLink size={16} />
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</div>
