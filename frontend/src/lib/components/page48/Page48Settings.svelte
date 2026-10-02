<script lang="ts">
	import { onMount } from 'svelte';
	import { portal } from '$lib/actions/portal';
	import { fade } from 'svelte/transition';
	import { Ban, Lock, LoaderCircle, VolumeX, X } from 'lucide-svelte';
	import { page48Api, type PostUserItem, type PostUserListResponse } from '$lib/api/page48';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** The profile these settings belong to (always the signed-in user). */
		username: string;
	}

	let { username }: Props = $props();

	const { t } = useTranslation();

	type Relation = 'block' | 'mute';

	interface ListState {
		users: PostUserItem[];
		loading: boolean;
		loadingMore: boolean;
		hasMore: boolean;
		nextCursor: string | null;
	}

	const PAGE_SIZE = 20;

	function emptyList(): ListState {
		return { users: [], loading: true, loadingMore: false, hasMore: false, nextCursor: null };
	}

	let locked = $state(false);
	let lockedLoading = $state(true);
	let lockedBusy = $state(false);

	let lists = $state<Record<Relation, ListState>>({
		block: emptyList(),
		mute: emptyList()
	});
	let busyId = $state<string | null>(null);
	/** Which relation's list modal is open, if any. */
	let openList = $state<Relation | null>(null);

	function fetchPage(relation: Relation, cursor: string | null): Promise<PostUserListResponse> {
		return relation === 'block'
			? page48Api.getBlocks(PAGE_SIZE, cursor)
			: page48Api.getMutes(PAGE_SIZE, cursor);
	}

	// Loaded once on mount; never from an effect, which would re-run forever
	// because these loaders reassign `lists`.
	onMount(() => {
		void loadLocked();
		void loadList('block');
		void loadList('mute');
	});

	async function loadLocked() {
		try {
			const profile = await page48Api.getUserProfile(username);
			locked = profile.isLocked;
		} catch {
			// Leave the switch off; toggling it again will retry.
		} finally {
			lockedLoading = false;
		}
	}

	async function toggleLock() {
		if (lockedBusy || lockedLoading) return;
		lockedBusy = true;
		try {
			const res = await page48Api.updateSettings(!locked);
			locked = res.locked;
			showToast(
				t(res.locked ? 'page48.settings.lockedOn' : 'page48.settings.lockedOff'),
				'success'
			);
		} catch (err: unknown) {
			const e = err as { detail?: string; message?: string };
			showToast(e?.detail || e?.message || t('common.error'), 'error');
		} finally {
			lockedBusy = false;
		}
	}

	async function loadList(relation: Relation) {
		try {
			const res = await fetchPage(relation, null);
			lists[relation] = {
				users: res.data,
				loading: false,
				loadingMore: false,
				hasMore: res.meta.hasMore,
				nextCursor: res.meta.nextCursor
			};
		} catch {
			lists[relation] = { ...emptyList(), loading: false };
		}
	}

	async function loadMore(relation: Relation) {
		const state = lists[relation];
		if (state.loadingMore || !state.hasMore || !state.nextCursor) return;
		state.loadingMore = true;
		try {
			const res = await fetchPage(relation, state.nextCursor);
			state.users = [...state.users, ...res.data];
			state.hasMore = res.meta.hasMore;
			state.nextCursor = res.meta.nextCursor;
		} catch (err) {
			console.error(err);
		} finally {
			state.loadingMore = false;
		}
	}

	async function release(relation: Relation, user: PostUserItem) {
		if (busyId) return;
		busyId = user.userId;
		try {
			if (relation === 'block') {
				await page48Api.unblockUser(user.username);
			} else {
				await page48Api.unmuteUser(user.username);
			}
			const state = lists[relation];
			state.users = state.users.filter((u) => u.userId !== user.userId);
			showToast(
				t(relation === 'block' ? 'page48.unblock.success' : 'page48.unmute.success'),
				'success'
			);
		} catch (err: unknown) {
			const e = err as { detail?: string; message?: string };
			showToast(e?.detail || e?.message || t('common.error'), 'error');
		} finally {
			busyId = null;
		}
	}

	function avatarUrl(user: PostUserItem): string {
		if (user.profilePicture_small || user.profilePicture) {
			return (user.profilePicture_small || user.profilePicture) as string;
		}
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name || user.username)}&background=fca5a5&color=fff`;
	}

	function listTitle(relation: Relation): string {
		return relation === 'block'
			? t('page48.relations.blocks.title')
			: t('page48.relations.mutes.title');
	}

	function listEmpty(relation: Relation): string {
		return relation === 'block'
			? t('page48.relations.blocks.empty')
			: t('page48.relations.mutes.empty');
	}

	function listAction(relation: Relation): string {
		return relation === 'block' ? t('page48.unblockUser') : t('page48.unmuteUser');
	}
</script>

<div class="glass-panel p-6 rounded-3xl">
	<div class="flex items-center gap-3 mb-4">
		<div
			class="w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/20 flex items-center justify-center shadow-sm"
		>
			<Lock class="w-5 h-5 text-red-600 dark:text-red-400" />
		</div>
		<div>
			<h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">
				{t('page48.settings.title')}
			</h3>
			<p class="text-xs text-gray-500 dark:text-gray-400">{t('page48.settings.subtitle')}</p>
		</div>
	</div>

	<div class="flex flex-col divide-y divide-gray-100 dark:divide-zinc-800">
		<!-- Follower-only lock -->
		<div class="flex items-start gap-3 py-3.5">
			<Lock class="mt-0.5 w-5 h-5 shrink-0 text-gray-500 dark:text-gray-400" />
			<div class="min-w-0 flex-1">
				<p class="text-[15px] font-semibold text-gray-900 dark:text-gray-100">
					{t('page48.settings.lockedTitle')}
				</p>
				<p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
					{t('page48.settings.lockedSubtitle')}
				</p>
			</div>
			{#if lockedLoading || lockedBusy}
				<LoaderCircle class="mt-1 w-5 h-5 shrink-0 animate-spin text-gray-400" />
			{:else}
				<button
					type="button"
					role="switch"
					aria-checked={locked}
					aria-label={t('page48.settings.lockedTitle')}
					onclick={toggleLock}
					class={`relative mt-1 h-6 w-11 shrink-0 rounded-full transition-colors cursor-pointer ${
						locked ? 'bg-red-600' : 'bg-gray-300 dark:bg-zinc-700'
					}`}
				>
					<span
						class={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
							locked ? 'left-[22px]' : 'left-0.5'
						}`}
					></span>
				</button>
			{/if}
		</div>

		<!-- Blocked accounts -->
		<div class="flex items-center gap-3 py-3.5">
			<Ban class="w-5 h-5 shrink-0 text-gray-500 dark:text-gray-400" />
			<div class="min-w-0 flex-1">
				<p class="text-[15px] font-semibold text-gray-900 dark:text-gray-100">
					{t('page48.relations.blocks.title')}
				</p>
				<p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
					{lists.block.loading ? t('common.loading') : lists.block.users.length}
				</p>
			</div>
			<button
				type="button"
				onclick={() => (openList = 'block')}
				class="shrink-0 rounded-full border border-gray-200 px-4 py-1.5 text-[13px] font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-zinc-700 dark:text-gray-200 dark:hover:bg-zinc-800 cursor-pointer"
			>
				{t('page48.settings.viewList')}
			</button>
		</div>

		<!-- Muted accounts -->
		<div class="flex items-center gap-3 py-3.5">
			<VolumeX class="w-5 h-5 shrink-0 text-gray-500 dark:text-gray-400" />
			<div class="min-w-0 flex-1">
				<p class="text-[15px] font-semibold text-gray-900 dark:text-gray-100">
					{t('page48.relations.mutes.title')}
				</p>
				<p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
					{lists.mute.loading ? t('common.loading') : lists.mute.users.length}
				</p>
			</div>
			<button
				type="button"
				onclick={() => (openList = 'mute')}
				class="shrink-0 rounded-full border border-gray-200 px-4 py-1.5 text-[13px] font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-zinc-700 dark:text-gray-200 dark:hover:bg-zinc-800 cursor-pointer"
			>
				{t('page48.settings.viewList')}
			</button>
		</div>
	</div>
</div>

{#if openList}
	{@const relation = openList}
	{@const state = lists[relation]}
	<div
		use:portal
		class="fixed inset-0 z-[10060] flex items-end justify-center sm:items-center sm:p-4"
		transition:fade={{ duration: 150 }}
		role="dialog"
		aria-modal="true"
	>
		<div
			class="absolute inset-0 bg-black/60 backdrop-blur-sm"
			onclick={() => (openList = null)}
			role="presentation"
		></div>

		<div
			class="relative flex max-h-[80vh] w-full flex-col rounded-t-2xl border border-gray-200 bg-white shadow-2xl sm:max-w-md sm:rounded-2xl dark:border-zinc-800 dark:bg-zinc-900"
		>
			<div
				class="flex items-center justify-between border-b border-gray-100 px-5 py-4 dark:border-zinc-800"
			>
				<h3 class="text-[16px] font-bold text-gray-900 dark:text-gray-100">
					{listTitle(relation)}
				</h3>
				<button
					type="button"
					onclick={() => (openList = null)}
					aria-label={t('common.close')}
					class="rounded-full p-1.5 text-gray-500 transition-colors hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-zinc-800 cursor-pointer"
				>
					<X size={18} />
				</button>
			</div>

			<div class="min-h-0 flex-1 overflow-y-auto px-5 py-2">
				{#if state.loading}
					<div class="flex justify-center py-8">
						<LoaderCircle class="w-5 h-5 animate-spin text-gray-400" />
					</div>
				{:else if state.users.length === 0}
					<p class="py-8 text-center text-[13px] font-medium text-gray-400 dark:text-gray-500">
						{listEmpty(relation)}
					</p>
				{:else}
					<div class="flex flex-col divide-y divide-gray-100 dark:divide-zinc-800">
						{#each state.users as user (user.userId)}
							<div class="flex items-center gap-3 py-3">
								<a href={`/page48/u/${user.username}`} class="shrink-0">
									<img
										src={avatarUrl(user)}
										alt={user.username}
										class="h-10 w-10 rounded-full bg-gray-100 object-cover dark:bg-zinc-800"
										loading="lazy"
									/>
								</a>
								<div class="min-w-0 flex-1">
									<a href={`/page48/u/${user.username}`} class="group/name block">
										<span
											class="truncate text-[15px] font-semibold text-gray-900 group-hover/name:underline dark:text-gray-100"
										>
											{user.name}
										</span>
										<span class="block truncate text-[13px] text-gray-500 dark:text-gray-400">
											@{user.username}
										</span>
									</a>
								</div>
								<button
									type="button"
									onclick={() => release(relation, user)}
									disabled={busyId === user.userId}
									class="shrink-0 rounded-full border border-gray-200 px-3.5 py-1.5 text-[13px] font-semibold text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50 dark:border-zinc-700 dark:text-gray-200 dark:hover:bg-zinc-800 cursor-pointer"
								>
									{listAction(relation)}
								</button>
							</div>
						{/each}

						{#if state.hasMore}
							<div class="flex justify-center py-3">
								<button
									type="button"
									onclick={() => loadMore(relation)}
									disabled={state.loadingMore}
									class="rounded-full border border-gray-200 px-4 py-2 text-[13px] font-semibold text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50 dark:border-zinc-700 dark:text-gray-200 dark:hover:bg-zinc-800 cursor-pointer"
								>
									{t('page48.userPage.loadMore')}
								</button>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
