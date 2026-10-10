<script lang="ts">
	import type { PostUserItem } from '$lib/api/page48';
	import FollowButton from '$lib/components/page48/FollowButton.svelte';
	import AccountBadge from '$lib/components/page48/AccountBadge.svelte';

	interface Props {
		user: PostUserItem;
		/** Show a follow button on the right (hidden for your own row). */
		showFollow?: boolean;
	}

	let { user, showFollow = false }: Props = $props();

	function avatarUrl(u: PostUserItem): string {
		if (u.profilePicture_small || u.profilePicture) {
			return (u.profilePicture_small || u.profilePicture) as string;
		}
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(u.name || u.username)}&background=fca5a5&color=fff`;
	}
</script>

<div
	class="flex items-start gap-3 px-5 py-3 transition-colors hover:bg-black/[0.03] sm:px-6 dark:hover:bg-white/[0.03]"
>
	<a href={`/page48/u/${user.username}`} class="shrink-0">
		<img
			src={avatarUrl(user)}
			alt={user.username}
			class="h-11 w-11 rounded-full bg-gray-100 object-cover dark:bg-zinc-800"
			loading="lazy"
		/>
	</a>
	<div class="min-w-0 flex-1">
		<a href={`/page48/u/${user.username}`} class="group/name block">
			<div class="flex flex-wrap items-baseline gap-x-1.5">
				<span
					class="truncate text-[15px] font-semibold text-gray-900 group-hover/name:underline dark:text-gray-100"
				>
					{user.name}
				</span>
				<AccountBadge type={user.page48AccountType} size={15} />
				<span class="truncate text-[14px] text-gray-500 dark:text-gray-400">
					@{user.username}
				</span>
			</div>
		</a>
		{#if user.bio}
			<p class="mt-0.5 line-clamp-2 break-words text-[14px] text-gray-600 dark:text-gray-300">
				{user.bio}
			</p>
		{/if}
	</div>
	{#if showFollow}
		<FollowButton
			username={user.username}
			isFollowing={user.isFollowing ?? false}
			isPending={user.isPending ?? false}
		/>
	{/if}
</div>
