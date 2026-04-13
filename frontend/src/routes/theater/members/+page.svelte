<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import type { Member } from '$lib/apis/members';
	import { MemberDetailModal } from '$lib/components/profile';
	import { EmptyState, ErrorState } from '$lib/components';
	import { showToast } from '$lib/stores';
	import { Search } from 'lucide-svelte';
	import { membersStore, isMembersLoading } from '$lib/stores/theater';
	import MemberCard from '$lib/components/theater/MemberCard.svelte';
	import MemberCardSkeleton from '$lib/components/theater/MemberCardSkeleton.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';

	const { t } = useTranslation();

	// State
	let loadingGenerations = $state(true);
	let searchQuery = $state('');
	let selectedGeneration: string | null = $state(null);
	let selectedType: string | null = $state(null);
	let generations: string[] = $state([]);
	let showMemberDetail = $state(false);
	let selectedMember: Member | null = $state(null);

	const teamOrder = ['LOVE', 'DREAM', 'PASSION', 'TRAINEE', 'JKT48_VIRTUAL'];
	const teamColors: Record<string, string> = {
		LOVE: 'text-pink-600 border-pink-500 bg-pink-50 dark:bg-pink-900/10',
		DREAM: 'text-cyan-600 border-cyan-500 bg-cyan-50 dark:bg-cyan-900/10',
		PASSION: 'text-orange-600 border-orange-500 bg-orange-50 dark:bg-orange-900/10',
		TRAINEE: 'text-[#c08081] border-[#c08081] bg-rose-50 dark:bg-rose-900/10',
		JKT48_VIRTUAL: 'text-blue-600 border-blue-500 bg-blue-50 dark:bg-blue-900/10',
		JKT48: 'text-pink-600 border-pink-500 bg-pink-50 dark:bg-pink-900/10'
	};

	const accentColors: Record<string, string> = {
		LOVE: 'bg-pink-500 shadow-pink-500/20',
		DREAM: 'bg-cyan-500 shadow-cyan-500/20',
		PASSION: 'bg-orange-500 shadow-orange-500/20',
		TRAINEE: 'bg-[#c08081] shadow-[#c08081]/20',
		JKT48_VIRTUAL: 'bg-blue-600 shadow-blue-600/20',
		JKT48: 'bg-pink-500 shadow-pink-500/20'
	};

	const teamNames: Record<string, string> = {
		LOVE: 'Team Love',
		DREAM: 'Team Dream',
		PASSION: 'Team Passion',
		TRAINEE: 'Trainee',
		JKT48_VIRTUAL: 'JKT48 Virtual',
		JKT48: 'Member'
	};
	// Store data via derived runes
	let membersState = $derived($membersStore);
	let membersList = $derived(membersState.list);
	let pagination = $derived(membersState.pagination);
	let error = $derived(membersState.error);

	async function fetchGenerations() {
		try {
			if (generations.length === 0) {
				const gens = await membersStore.getGenerations();
				generations = gens.sort((a: string, b: string) => parseInt(a) - parseInt(b));
			}
		} catch {
			// Error logged by store
		} finally {
			loadingGenerations = false;
		}
	}

	// Fetch members
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
		} catch {
			// Error logged by store
			showToast($t('theater.members.errorTitle') || 'Failed to load members', 'error');
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

	function setType(type: string | null) {
		selectedType = type;
	}

	function openMemberDetail(member: Member) {
		selectedMember = member;
		showMemberDetail = true;
	}

	function closeMemberDetail() {
		showMemberDetail = false;
	}

	let mounted = $state(false);

	onMount(async () => {
		fetchGenerations();

		// Always reset filter to "All" on mount
		selectedGeneration = null;

		// Fetch members with "All" filter, loading a larger batch initially (100)
		// to ensure the modal sidebar has all members.
		await membersStore.load({ limit: 100 }, true);
		mounted = true;
	});

	function handleInfiniteScroll() {
		if (!$isMembersLoading && pagination.hasMore) {
			fetchMembers(false);
		}
	}
	let filteredList = $derived(
		membersList.filter((m) => {
			if (selectedType && (m.member_type || 'JKT48') !== selectedType) return false;
			return true;
		})
	);

	let groupedMembers = $derived(
		filteredList.reduce(
			(acc, member) => {
				const type = member.member_type || 'JKT48';
				if (!acc[type]) acc[type] = [];
				acc[type].push(member);
				return acc;
			},
			{} as Record<string, Member[]>
		)
	);

	let types = $derived(
		[...teamOrder, 'JKT48'].filter((t) => groupedMembers[t] && groupedMembers[t].length > 0)
	);
	// Handle any dynamic types not in our list
	let otherTypes = $derived(
		Object.keys(groupedMembers)
			.filter((t) => !teamOrder.includes(t) && t !== 'JKT48')
			.sort()
	);
	let allSortedTypes = $derived([...types, ...otherTypes]);
</script>

<SEO
	title={$t('theater.members.title')}
	path="/theater/members"
	description={$t('theater.members.subtitle')}
/>

<div class="space-y-6 mb-2">
	<!-- Search and Filters -->
	<div class="flex flex-col md:flex-row gap-4 md:items-center justify-between">
		<!-- Generation Filters -->
		<div class="flex-1 overflow-x-auto pb-2 -mx-4 px-4 md:mx-0 md:px-0 scrollbar-hide">
			<div class="flex items-center gap-2">
				<button
					onclick={() => setGeneration(null)}
					class={`px-3 sm:px-4 py-1.5 sm:py-2.5 rounded-full text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
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
							onclick={() => setGeneration(gen)}
							class={`px-3 sm:px-4 py-1.5 sm:py-2.5 rounded-full text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
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
		<div class="relative w-full md:w-80 shrink-0">
			<Search class="absolute left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
			<input
				type="text"
				placeholder={$t('common.search')}
				value={searchQuery}
				oninput={handleSearch}
				class="w-full pl-9.5 pr-4 py-2 bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-700 rounded-full text-sm text-themed placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-pink-500/20 focus:border-pink-500 transition-all shadow-sm"
			/>
		</div>
	</div>

	<!-- Team Filters -->
	<div class="overflow-x-auto pb-4 -mx-4 px-4 md:mx-0 md:px-0 scrollbar-hide">
		<div class="flex items-center gap-2">
			<button
				onclick={() => setType(null)}
				class={`px-4 sm:px-6 py-1.5 sm:py-2.5 rounded-full text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
					selectedType === null
						? 'bg-pink-100 dark:bg-pink-500/20 text-pink-600 dark:text-pink-400 shadow-sm ring-1 ring-pink-200 dark:ring-pink-500/30'
						: 'bg-white dark:bg-zinc-900 text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-700 hover:border-pink-500/50'
				}`}
			>
				Semua Member
			</button>
			{#each teamOrder as type}
				<button
					onclick={() => setType(type)}
					class={`px-4 sm:px-6 py-1.5 sm:py-2.5 rounded-full text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer border ${
						selectedType === type
							? teamColors[type] || 'bg-pink-500 text-white'
							: 'bg-white dark:bg-zinc-900 text-gray-500 dark:text-gray-400 border-gray-100 dark:border-zinc-700 hover:border-themed'
					}`}
				>
					{teamNames[type] || type}
				</button>
			{/each}
		</div>
	</div>
</div>

<!-- Members Grid -->
{#if (!mounted || $isMembersLoading) && membersList.length === 0}
	<div
		class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-3 sm:gap-4"
	>
		<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
		{#each Array(14) as _}
			<MemberCardSkeleton />
		{/each}
	</div>
{:else if error && membersList.length === 0}
	<ErrorState
		title={$t('theater.members.errorTitle') || 'Failed to load members'}
		description={$t('theater.members.errorDesc') || error || ''}
		onRetry={() => fetchMembers(true)}
	/>
{:else if membersList.length === 0}
	<EmptyState
		icon={Search}
		title={$t('member.emptyState.title')}
		description={$t('member.emptyState.description')}
	>
		{#if searchQuery || selectedGeneration}
			<button
				onclick={() => {
					searchQuery = '';
					selectedGeneration = null;
					fetchMembers(true);
				}}
				class="mt-4 px-6 py-2 bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 rounded-full text-sm font-bold hover:bg-pink-200 dark:hover:bg-pink-900/50 transition-colors cursor-pointer"
			>
				{$t('common.clearFilters')}
			</button>
		{/if}
	</EmptyState>
{:else}
	{#each allSortedTypes as type}
		<div class="mb-8 last:mb-0">
			<!-- Group Header -->
			<div class="flex items-center gap-3 mb-2 group/header">
				<div
					class={`h-8 w-1.5 rounded-full group-hover/header:h-10 transition-all duration-300 shadow-lg ${accentColors[type] || 'bg-pink-500 shadow-pink-500/20'}`}
				></div>
				<h2 class="text-xl font-bold text-themed tracking-tight">
					{teamNames[type] || type}
				</h2>
				<span
					class="px-2.5 py-0.5 rounded-full bg-gray-100 dark:bg-zinc-800 text-[10px] font-black uppercase tracking-wider text-gray-500 dark:text-gray-400 border border-gray-200/50 dark:border-zinc-700/50"
				>
					{groupedMembers[type].length}
				</span>
			</div>

			<!-- Grid -->
			<div
				class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-3 sm:gap-4"
			>
				{#each groupedMembers[type] as member (member.id)}
					<MemberCard {member} onclick={() => openMemberDetail(member)} />
				{/each}
			</div>
		</div>
	{/each}

	<!-- Skeletons for Infinite Scroll (Appending) -->
	{#if $isMembersLoading && membersList.length > 0}
		<div
			class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-3 sm:gap-4 mt-3 sm:mt-4"
		>
			<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
			{#each Array(7) as _}
				<MemberCardSkeleton />
			{/each}
		</div>
	{/if}

	<!-- Sentinel for Infinite Scroll -->
	<div
		use:infiniteScroll
		onintersect={handleInfiniteScroll}
		class="h-8 w-full flex justify-center items-center py-2"
	></div>
{/if}

<!-- Member Detail Modal -->
<MemberDetailModal
	show={showMemberDetail}
	member={selectedMember}
	members={membersList}
	loading={false}
	onClose={closeMemberDetail}
/>
