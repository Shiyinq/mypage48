<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { Member } from '$lib/apis/members';
	import { MemberDetailModal } from '$lib/components/profile';
	import { EmptyState, ErrorState } from '$lib/components';
	import { showToast } from '$lib/stores';
	import { Search } from 'lucide-svelte';
	import { membersStore, isMembersLoading } from '$lib/stores/theater';
	import MemberCard from '$lib/components/theater/MemberCard.svelte';
	import MemberCardSkeleton from '$lib/components/theater/MemberCardSkeleton.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import SEO from '$lib/components/SEO.svelte';

	const { t } = useTranslation();

	// State
	let loadingGenerations = true;
	let searchQuery = '';
	let selectedGeneration: string | null = null;
	let generations: string[] = [];
	let showMemberDetail = false;
	let selectedMember: Member | null = null;
	
	// Store subscriptions
	$: state = $membersStore;
	$: membersList = state.list;
	$: pagination = state.pagination;
	$: error = state.error;
	$: isAppending = $isMembersLoading && membersList.length > 0 && pagination.page > 0;

	async function fetchGenerations() {
		try {
			if (generations.length === 0) {
				const gens = await membersStore.getGenerations();
				generations = gens.sort((a: string, b: string) => parseInt(a) - parseInt(b));
			}
		} catch (e) {
			// Error logged by store
		} finally {
			loadingGenerations = false;
		}
	}

	async function fetchMembers(reset = false) {
		if ($isMembersLoading) return;
		try {
			await membersStore.load(
				{
					generation: selectedGeneration || undefined,
					search: searchQuery || undefined
				},
				reset
			);
		} catch (err) {
			showToast($t('theater.members.errorTitle') || 'Failed to load members', 'error');
		}
	}

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
		selectedGeneration = null;
		membersStore.load({ limit: 100 }, true);
	});

	function handleInfiniteScroll() {
		if (!$isMembersLoading && pagination.hasMore) {
			fetchMembers(false);
		}
	}

	$: groupedMembers = membersList.reduce(
		(acc, member) => {
			const type = member.member_type || 'JKT48';
			if (!acc[type]) acc[type] = [];
			acc[type].push(member);
			return acc;
		},
		{} as Record<string, Member[]>
	);

	$: types = Object.keys(groupedMembers).sort((a, b) => {
		if (a === 'JKT48') return -1;
		if (b === 'JKT48') return 1;
		return a.localeCompare(b);
	});
</script>

<SEO
	title={$t('theater.members.title')}
	path="/jkt48/members"
	description={$t('theater.members.subtitle')}
/>

<div class="space-y-12 pt-4 md:pt-6 pb-12">
	<div class="text-center space-y-4 mb-8">
		<h1 class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter uppercase mb-3">
			{$t('theater.members.title')}
		</h1>
		<p class="text-base md:text-lg text-slate-500 dark:text-slate-400 font-medium max-w-2xl mx-auto uppercase tracking-widest">
			{$t('theater.members.subtitle')}
		</p>
	</div>

	<!-- Search and Filters -->
	<div class="flex flex-col-reverse md:flex-row gap-4 mb-8 md:items-center justify-between">
		<!-- Generation Filters -->
		<div class="flex-1 overflow-x-auto pb-2 -mx-4 px-4 md:mx-0 md:px-0 scrollbar-hide">
			<div class="flex items-center gap-2">
				<button
					on:click={() => setGeneration(null)}
					class={`px-4 py-2.5 rounded-full text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
						selectedGeneration === null
							? 'bg-red-600 text-white shadow-lg shadow-red-500/20'
							: 'bg-white dark:bg-zinc-900 text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 border border-gray-100 dark:border-zinc-700'
					}`}
				>
					{$t('common.all')}
				</button>
				{#if loadingGenerations}
					{#each Array(5) as _}
						<div class="h-[42px] w-20 bg-gray-100 dark:bg-zinc-800 rounded-full animate-pulse shrink-0"></div>
					{/each}
				{:else}
					{#each generations as gen}
						<button
							on:click={() => setGeneration(gen)}
							class={`px-4 py-2.5 rounded-full text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
								selectedGeneration === gen
									? 'bg-red-600 text-white shadow-lg shadow-red-500/20'
									: 'bg-white dark:bg-zinc-900 text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 border border-gray-100 dark:border-zinc-700'
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
				class="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-700 rounded-full text-sm text-themed placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all shadow-sm"
			/>
		</div>
	</div>

	<!-- Members Grid -->
	{#if $isMembersLoading && membersList.length === 0}
		<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6">
			{#each Array(12) as _}
				<MemberCardSkeleton />
			{/each}
		</div>
	{:else if error && membersList.length === 0}
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
					class="mt-4 px-6 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-full text-sm font-bold hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors cursor-pointer"
				>
					{$t('common.clearFilters')}
				</button>
			{/if}
		</EmptyState>
	{:else}
		{#each types as type}
			<div class="mb-16 last:mb-0">
				<!-- Group Header -->
				<div class="flex items-center gap-4 mb-8 group/header">
					<div class="h-10 w-2 bg-red-600 rounded-full shadow-lg shadow-red-500/20"></div>
					<h2 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase">
						{type === 'JKT48'
							? $t('member.type.member') || 'Member'
							: $t('member.type.trainee') || 'Trainee'}
					</h2>
					<span class="px-3 py-1 rounded-full bg-white dark:bg-zinc-900 text-xs font-black text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-800 shadow-sm">
						{groupedMembers[type].length}
					</span>
				</div>

				<!-- Grid -->
				<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6">
					{#each groupedMembers[type] as member (member.id)}
						<MemberCard {member} on:click={() => openMemberDetail(member)} />
					{/each}
				</div>
			</div>
		{/each}

		<!-- Skeletons for Infinite Scroll (Appending) -->
		{#if $isMembersLoading && membersList.length > 0}
			<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6 mt-6">
				{#each Array(6) as _}
					<MemberCardSkeleton />
				{/each}
			</div>
		{/if}

		<!-- Sentinel for Infinite Scroll -->
		<div
			use:infiniteScroll
			on:intersect={handleInfiniteScroll}
			class="h-8 w-full flex justify-center items-center py-2"
		></div>
	{/if}
</div>

<!-- Member Detail Modal -->
<MemberDetailModal
	show={showMemberDetail}
	member={selectedMember}
	members={membersList}
	loading={false}
	onClose={closeMemberDetail}
/>
