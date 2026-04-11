<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { adminStore, isAdminSetlistsLoading } from '$lib/stores/admin';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { showToast } from '$lib/stores';
	import type { Setlist } from '$lib/apis/setlists';
	import TableSkeleton from '$lib/components/skeletons/TableSkeleton.svelte';
	import SetlistTable from '$lib/components/admin/SetlistTable.svelte';
	import AdminSetlistModal from '$lib/components/admin/AdminSetlistModal.svelte';
	import AdminDeleteModal from '$lib/components/admin/AdminDeleteModal.svelte';
	import { Plus, Music, Search, X } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	// Store state
	$: setlistsList = $adminStore.setlists.data;
	$: error = $adminStore.setlists.error;
	$: setlistsHasMore = $adminStore.setlists.hasMore;

	// Search state
	let searchQuery = '';
	let searchTimeout: ReturnType<typeof setTimeout>;

	// Modal states
	let showSetlistModal = false;
	let showDeleteModal = false;
	let editingSetlist: Partial<Setlist> = {};
	let isCreatingSetlist = false;
	let isSubmitting = false;
	let deletingId: string | null = null;

	// Initial load state
	let isInitialLoad = true;

	onMount(() => {
		// Only load if data is not already cached
		if (setlistsList.length === 0) {
			adminStore.loadSetlists();
		} else {
			isInitialLoad = false;
		}
	});

	// Update initial load state when data is loaded
	$: if (setlistsList.length > 0) {
		isInitialLoad = false;
	}

	onDestroy(() => {
		if (searchTimeout) clearTimeout(searchTimeout);
	});

	function handleSearch() {
		if (searchTimeout) clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			adminStore.setSetlistSearch(searchQuery);
		}, 300);
	}

	function clearSearch() {
		searchQuery = '';
		handleSearch();
	}

	function loadMoreSetlists() {
		if (setlistsHasMore && !$isAdminSetlistsLoading) {
			adminStore.loadSetlists();
		}
	}

	function openCreateSetlist() {
		editingSetlist = {};
		isCreatingSetlist = true;
		showSetlistModal = true;
	}

	function openEditSetlist(e: CustomEvent<Setlist>) {
		editingSetlist = e.detail;
		isCreatingSetlist = false;
		showSetlistModal = true;
	}

	function confirmDeleteSetlist(e: CustomEvent<Setlist>) {
		deletingId = e.detail.setlistId;
		showDeleteModal = true;
	}

	async function handleSetlistSubmit(e: CustomEvent<any>) {
		isSubmitting = true;
		try {
			if (isCreatingSetlist) {
				await adminStore.createSetlist(e.detail);
				showToast($t('admin.setlists.modal.created'), 'success');
			} else if (editingSetlist && editingSetlist.setlistId) {
				await adminStore.updateSetlist(editingSetlist.setlistId, e.detail);
				showToast($t('admin.setlists.modal.updated'), 'success');
			}
			showSetlistModal = false;
		} catch {
			showToast($t('admin.setlists.modal.failedSave'), 'error');
		} finally {
			isSubmitting = false;
		}
	}

	async function handleDeleteConfirm() {
		if (deletingId === null) return;
		try {
			await adminStore.deleteSetlist(deletingId);
			showToast($t('admin.setlists.modal.deleted'), 'success');
			showDeleteModal = false;
		} catch {
			showToast($t('admin.setlists.modal.failedDelete'), 'error');
		}
	}
</script>

<div>
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 bg-white dark:bg-zinc-800 p-4 rounded-3xl shadow-sm"
	>
		<div class="flex flex-col sm:flex-row sm:items-center gap-4 flex-1">
			<h2 class="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2 min-w-fit">
				<Music class="w-5 h-5 text-purple-500" />
				{$t('admin.setlists.title')} ({$adminStore.setlists.total})
			</h2>

			<!-- Search Input -->
			<div class="relative w-full sm:max-w-xs">
				<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
				<input
					type="text"
					bind:value={searchQuery}
					on:input={handleSearch}
					placeholder={$t('admin.setlists.searchPlaceholder')}
					class="w-full pl-9 pr-8 py-2 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all"
				/>
				{#if searchQuery}
					<button
						on:click={clearSearch}
						class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 cursor-pointer"
					>
						<X class="w-3 h-3" />
					</button>
				{/if}
			</div>
		</div>

		<button
			on:click={openCreateSetlist}
			class="px-4 py-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl font-bold text-sm flex items-center gap-2 hover:opacity-90 transition-opacity shadow-lg shadow-gray-200 dark:shadow-none cursor-pointer"
		>
			<Plus class="w-4 h-4" />
			{$t('admin.setlists.addSetlist')}
		</button>
	</div>

	{#if isInitialLoad && $isAdminSetlistsLoading}
		<TableSkeleton
			rows={10}
			columns={[
				$t('admin.setlists.table.setlistInfo'),
				$t('admin.setlists.table.japaneseTitle'),
				$t('admin.setlists.table.type'),
				$t('admin.setlists.table.status'),
				$t('admin.setlists.table.actions')
			]}
		/>
	{:else}
		<SetlistTable
			setlists={setlistsList}
			on:edit={openEditSetlist}
			on:delete={confirmDeleteSetlist}
		/>

		<!-- Infinite Scroll Sentinel -->
		{#if setlistsHasMore}
			<div class="mt-4" use:infiniteScroll on:intersect={loadMoreSetlists}>
				{#if $isAdminSetlistsLoading}
					<TableSkeleton
						rows={3}
						columns={[
							$t('admin.setlists.table.setlistInfo'),
							$t('admin.setlists.table.japaneseTitle'),
							$t('admin.setlists.table.type'),
							$t('admin.setlists.table.status'),
							$t('admin.setlists.table.actions')
						]}
						showHeader={false}
					/>
				{/if}
			</div>
		{:else if setlistsList.length > 0}
			<div class="py-12 text-center text-gray-400 text-sm">
				{$t('admin.setlists.noMoreSetlists')}
			</div>
		{:else}
			<div class="py-20 text-center text-gray-500">
				{$t('admin.setlists.noSetlistsFound', { query: searchQuery })}
			</div>
		{/if}
	{/if}
</div>

<!-- Setlist Modal -->
<AdminSetlistModal
	bind:show={showSetlistModal}
	setlist={editingSetlist}
	isCreating={isCreatingSetlist}
	{isSubmitting}
	on:submit={handleSetlistSubmit}
/>

<!-- Delete Confirmation Modal -->
<AdminDeleteModal
	bind:show={showDeleteModal}
	onCancel={() => (showDeleteModal = false)}
	onConfirm={handleDeleteConfirm}
	title={$t('admin.setlists.modal.deleteTitle')}
	description={$t('admin.setlists.modal.deleteDesc')}
/>
