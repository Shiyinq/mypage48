<script lang="ts">
	import { Video as VideoIcon, X } from 'lucide-svelte';
	import type { Page48Post } from '$lib/api/page48';
	import { formatTimeAgo } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** The quoted post. `null` with `unavailable` set means it was deleted. */
		post: Page48Post | null;
		/** The original is gone: show a placeholder instead of the preview. */
		unavailable?: boolean;
		/** Show a remove button (used inside the composer). */
		removable?: boolean;
		onRemove?: () => void;
	}

	let { post, unavailable = false, removable = false, onRemove }: Props = $props();

	const { t } = useTranslation();

	let thumbnail = $derived(post ? (post.images?.[0]?.url_small ?? post.images?.[0]?.url) : null);

	function avatarUrl(user: Page48Post): string {
		if (user.userProfilePicture_small || user.userProfilePicture) {
			return (user.userProfilePicture_small || user.userProfilePicture) as string;
		}
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(user.userDisplayName)}&background=fca5a5&color=fff`;
	}
</script>

<div
	class="relative mt-3 rounded-2xl border border-gray-200 bg-white overflow-hidden dark:border-zinc-700 dark:bg-zinc-900"
>
	{#if removable}
		<button
			type="button"
			class="absolute right-1.5 top-1.5 z-[2] p-1.5 rounded-full text-gray-400 hover:text-gray-900 hover:bg-gray-100 dark:hover:text-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
			onclick={(e) => {
				e.stopPropagation();
				onRemove?.();
			}}
			aria-label={t('page48.aria.removeQuote')}
		>
			<X size={15} />
		</button>
	{/if}

	{#if unavailable || !post}
		<p class="px-3 py-3 text-[13px] text-gray-500 dark:text-gray-400">
			{t('page48.post.quotedUnavailable')}
		</p>
	{:else}
		<a
			href={`/page48/post/${post.postId}`}
			class="block p-3 hover:bg-black/[0.02] dark:hover:bg-white/[0.03]"
		>
			<div class="flex items-center gap-1.5 text-[13px]">
				<img
					src={avatarUrl(post)}
					alt={post.username}
					class="w-5 h-5 rounded-full object-cover bg-gray-100 dark:bg-zinc-800 shrink-0"
					loading="lazy"
				/>
				<span class="truncate font-semibold text-gray-900 dark:text-gray-100">
					{post.userDisplayName}
				</span>
				<span class="truncate text-gray-500 dark:text-gray-400">@{post.username}</span>
				<span class="shrink-0 text-gray-400">·</span>
				<span class="shrink-0 text-gray-500 dark:text-gray-400">
					{formatTimeAgo(post.createdAt)}
				</span>
				{#if post.videos && post.videos.length > 0}
					<VideoIcon size={14} class="ml-auto shrink-0 text-gray-400" />
				{/if}
			</div>

			{#if post.content}
				<p
					class="mt-1 line-clamp-4 whitespace-pre-wrap break-words text-[14px] leading-relaxed text-gray-700 dark:text-gray-300"
				>
					{post.content}
				</p>
			{/if}

			{#if thumbnail}
				<img
					src={thumbnail}
					alt={t('page48.aria.media')}
					class="mt-2 max-h-[200px] w-full rounded-lg object-cover bg-gray-100 dark:bg-zinc-800"
					loading="lazy"
				/>
			{/if}
		</a>
	{/if}
</div>
