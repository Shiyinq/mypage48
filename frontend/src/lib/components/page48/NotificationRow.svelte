<script lang="ts">
	import type { Page48Notification } from '$lib/api/page48';
	import { page48Api } from '$lib/api/page48';
	import UserHoverCard from '$lib/components/page48/UserHoverCard.svelte';
	import {
		NOTIFICATION_ACTION_KEYS,
		NOTIFICATION_ICONS
	} from '$lib/components/page48/notificationMeta';
	import { showToast } from '$lib/stores/toast.svelte';
	import { formatPostTime, userUrl } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		notification: Page48Notification;
		/** Asked to drop the row once a follow request has been handled. */
		onResolved?: (notificationId: string) => void;
	}

	let { notification, onResolved }: Props = $props();

	const { t } = useTranslation();

	let busy = $state(false);

	let avatar = $derived(
		notification.actor.profilePicture_small ||
			notification.actor.profilePicture ||
			`https://ui-avatars.com/api/?name=${encodeURIComponent(
				notification.actor.name || notification.actor.username
			)}&background=fca5a5&color=fff`
	);

	let action = $derived(NOTIFICATION_ACTION_KEYS[notification.type]);
	let Icon = $derived(NOTIFICATION_ICONS[notification.type]);
	// A follow (request) and any deleted post have no post to open.
	let href = $derived(
		notification.type === 'follow' || notification.type === 'followRequest' || !notification.post
			? userUrl(notification.actor.username)
			: `/page48/post/${notification.post.postId}`
	);

	let snippet = $derived(notification.post?.content?.trim() ?? '');
	let isFollowRequest = $derived(notification.type === 'followRequest');

	async function respond(accept: boolean) {
		if (busy) return;
		busy = true;
		try {
			if (accept) {
				await page48Api.acceptFollowRequest(notification.actor.username);
			} else {
				await page48Api.declineFollowRequest(notification.actor.username);
			}
			showToast(t(accept ? 'page48.follow.accepted' : 'page48.follow.declined'), 'success');
			onResolved?.(notification.notificationId);
		} catch (err: unknown) {
			const e = err as { detail?: string; message?: string };
			showToast(e?.detail || e?.message || t('page48.follow.error'), 'error');
		} finally {
			busy = false;
		}
	}
</script>

<!-- Only the pieces that must be links are raised above the row link; everything
     else falls through to it, so no anchor ends up nested inside another. -->
<div
	class={`relative isolate flex gap-3 px-5 py-3.5 transition-colors hover:bg-gray-50 dark:hover:bg-white/5 sm:px-6 ${
		notification.isUnread ? 'bg-red-50/40 dark:bg-red-950/10' : ''
	}`}
>
	<a {href} class="absolute inset-0 z-0" aria-label={t(action)}></a>

	<div class="relative z-[1] shrink-0 pointer-events-auto">
		<UserHoverCard
			username={notification.actor.username}
			href={userUrl(notification.actor.username)}
		>
			<img
				src={avatar}
				alt={notification.actor.username}
				class="h-10 w-10 rounded-full bg-gray-100 object-cover dark:bg-zinc-800"
				loading="lazy"
			/>
		</UserHoverCard>
		<span
			class="pointer-events-none absolute -bottom-0.5 -right-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-white dark:bg-zinc-950"
		>
			<Icon size={13} class="text-red-500" />
		</span>
	</div>

	<div class="pointer-events-none relative z-[1] min-w-0 flex-1">
		<div class="flex items-center gap-1.5 text-[14px]">
			<UserHoverCard
				username={notification.actor.username}
				href={userUrl(notification.actor.username)}
				class="pointer-events-auto min-w-0 truncate font-semibold text-gray-900 hover:underline dark:text-gray-100"
			>
				{notification.actor.name}
			</UserHoverCard>
			<span class="truncate text-[13px] text-gray-500 dark:text-gray-400"
				>@{notification.actor.username}</span
			>
			<span class="shrink-0 text-gray-400">·</span>
			<span class="shrink-0 text-[12px] text-gray-500 dark:text-gray-400"
				>{formatPostTime(notification.createdAt)}</span
			>
			{#if notification.isUnread}
				<span class="ml-auto h-2 w-2 shrink-0 rounded-full bg-red-500" aria-hidden="true"></span>
			{/if}
		</div>

		<p class="mt-0.5 text-[14px] text-gray-600 dark:text-gray-300">{t(action)}</p>

		<!-- The post sits in its own boxed snippet so it cannot be mistaken for a
		     continuation of the action line above it. -->
		{#if snippet}
			<div
				class="mt-1.5 line-clamp-2 rounded-xl border border-gray-100 bg-gray-50/70 px-2.5 py-1.5 text-[13px] text-gray-500 dark:border-white/10 dark:bg-white/5 dark:text-gray-400"
			>
				{snippet}
			</div>
		{:else if !notification.post && !isFollowRequest && notification.type !== 'follow'}
			<p class="mt-1.5 text-[13px] italic text-gray-400 dark:text-gray-500">
				{t('page48.notifications.postUnavailable')}
			</p>
		{/if}

		{#if isFollowRequest}
			<div class="pointer-events-auto mt-2 flex gap-2">
				<button
					type="button"
					onclick={() => respond(true)}
					disabled={busy}
					class="rounded-full bg-red-600 px-4 py-1.5 text-[13px] font-semibold text-white transition-colors hover:bg-red-700 disabled:opacity-50 cursor-pointer"
				>
					{t('page48.follow.accept')}
				</button>
				<button
					type="button"
					onclick={() => respond(false)}
					disabled={busy}
					class="rounded-full border border-gray-200 px-4 py-1.5 text-[13px] font-semibold text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50 dark:border-zinc-700 dark:text-gray-200 dark:hover:bg-zinc-800 cursor-pointer"
				>
					{t('page48.follow.decline')}
				</button>
			</div>
		{/if}
	</div>
</div>
