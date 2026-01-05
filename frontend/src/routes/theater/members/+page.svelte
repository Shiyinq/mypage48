<script lang="ts">
	export let params: Record<string, string> | undefined = undefined;
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import type { Member } from '$lib/apis/members';
	import { MemberDetailModal } from '$lib/components/profile';
	import { EmptyState, ErrorState } from '$lib/components';
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { Search } from 'lucide-svelte';
	import { membersStore } from '$lib/stores/theater';
	import MemberCard from '$lib/components/theater/MemberCard.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';

	const { t } = useTranslation();

	// State
	let isLoading = false;
	let isAppending = false;
	let loadingGenerations = true;
	let searchQuery = '';
	let selectedGeneration: string | null = null;
	let generations: string[] = [];
	let error: string | null = null;
	let showMemberDetail = false;
	let selectedMember: Member | null = null;

	// Subscribe to store
	$: state = $membersStore;
	$: membersList = state.list;
	$: pagination = state.pagination;

	async function fetchGenerations() {
		try {
			if (generations.length === 0) {
				const gens = await membersStore.getGenerations();
				generations = gens.sort((a: string, b: string) => parseInt(a) - parseInt(b));
			}
		} catch (e) {
			logger.error('Failed to fetch generations', e, { context: 'MembersPage' });
		} finally {
			loadingGenerations = false;
		}
	}

	// Fetch members
	async function fetchMembers(reset = false) {
		if (isLoading || isAppending) return;

		if (reset) {
			isLoading = true;
		} else {
			isAppending = true;
		}
		error = null;

		try {
			await membersStore.load(
				{
					generation: selectedGeneration || undefined,
					search: searchQuery || undefined
				},
				reset
			);
		} catch (err) {
			logger.error('Failed to fetch members', err, { context: 'MembersPage' });
			error = 'Failed to load members';
			showToast($t('theater.members.errorTitle') || 'Failed to load members', 'error');
		} finally {
			isLoading = false;
			isAppending = false;
		}
	}

	// Watch filters
	let searchTimeout: ReturnType<typeof setTimeout>;
	function handleSearch(e: Event) {
		const target = e.target as HTMLInputElement;
		searchQuery = target.value;
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			fetchMembers(true);
		}, 300);
	}

	function setGeneration(gen: string | null) {
		selectedGeneration = gen;
		fetchMembers(true);
	}

	function openMemberDetail(member: Member) {
		selectedMember = member;
		showMemberDetail = true;
	}

	function closeMemberDetail() {
		showMemberDetail = false;
	}

	onMount(() => {
		fetchGenerations();

		// Always reset filter to "All" on mount
		selectedGeneration = null;

		// Fetch members with "All" filter (store will use cache if available)
		fetchMembers(true);
	});

	function handleInfiniteScroll() {
		if (!isLoading && !isAppending && pagination.hasMore) {
			fetchMembers(false);
		}
	}
</script>

<SEO
	title={$t('theater.members.title')}
	path="/theater/members"
	description={$t('theater.members.subtitle')}
/>

<!-- Search and Filters -->
<div class="flex flex-col-reverse md:flex-row gap-4 mb-6 md:items-center justify-between">
	<!-- Generation Filters -->
	<div class="flex-1 overflow-x-auto pb-2 -mx-4 px-4 md:mx-0 md:px-0 scrollbar-hide">
		<div class="flex items-center gap-2">
			<button
				on:click={() => setGeneration(null)}
				class={`px-4 py-2.5 rounded-full text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
					selectedGeneration === null
						? 'bg-pink-100 dark:bg-pink-500/20 text-pink-600 dark:text-pink-400 shadow-sm ring-1 ring-pink-200 dark:ring-pink-500/30'
						: 'bg-white dark:bg-zinc-900 text-gray-500 dark:text-gray-400 hover:text-pink-600 dark:hover:text-pink-400 border border-gray-100 dark:border-zinc-700'
				}`}
			>
				{$t('common.all')}
			</button>
			{#if loadingGenerations}
				<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
				{#each Array(5) as _}
					<div
						class="h-[42px] w-20 bg-gray-100 dark:bg-zinc-800 rounded-full animate-pulse shrink-0"
					></div>
				{/each}
			{:else}
				{#each generations as gen}
					<button
						on:click={() => setGeneration(gen)}
						class={`px-4 py-2.5 rounded-full text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
							selectedGeneration === gen
								? 'bg-pink-100 dark:bg-pink-500/20 text-pink-600 dark:text-pink-400 shadow-sm ring-1 ring-pink-200 dark:ring-pink-500/30'
								: 'bg-white dark:bg-zinc-900 text-gray-500 dark:text-gray-400 hover:text-pink-600 dark:hover:text-pink-400 border border-gray-100 dark:border-zinc-700'
						}`}
					>
						Gen {gen}
					</button>
				{/each}
			{/if}
		</div>
	</div>

	<!-- Search Bar -->
	<div class="relative w-full md:w-64 shrink-0">
		<Search class="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
		<input
			type="text"
			placeholder={$t('common.search')}
			value={searchQuery}
			on:input={handleSearch}
			class="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-700 rounded-full text-sm text-themed placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-pink-500/20 focus:border-pink-500 transition-all shadow-sm"
		/>
	</div>
</div>

<!-- Members Grid -->
{#if isLoading}
	<div
		class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-3 sm:gap-4"
	>
		<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
		{#each Array(14) as _}
			<div
				class="flex flex-col bg-white dark:bg-zinc-900 rounded-xl overflow-hidden border-2 border-pink-100 dark:border-pink-900/30 shadow-sm"
			>
				<div
					class="relative w-full bg-gray-100 dark:bg-zinc-800 animate-pulse"
					style="aspect-ratio: 2/3;"
				></div>
				<div
					class="flex-1 p-2.5 flex flex-col items-center justify-center gap-1.5 bg-pink-50/50 dark:bg-zinc-900/50"
				>
					<div class="w-16 h-3 bg-gray-100 dark:bg-zinc-800 rounded animate-pulse"></div>
					<div class="w-20 h-2.5 bg-gray-50 dark:bg-zinc-800/50 rounded animate-pulse"></div>
				</div>
			</div>
		{/each}
	</div>
{:else if error}
	<ErrorState
		title={$t('theater.members.errorTitle') || 'Failed to load members'}
		description={$t('theater.members.errorDesc') || error || ''}
		onRetry={fetchMembers}
	/>
{:else if membersList.length === 0}
	<EmptyState
		icon={Search}
		title={$t('member.emptyState.title')}
		description={$t('member.emptyState.description')}
	>
		{#if searchQuery || selectedGeneration}
			<button
				on:click={() => {
					searchQuery = '';
					selectedGeneration = null;
					fetchMembers();
				}}
				class="mt-4 px-6 py-2 bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 rounded-full text-sm font-bold hover:bg-pink-200 dark:hover:bg-pink-900/50 transition-colors cursor-pointer"
			>
				{$t('common.clearFilters')}
			</button>
		{/if}
	</EmptyState>
{:else}
	<div
		class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-3 sm:gap-4"
	>
		{#each membersList as member (member.id)}
			<MemberCard {member} on:click={() => openMemberDetail(member)} />
		{/each}
	</div>

	<!-- Sentinel for Infinite Scroll -->
	<div
		use:infiniteScroll
		on:intersect={handleInfiniteScroll}
		class="h-8 w-full flex justify-center items-center py-2"
	>
		{#if isAppending}
			<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-pink-500"></div>
		{/if}
	</div>
{/if}

<!-- Member Detail Modal -->
<MemberDetailModal
	show={showMemberDetail}
	member={selectedMember}
	loading={false}
	onClose={closeMemberDetail}
/>
