<script lang="ts">
	import type { Snippet } from 'svelte';
	import { fade } from 'svelte/transition';
	import { CircleAlert, UserRoundX } from 'lucide-svelte';
	import { portal } from '$lib/actions/portal';
	import type { Page48UserProfile } from '$lib/api/page48';
	import FollowButton from '$lib/components/page48/FollowButton.svelte';
	import { page48HoverProfileStore } from '$lib/stores/page48.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		username: string;
		href: string;
		/** Classes for the trigger link, which is rendered by this component. */
		class?: string;
		children: Snippet;
	}

	let { username, href, class: className = '', children }: Props = $props();

	const { t } = useTranslation();

	// The pointer has to come to rest on the handle before the card opens: entering
	// starts the countdown and every move restarts it, so sweeping the pointer across a
	// name never opens it — only a deliberate pause does. (Browsers do not synthesise
	// hover events when content scrolls under a still pointer, so scrolling is safe.)
	// The close delay leaves time to cross the gap onto the card itself.
	const REST_MS = 500;
	const CLOSE_DELAY_MS = 150;
	const CARD_WIDTH = 300;
	const CARD_HEIGHT = 232;
	const GAP = 8;

	let trigger = $state<HTMLAnchorElement>();
	let visible = $state(false);
	let profile = $state<Page48UserProfile | null>(null);
	/** The handle has no account (deleted, renamed, or never existed). */
	let missing = $state(false);
	/** The lookup itself failed, so the next hover retries it. */
	let failed = $state(false);
	let position = $state({ left: GAP, top: GAP });

	let openTimer: ReturnType<typeof setTimeout> | null = null;
	let closeTimer: ReturnType<typeof setTimeout> | null = null;

	function clearTimers() {
		if (openTimer) clearTimeout(openTimer);
		if (closeTimer) clearTimeout(closeTimer);
		openTimer = null;
		closeTimer = null;
	}

	function scheduleOpen() {
		clearTimers();
		if (visible) return;
		openTimer = setTimeout(() => (visible = true), REST_MS);
	}

	function scheduleClose() {
		clearTimers();
		if (!visible) return;
		closeTimer = setTimeout(() => {
			visible = false;
			// Drop the outcome so the next hover looks it up again. A cached profile
			// comes straight back, while a failure gets a fresh attempt.
			profile = null;
			missing = false;
			failed = false;
		}, CLOSE_DELAY_MS);
	}

	function cancelClose() {
		if (closeTimer) clearTimeout(closeTimer);
		closeTimer = null;
	}

	function place() {
		if (!trigger) return;
		const rect = trigger.getBoundingClientRect();
		const left = Math.max(GAP, Math.min(rect.left, window.innerWidth - CARD_WIDTH - GAP));
		// Sits under the handle, lifted when there is no room below it.
		const top = Math.min(rect.bottom + GAP, window.innerHeight - CARD_HEIGHT - GAP);
		position = { left, top: Math.max(GAP, top) };
	}

	$effect(() => {
		if (!visible || profile || missing || failed) return;
		place();

		let cancelled = false;
		void page48HoverProfileStore.get(username).then((result) => {
			if (cancelled) return;
			if (result.status === 'ok') profile = result.profile;
			else if (result.status === 'missing') missing = true;
			else failed = true;
		});
		return () => {
			cancelled = true;
		};
	});

	function avatarUrl(data: Page48UserProfile): string {
		if (data.profilePicture_small || data.profilePicture) {
			return (data.profilePicture_small || data.profilePicture) as string;
		}
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(data.name || data.username)}&background=fca5a5&color=fff`;
	}

	/** Keep the follower count in step while the card stays open. */
	function handleFollowChange(following: boolean, pending: boolean) {
		if (!profile) return;
		const wasFollowing = profile.isFollowing;
		profile = {
			...profile,
			isFollowing: following,
			isFollowPending: pending,
			followerCount: Math.max(
				0,
				profile.followerCount +
					(following && !wasFollowing ? 1 : !following && wasFollowing ? -1 : 0)
			)
		};
	}
</script>

<a
	bind:this={trigger}
	{href}
	class={className}
	onmousemove={scheduleOpen}
	onmouseenter={scheduleOpen}
	onmouseleave={scheduleClose}
>
	{@render children()}
</a>

{#if visible}
	<!-- Above the page (and the media viewer at z-10010) but below the popover menus,
	     so a 3-dot menu opened on top of it is never covered. -->
	<div
		use:portal
		class="fixed z-[10020] rounded-2xl border border-gray-200 bg-white p-3 shadow-xl dark:border-zinc-800 dark:bg-zinc-900"
		style={`left:${position.left}px; top:${position.top}px; width:${CARD_WIDTH}px;`}
		role="dialog"
		tabindex="-1"
		aria-label={t('page48.aria.userPreview')}
		onmouseenter={cancelClose}
		onmouseleave={scheduleClose}
		transition:fade={{ duration: 100 }}
	>
		{#if profile}
			<div class="flex items-start gap-3">
				<div class="h-11 w-11 shrink-0 overflow-hidden rounded-full bg-gray-100 dark:bg-zinc-800">
					<img src={avatarUrl(profile)} alt="" class="h-full w-full object-cover" />
				</div>
				<a {href} class="min-w-0 flex-1">
					<span class="block truncate text-[15px] font-bold text-gray-900 dark:text-gray-100">
						{profile.name}
					</span>
					<span class="block truncate text-[13px] text-gray-500 dark:text-gray-400">
						@{profile.username}
					</span>
				</a>
				<FollowButton
					username={profile.username}
					isFollowing={profile.isFollowing}
					isPending={profile.isFollowPending}
					onChange={handleFollowChange}
				/>
			</div>

			{#if profile.bio}
				<p
					class="mt-2 line-clamp-3 text-[13px] whitespace-pre-wrap break-words text-gray-700 dark:text-gray-300"
				>
					{profile.bio}
				</p>
			{/if}

			<div class="mt-2 flex items-center gap-3 text-[13px] text-gray-500 dark:text-gray-400">
				<span>
					<span class="font-semibold text-gray-900 dark:text-gray-100">
						{profile.followerCount}
					</span>
					{t('page48.userPage.followers')}
				</span>
				<span>
					<span class="font-semibold text-gray-900 dark:text-gray-100">
						{profile.followingCount}
					</span>
					{t('page48.userPage.following')}
				</span>
			</div>
		{:else if missing || failed}
			<div class="flex items-start gap-3">
				<div
					class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gray-100 text-gray-400 dark:bg-zinc-800 dark:text-zinc-500"
				>
					{#if missing}
						<UserRoundX size={20} />
					{:else}
						<CircleAlert size={20} />
					{/if}
				</div>
				<div class="min-w-0 flex-1">
					<p class="truncate text-[14px] font-bold text-gray-900 dark:text-gray-100">
						@{username}
					</p>
					<p class="mt-0.5 text-[12px] text-gray-500 dark:text-gray-400">
						{missing ? t('page48.hover.notFoundText') : t('page48.hover.loadError')}
					</p>
				</div>
			</div>
		{:else}
			<div class="animate-pulse">
				<div class="flex items-start gap-3">
					<div class="h-11 w-11 shrink-0 rounded-full bg-gray-200/80 dark:bg-zinc-800"></div>
					<div class="flex-1 space-y-2 pt-0.5">
						<div class="h-4 w-32 rounded bg-gray-200 dark:bg-zinc-800"></div>
						<div class="h-3.5 w-20 rounded bg-gray-200 dark:bg-zinc-800"></div>
					</div>
				</div>
				<div class="mt-2 space-y-2">
					<div class="h-3.5 w-full rounded bg-gray-200 dark:bg-zinc-800"></div>
					<div class="h-3.5 w-2/3 rounded bg-gray-200 dark:bg-zinc-800"></div>
				</div>
			</div>
		{/if}
	</div>
{/if}
