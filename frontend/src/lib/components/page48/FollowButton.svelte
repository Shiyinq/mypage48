<script lang="ts">
	import { untrack } from 'svelte';
	import { page48Api } from '$lib/api/page48';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { page48HoverProfileStore } from '$lib/stores/page48.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		username: string;
		isFollowing: boolean;
		/** The target is follower-only and the request has not been answered yet. */
		isPending?: boolean;
		/** `md` is the profile header size, `sm` fits inside user lists. */
		size?: 'sm' | 'md';
		/** Extra classes for the button (e.g. `w-full` for the mobile CTA). */
		class?: string;
		onChange?: (isFollowing: boolean, isPending: boolean) => void;
	}

	let {
		username,
		isFollowing = false,
		isPending = false,
		size = 'sm',
		class: className = '',
		onChange
	}: Props = $props();

	const { t } = useTranslation();

	// `untrack` because the props only seed the initial value; the $effect below
	// keeps them in sync afterwards.
	let following = $state(untrack(() => isFollowing));
	let pending = $state(untrack(() => isPending));
	let busy = $state(false);

	// Follow the parent's values when it reloads (the button owns them in between).
	$effect(() => {
		following = isFollowing;
		pending = isPending;
	});

	let isSelf = $derived(!!userProfile.data && userProfile.data.username === username);
	let canFollow = $derived(isAuthenticated.value && !isSelf);

	// Either state undoes the relationship: following unfollows, pending cancels.
	let canUndo = $derived(following || pending);

	async function toggle(e: MouseEvent) {
		e.preventDefault();
		e.stopPropagation();
		if (busy || !canFollow) return;
		busy = true;
		try {
			const res = canUndo
				? await page48Api.unfollowUser(username)
				: await page48Api.followUser(username);
			following = res.isFollowing;
			pending = res.isPending;
			// The hover card caches this profile, so its counts are now stale.
			page48HoverProfileStore.invalidate(username);
			onChange?.(res.isFollowing, res.isPending);
		} catch (err: unknown) {
			const e2 = err as { detail?: string; message?: string };
			showToast(e2?.detail || e2?.message || t('page48.follow.error'), 'error');
		} finally {
			busy = false;
		}
	}

	let label = $derived(
		pending
			? t('page48.follow.requested')
			: following
				? t('page48.follow.following')
				: t('page48.follow.follow')
	);
	let ariaLabel = $derived(
		canUndo
			? pending
				? t('page48.follow.cancelRequest')
				: t('page48.follow.unfollow')
			: t('page48.follow.follow')
	);
</script>

{#if canFollow}
	<button
		type="button"
		class={`shrink-0 rounded-full font-bold transition-colors cursor-pointer disabled:opacity-60 ${className} ${
			size === 'md' ? 'h-9 px-4 text-[13px]' : 'h-8 px-3 text-[12px]'
		} ${
			canUndo
				? 'border border-gray-300 text-gray-800 hover:border-red-300 hover:text-red-600 dark:border-zinc-700 dark:text-gray-200 dark:hover:border-red-900 dark:hover:text-red-400'
				: 'bg-red-600 text-white hover:bg-red-700'
		}`}
		onclick={toggle}
		disabled={busy}
		aria-label={ariaLabel}
	>
		{label}
	</button>
{/if}
