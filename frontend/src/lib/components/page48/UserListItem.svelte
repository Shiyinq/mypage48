<script lang="ts">
	import type { PostUserItem } from '$lib/api/page48';

	interface Props {
		user: PostUserItem;
	}

	let { user }: Props = $props();

	function avatarUrl(u: PostUserItem): string {
		if (u.profilePicture_small || u.profilePicture) {
			return (u.profilePicture_small || u.profilePicture) as string;
		}
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(u.name || u.username)}&background=fca5a5&color=fff`;
	}
</script>

<a
	href={`/page48/u/${user.username}`}
	class="flex items-start gap-3 px-5 sm:px-6 py-3 hover:bg-black/[0.03] dark:hover:bg-white/[0.03] transition-colors"
>
	<img
		src={avatarUrl(user)}
		alt={user.username}
		class="w-11 h-11 shrink-0 rounded-full object-cover bg-gray-100 dark:bg-zinc-800"
		loading="lazy"
	/>
	<div class="min-w-0 flex-1">
		<div class="flex flex-wrap items-baseline gap-x-1.5">
			<span class="truncate font-semibold text-[15px] text-gray-900 dark:text-gray-100">
				{user.name}
			</span>
			<span class="truncate text-[14px] text-gray-500 dark:text-gray-400">
				@{user.username}
			</span>
		</div>
		{#if user.bio}
			<p class="mt-0.5 line-clamp-2 break-words text-[14px] text-gray-600 dark:text-gray-300">
				{user.bio}
			</p>
		{/if}
	</div>
</a>
