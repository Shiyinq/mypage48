<script lang="ts">
	import { onMount } from 'svelte';
	import { Hash, ExternalLink } from 'lucide-svelte';
	import { page } from '$app/stores';
	import { members, type MemberXAccount } from '$lib/apis/members';
	import { getActiveMedia, tagUrl } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	let accounts = $state<MemberXAccount[]>([]);
	let loading = $state(true);
	// Keep the active media filter (Gambar/Video) when opening a tag.
	let activeMedia = $derived(getActiveMedia($page.url.pathname, $page.url.search));

	onMount(async () => {
		try {
			accounts = await members.getXAccounts();
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	});

	function tagHref(username: string): string {
		return tagUrl(username, activeMedia);
	}
</script>

<section
	class="flex flex-col max-h-[calc(100vh-6rem)] rounded-2xl bg-white/80 dark:bg-zinc-900/80 border border-gray-200/70 dark:border-white/10 backdrop-blur-xl overflow-hidden"
>
	<div
		class="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-white/5 shrink-0"
	>
		<Hash size={16} class="text-red-500" />
		<h2 class="font-bold text-[15px] text-gray-900 dark:text-gray-100">
			{t('page48.members.title')}
		</h2>
	</div>

	{#if loading}
		<div class="p-4 space-y-3 animate-pulse">
			{#each Array(8) as _}
				<div class="flex items-center justify-between">
					<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-2/3"></div>
					<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-10"></div>
				</div>
			{/each}
		</div>
	{:else if accounts.length === 0}
		<div class="p-5 text-center text-[13px] text-gray-400 dark:text-gray-500">
			{t('page48.members.empty')}
		</div>
	{:else}
		<ul
			class="flex-1 min-h-0 overflow-y-auto divide-y divide-gray-100 dark:divide-white/5 scroll-hover"
		>
			{#each accounts as account (account.memberId)}
				<li class="flex items-center hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
					<a
						href={tagHref(account.username)}
						class="flex-1 min-w-0 flex items-center gap-2 px-4 py-2.5 cursor-pointer"
						title={account.name}
					>
						<span class="font-semibold text-[14px] text-red-500 truncate">
							#{account.username}
						</span>
						{#if account.nickname}
							<span class="text-[12px] text-gray-400 dark:text-gray-500 truncate">
								{account.nickname}
							</span>
						{/if}
					</a>
					<a
						href={account.url}
						target="_blank"
						rel="noopener noreferrer"
						class="px-3 py-2.5 text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors cursor-pointer"
						aria-label={t('page48.aria.openX', { username: account.username })}
						title={t('page48.aria.openX', { username: account.username })}
					>
						<ExternalLink size={14} />
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</section>

<style>
	/* Scrollbar stays hidden until hover, so users know the list is scrollable. */
	.scroll-hover {
		scrollbar-width: thin;
		scrollbar-color: transparent transparent;
	}

	.scroll-hover:hover {
		scrollbar-color: rgba(100, 116, 139, 0.5) transparent;
	}

	.scroll-hover::-webkit-scrollbar {
		width: 6px;
	}

	.scroll-hover::-webkit-scrollbar-track {
		background: transparent;
	}

	.scroll-hover::-webkit-scrollbar-thumb {
		background: transparent;
		border-radius: 9999px;
	}

	.scroll-hover:hover::-webkit-scrollbar-thumb {
		background: rgba(100, 116, 139, 0.5);
	}

	.scroll-hover:hover::-webkit-scrollbar-thumb:hover {
		background: rgba(100, 116, 139, 0.8);
	}
</style>
