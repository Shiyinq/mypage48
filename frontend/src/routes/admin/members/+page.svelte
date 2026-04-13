<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { adminStore, isAdminMembersLoading } from '$lib/stores/admin';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { showToast } from '$lib/stores';
	import type { Member } from '$lib/apis/members';
	import TableSkeleton from '$lib/components/skeletons/TableSkeleton.svelte';
	import MemberTable from '$lib/components/admin/MemberTable.svelte';
	import AdminMemberModal from '$lib/components/admin/AdminMemberModal.svelte';
	import AdminDeleteModal from '$lib/components/admin/AdminDeleteModal.svelte';
	import { Plus, Users, Search, X } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	// Store state
	let membersList = $derived($adminStore.members.data);
	let membersHasMore = $derived($adminStore.members.hasMore);

	// Search state
	let searchQuery = $state('');
	let searchTimeout: ReturnType<typeof setTimeout>;

	// Modal states
	let showMemberModal = $state(false);
	let showDeleteModal = $state(false);
	let editingMember: Partial<Member> = $state({});
	let isCreatingMember = $state(false);
	let isSubmitting = $state(false);
	let deletingId: string | number | null = null;

	// Initial load state
	let isInitialLoad = $state(true);

	onMount(() => {
		// Only load if data is not already cached
		if (membersList.length === 0) {
			adminStore.loadMembers();
		} else {
			isInitialLoad = false;
		}
	});

	// Update initial load state when data is loaded
	$effect(() => {
		if (membersList.length > 0) {
			isInitialLoad = false;
		}
	});

	onDestroy(() => {
		if (searchTimeout) clearTimeout(searchTimeout);
	});

	function handleSearch() {
		if (searchTimeout) clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			adminStore.setMemberSearch(searchQuery);
		}, 300);
	}

	function clearSearch() {
		searchQuery = '';
		handleSearch();
	}

	function loadMoreMembers() {
		if (membersHasMore && !$isAdminMembersLoading) {
			adminStore.loadMembers();
		}
	}

	function openCreateMember() {
		editingMember = {};
		isCreatingMember = true;
		showMemberModal = true;
	}

	function openEditMember(member: Member) {
		editingMember = member;
		isCreatingMember = false;
		showMemberModal = true;
	}

	function confirmDeleteMember(member: Member) {
		deletingId = member.id;
		showDeleteModal = true;
	}

	async function handleMemberSubmit(data: Partial<Member>) {
		isSubmitting = true;
		try {
			if (isCreatingMember) {
				await adminStore.createMember(data as Omit<Member, 'id'>);
				showToast($t('admin.members.modal.created'), 'success');
			} else if (editingMember && editingMember.id !== undefined) {
				await adminStore.updateMember(editingMember.id, data as Partial<Omit<Member, 'id'>>);
				showToast($t('admin.members.modal.updated'), 'success');
			}
			showMemberModal = false;
		} catch {
			showToast($t('admin.members.modal.failedSave'), 'error');
		} finally {
			isSubmitting = false;
		}
	}

	async function handleDeleteConfirm() {
		if (deletingId === null) return;
		try {
			await adminStore.deleteMember(deletingId);
			showToast($t('admin.members.modal.deleted'), 'success');
			showDeleteModal = false;
		} catch {
			showToast($t('admin.members.modal.failedDelete'), 'error');
		}
	}
</script>

<div>
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 bg-white dark:bg-zinc-800 p-4 rounded-3xl shadow-sm"
	>
		<div class="flex flex-col sm:flex-row sm:items-center gap-4 flex-1">
			<h2 class="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2 min-w-fit">
				<Users class="w-5 h-5 text-pink-500" />
				{$t('admin.members.title')} ({$adminStore.members.total})
			</h2>

			<!-- Search Input -->
			<div class="relative w-full sm:max-w-xs">
				<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
				<input
					type="text"
					bind:value={searchQuery}
					oninput={handleSearch}
					placeholder={$t('admin.members.searchPlaceholder')}
					class="w-full pl-9 pr-8 py-2 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl text-sm focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none transition-all"
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

		<button
			onclick={openCreateMember}
			class="px-4 py-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl font-bold text-sm flex items-center gap-2 hover:opacity-90 transition-opacity shadow-lg shadow-gray-200 dark:shadow-none cursor-pointer"
		>
			<Plus class="w-4 h-4" />
			{$t('admin.members.addMember')}
		</button>
	</div>

	{#if isInitialLoad && $isAdminMembersLoading}
		<TableSkeleton
			rows={10}
			columns={[
				$t('admin.members.table.memberInfo'),
				$t('admin.members.table.generation'),
				$t('admin.members.table.status'),
				$t('admin.members.table.actions')
			]}
		/>
	{:else}
		<MemberTable members={membersList} onedit={openEditMember} ondelete={confirmDeleteMember} />

		<!-- Infinite Scroll Sentinel -->
		{#if membersHasMore}
			<div class="mt-4" use:infiniteScroll onintersect={loadMoreMembers}>
				{#if $isAdminMembersLoading}
					<TableSkeleton
						rows={3}
						columns={[
							$t('admin.members.table.memberInfo'),
							$t('admin.members.table.generation'),
							$t('admin.members.table.status'),
							$t('admin.members.table.actions')
						]}
						showHeader={false}
					/>
				{/if}
			</div>
		{:else if membersList.length > 0}
			<div class="py-12 text-center text-gray-400 text-sm">
				{$t('admin.members.noMoreMembers')}
			</div>
		{:else}
			<div class="py-20 text-center text-gray-500">
				{$t('admin.members.noMembersFound', { query: searchQuery })}
			</div>
		{/if}
	{/if}
</div>

<!-- Member Modal -->
<AdminMemberModal
	bind:show={showMemberModal}
	member={editingMember}
	isCreating={isCreatingMember}
	{isSubmitting}
	onsubmit={handleMemberSubmit}
/>

<!-- Delete Confirmation Modal -->
<AdminDeleteModal
	bind:show={showDeleteModal}
	onCancel={() => (showDeleteModal = false)}
	onConfirm={handleDeleteConfirm}
	title={$t('admin.members.modal.deleteTitle')}
	description={$t('admin.members.modal.deleteDesc')}
/>
