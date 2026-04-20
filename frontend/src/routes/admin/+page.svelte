<script lang="ts">
	import { adminStore, isAdminUsersLoading } from '$lib/stores/admin.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import TableSkeleton from '$lib/components/skeletons/TableSkeleton.svelte';
	import { Search, X, UserCheck, ShieldCheck, Mail, Lock, Eye, EyeOff } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { OptimizedImage } from '$lib/components/common';
	import { formatDate } from '$lib/i18n';

	const { t } = useTranslation();

	// Store state
	let usersList = $derived(adminStore.users.data);
	let usersHasMore = $derived(adminStore.users.hasMore);

	// Search state
	let searchQuery = $state('');
	let searchTimeout: ReturnType<typeof setTimeout>;

	// Initial load state
	let isInitialLoad = $state(true);

	$effect(() => {
		// Only load if data is not already cached
		if (usersList.length === 0) {
			adminStore.loadUsers();
		} else {
			isInitialLoad = false;
		}

		if (usersList.length > 0) {
			isInitialLoad = false;
		}

		return () => {
			if (searchTimeout) clearTimeout(searchTimeout);
		};
	});

	function handleSearch() {
		if (searchTimeout) clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			adminStore.setUserSearch(searchQuery);
		}, 300);
	}

	function clearSearch() {
		searchQuery = '';
		handleSearch();
	}

	function loadMoreUsers() {
		if (usersHasMore && !isAdminUsersLoading.value) {
			adminStore.loadUsers();
		}
	}

	function maskEmail(email: string) {
		const [local, domain] = email.split('@');
		if (!local || !domain) return email;
		if (local.length <= 2) return `${local.slice(0, 1)}***@${domain}`;
		return `${local.slice(0, 2)}***@${domain}`;
	}

	let revealedEmails = $state(new Set<string>());

	function toggleEmail(userId: string) {
		if (revealedEmails.has(userId)) {
			revealedEmails.delete(userId);
		} else {
			revealedEmails.add(userId);
		}
		revealedEmails = revealedEmails;
	}
</script>

<div>
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 bg-white dark:bg-zinc-800 p-4 rounded-3xl shadow-sm"
	>
		<div class="flex flex-col sm:flex-row sm:items-center gap-4 flex-1">
			<h2 class="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2 min-w-fit">
				<UserCheck class="w-5 h-5 text-red-500" />
				{t('admin.users.title')} ({adminStore.users.total})
			</h2>

			<!-- Search Input -->
			<div class="relative w-full sm:max-w-xs">
				<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
				<input
					type="text"
					bind:value={searchQuery}
					oninput={handleSearch}
					placeholder={t('admin.users.searchPlaceholder')}
					class="w-full pl-9 pr-8 py-2 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all"
				/>
				{#if searchQuery}
					<button
						onclick={clearSearch}
						class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 cursor-pointer"
					>
						<X class="w-3 h-3" />
					</button>
				{/if}
			</div>
		</div>
	</div>

	{#if isInitialLoad && isAdminUsersLoading.value}
		<TableSkeleton
			rows={10}
			columns={[
				t('admin.users.table.userInfo'),
				t('admin.users.table.email'),
				t('admin.users.table.status'),
				t('admin.users.table.created')
			]}
		/>
	{:else}
		<div class="glass-panel rounded-3xl overflow-hidden shadow-sm">
			<div class="overflow-x-auto">
				<table class="w-full text-left border-collapse">
					<thead>
						<tr
							class="bg-gray-50/80 dark:bg-zinc-800/80 border-b border-gray-200 dark:border-zinc-700 text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 font-bold"
						>
							<th class="p-4">{t('admin.users.table.userInfo')}</th>
							<th class="p-4">{t('admin.users.table.email')}</th>
							<th class="p-4">{t('admin.users.table.status')}</th>
							<th class="p-4">{t('admin.users.table.created')}</th>
						</tr>
					</thead>
					<tbody
						class="bg-white/50 dark:bg-zinc-900/50 divide-y divide-gray-100 dark:divide-zinc-700"
					>
						{#each usersList as user}
							<tr class="hover:bg-gray-50/50 dark:hover:bg-zinc-800/50 transition-colors">
								<td class="p-4">
									<div class="flex items-center gap-3">
										{#if user.profilePicture}
											<OptimizedImage
												src={user.profilePicture || ''}
												srcMedium={user.profilePicture_medium}
												srcSmall={user.profilePicture_small}
												alt={user.name || ''}
												sizes="40px"
												class="w-10 h-10 rounded-full object-cover"
											/>
										{:else}
											<div
												class="w-10 h-10 rounded-full bg-gradient-to-br from-red-400 to-pink-500 flex items-center justify-center text-white font-bold"
											>
												{user.name.charAt(0).toUpperCase()}
											</div>
										{/if}
										<div>
											<div
												class="font-semibold text-gray-900 dark:text-white flex items-center gap-2"
											>
												{user.name}
												{#if user.isAdmin}
													<ShieldCheck class="w-4 h-4 text-red-500" />
												{/if}
											</div>
											<div class="text-sm text-gray-500 dark:text-gray-400">@{user.username}</div>
										</div>
									</div>
								</td>
								<td class="p-4">
									<div class="flex items-center gap-2">
										<span class="text-gray-700 dark:text-gray-300 font-mono text-sm">
											{revealedEmails.has(user.userId) ? user.email : maskEmail(user.email)}
										</span>
										<button
											class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 focus:outline-none transition-colors cursor-pointer"
											onclick={() => toggleEmail(user.userId)}
											title={revealedEmails.has(user.userId) ? 'Hide email' : 'Show email'}
										>
											{#if revealedEmails.has(user.userId)}
												<EyeOff class="w-4 h-4" />
											{:else}
												<Eye class="w-4 h-4" />
											{/if}
										</button>
									</div>
								</td>
								<td class="p-4">
									<div class="flex items-center gap-2">
										{#if user.isEmailVerified}
											<span
												class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
											>
												<Mail class="w-3 h-3" />
												{t('admin.users.status.verified')}
											</span>
										{:else}
											<span
												class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
											>
												<Mail class="w-3 h-3" />
												{t('admin.users.status.unverified')}
											</span>
										{/if}
										{#if user.isAccountLocked}
											<span
												class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
											>
												<Lock class="w-3 h-3" />
												{t('admin.users.status.locked')}
											</span>
										{/if}
									</div>
								</td>
								<td class="p-4">
									<span class="text-gray-600 dark:text-gray-400 text-sm"
										>{formatDate(user.createdAt, {
											year: 'numeric',
											month: 'short',
											day: 'numeric'
										})}</span
									>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>

		<!-- Infinite Scroll Sentinel -->
		{#if usersHasMore}
			<div class="mt-4" use:infiniteScroll onintersect={loadMoreUsers}>
				{#if isAdminUsersLoading.value}
					<TableSkeleton
						rows={3}
						columns={[
							t('admin.users.table.userInfo'),
							t('admin.users.table.email'),
							t('admin.users.table.status'),
							t('admin.users.table.created')
						]}
						showHeader={false}
					/>
				{/if}
			</div>
		{:else if usersList.length > 0}
			<div class="py-12 text-center text-gray-400 text-sm">
				{t('admin.users.noMoreUsers')}
			</div>
		{:else}
			<div class="py-20 text-center text-gray-500">
				{t('admin.users.noUsersFound', { query: searchQuery })}
			</div>
		{/if}
	{/if}
</div>
