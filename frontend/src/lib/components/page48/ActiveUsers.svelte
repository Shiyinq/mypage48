<script lang="ts">
	import { onMount } from 'svelte';
	import { Users } from 'lucide-svelte';
	import { activeUsersStore } from '$lib/stores/page48.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	// Cached in the store, so navigating between Page48 pages doesn't refetch.
	let users = $derived(activeUsersStore.data);
	let loading = $derived(activeUsersStore.isLoading || !activeUsersStore.isLoaded);

	onMount(() => {
		void activeUsersStore.load();
	});

	function avatar(u: { profilePicture: string | null; username: string; name: string }): string {
		if (u.profilePicture) return u.profilePicture;
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(u.name || u.username)}&background=fca5a5&color=fff`;
	}
</script>

<section
	class="rounded-2xl bg-white/80 dark:bg-zinc-900/80 border border-gray-200/70 dark:border-white/10 backdrop-blur-xl overflow-hidden"
>
	<div class="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-white/5">
		<Users size={16} class="text-red-500" />
		<h2 class="font-bold text-[15px] text-gray-900 dark:text-gray-100">
			{t('page48.activeUsers.title')}
		</h2>
	</div>

	{#if loading}
		<div class="p-4 space-y-3 animate-pulse">
			{#each Array(5) as _}
				<div class="flex items-center gap-3">
					<div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-800 shrink-0"></div>
					<div class="flex-1 space-y-1.5">
						<div class="h-3.5 bg-gray-200 dark:bg-zinc-800 rounded w-1/2"></div>
						<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-1/3"></div>
					</div>
				</div>
			{/each}
		</div>
	{:else if users.length === 0}
		<div class="p-5 text-center text-[13px] text-gray-400 dark:text-gray-500">
			{t('page48.activeUsers.empty')}
		</div>
	{:else}
		<ul class="divide-y divide-gray-100 dark:divide-white/5">
			{#each users as user (user.userId)}
				<li>
					<a
						href={`/page48/u/${user.username}`}
						class="flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
					>
						<div class="w-8 h-8 rounded-full overflow-hidden bg-gray-100 dark:bg-zinc-800 shrink-0">
							<img src={avatar(user)} alt={user.username} class="w-full h-full object-cover" />
						</div>
						<div class="flex-1 min-w-0">
							<p class="font-semibold text-[14px] text-gray-900 dark:text-gray-100 truncate">
								{user.name}
							</p>
							<p class="text-[12px] text-gray-400 dark:text-gray-500 truncate">
								@{user.username}
							</p>
						</div>
						<span class="text-[11px] font-semibold text-red-500 shrink-0 tabular-nums">
							{t('page48.activeUsers.postCount', { count: user.postCount })}
						</span>
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</section>
