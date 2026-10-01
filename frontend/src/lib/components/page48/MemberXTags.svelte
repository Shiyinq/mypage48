<script lang="ts">
	import { onMount } from 'svelte';
	import { Hash, ExternalLink } from 'lucide-svelte';
	import { page } from '$app/stores';
	import { memberXTagsStore } from '$lib/stores/page48.svelte';
	import { getActiveMedia, tagUrl } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/**
		 * `card` is the fixed-height sidebar card. `inline` renders the same list
		 * flush inside a page — no card chrome and no inner scroll — so it flows
		 * with the page (used by the trending menu on mobile).
		 */
		variant?: 'card' | 'inline';
	}

	let { variant = 'card' }: Props = $props();

	const { t } = useTranslation();

	let isCard = $derived(variant === 'card');
	// The sidebar card is denser than the in-page list.
	let rowPadX = $derived(isCard ? 'px-4' : 'px-5 sm:px-6');
	let rowPadY = $derived(isCard ? 'py-2.5' : 'py-3');
	let tagSize = $derived(isCard ? 'text-[14px]' : 'text-[15px]');
	let nickSize = $derived(isCard ? 'text-[12px]' : 'text-[13px]');

	// Cached in the store, so navigating between Page48 pages doesn't refetch.
	let accounts = $derived(memberXTagsStore.data);
	let loading = $derived(memberXTagsStore.isLoading || !memberXTagsStore.isLoaded);
	// Keep the active media filter (Gambar/Video) when opening a tag.
	let activeMedia = $derived(getActiveMedia($page.url.pathname, $page.url.search));

	onMount(() => {
		void memberXTagsStore.load();
	});

	function tagHref(username: string): string {
		return tagUrl(username, activeMedia);
	}
</script>

<section
	class={isCard
		? 'flex flex-col max-h-[calc(100vh-6rem)] rounded-2xl bg-white/80 dark:bg-zinc-900/80 border border-gray-200/70 dark:border-white/10 backdrop-blur-xl overflow-hidden'
		: ''}
>
	{#if isCard}
		<div
			class="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-white/5 shrink-0"
		>
			<Hash size={16} class="text-red-500" />
			<h2 class="font-bold text-[15px] text-gray-900 dark:text-gray-100">
				{t('page48.members.title')}
			</h2>
		</div>
	{:else}
		<!-- Same heading as the standalone members page this replaced. -->
		<div class="px-5 sm:px-6 pt-5 pb-4 border-b border-gray-100/60 dark:border-white/5">
			<div class="flex items-center gap-2">
				<Hash size={22} class="text-red-500" />
				<h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">
					{t('page48.members.title')}
				</h2>
			</div>
			<p class="text-[13px] text-gray-500 dark:text-gray-400 mt-1">
				{t('page48.members.subtitle')}
			</p>
		</div>
	{/if}

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
		<div
			class={`text-center text-[13px] text-gray-400 dark:text-gray-500 ${isCard ? 'p-5' : 'p-12'}`}
		>
			{t('page48.members.empty')}
		</div>
	{:else}
		<ul
			class={`divide-y divide-gray-100 dark:divide-white/5 ${
				isCard ? 'flex-1 min-h-0 overflow-y-auto scroll-hover' : ''
			}`}
		>
			{#each accounts as account (account.memberId)}
				<li class="flex items-center hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
					<a
						href={tagHref(account.username)}
						class={`flex-1 min-w-0 flex items-center gap-2 cursor-pointer ${rowPadX} ${rowPadY}`}
						title={account.name}
					>
						<span class={`truncate font-semibold text-red-500 ${tagSize}`}>
							#{account.username}
						</span>
						{#if account.nickname}
							<span class={`truncate text-gray-400 dark:text-gray-500 ${nickSize}`}>
								{account.nickname}
							</span>
						{/if}
					</a>
					<a
						href={account.url}
						target="_blank"
						rel="noopener noreferrer"
						class={`text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors cursor-pointer ${
							isCard ? 'px-3 py-2.5' : 'px-4 py-3'
						}`}
						aria-label={t('page48.aria.openX', { username: account.username })}
						title={t('page48.aria.openX', { username: account.username })}
					>
						<ExternalLink size={isCard ? 14 : 16} />
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
