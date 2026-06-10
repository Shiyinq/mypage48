<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import type { Member } from '$lib/apis/members';
	import { EmptyState, ErrorState } from '$lib/components';
	import { showToast } from '$lib/stores';
	import { Search, ChevronDown, Users } from 'lucide-svelte';
	import { membersStore, isMembersLoading } from '$lib/stores/theater.svelte';
	import MemberCard from '$lib/components/theater/MemberCard.svelte';
	import MemberCardSkeleton from '$lib/components/theater/MemberCardSkeleton.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';

	const { t } = useTranslation();

	// State
	let searchQuery = $state('');
	let selectedGeneration: string | null = $state(null);
	let selectedType: string | null = $state(null);
	let generations: string[] = $state([]);

	const teamOrder = ['LOVE', 'DREAM', 'PASSION', 'TRAINEE', 'JKT48_VIRTUAL'];
	const accentColors: Record<string, string> = {
		LOVE: 'bg-pink-500 shadow-pink-500/20',
		DREAM: 'bg-cyan-500 shadow-cyan-500/20',
		PASSION: 'bg-orange-500 shadow-orange-500/20',
		TRAINEE: 'bg-[#c08081] shadow-[#c08081]/20',
		JKT48_VIRTUAL: 'bg-blue-600 shadow-blue-600/20',
		JKT48: 'bg-pink-500 shadow-pink-500/20'
	};

	let teamNames = $derived<Record<string, string>>({
		LOVE: `${t('theater.members.team')} Love`,
		DREAM: `${t('theater.members.team')} Dream`,
		PASSION: `${t('theater.members.team')} Passion`,
		TRAINEE: t('member.type.trainee'),
		JKT48_VIRTUAL: 'JKT48 Virtual',
		JKT48: t('member.type.member')
	});
	// Store data via derived runes
	let membersList = $derived(membersStore.list);
	let pagination = $derived(membersStore.pagination);
	let error = $derived(membersStore.error);

	async function fetchGenerations() {
		try {
			if (generations.length === 0) {
				const gens = await membersStore.getGenerations();
				generations = gens.sort((a: string, b: string) => parseInt(a) - parseInt(b));
			}
		} catch {
			// Error logged by store
		}
	}

	// Fetch members
	async function fetchMembers(reset = false) {
		if (isMembersLoading.value) return;

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
			showToast(t('theater.members.errorTitle') || 'Failed to load members', 'error');
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
		goto(`/theater/members/${member.id}`);
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
		if (!isMembersLoading.value && pagination.hasMore) {
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
	title={t('theater.members.title')}
	path="/theater/members"
	description={t('theater.members.subtitle')}
/>

<div class="mb-3 md:mb-6 relative z-30">
	<PageHeader
		title={t('theater.members.title')}
		subtitle={t('theater.members.subtitle')}
		icon={Users}
		theme="pink"
		mobileActions={true}
	>
		{#snippet actions()}
			<div class="flex flex-col md:flex-row gap-3 items-start md:items-center w-full md:w-auto">
				<!-- Dropdown Filters -->
				<div class="flex w-full md:w-auto gap-2">
					<!-- Generation Select -->
					<div class="relative flex-1 md:flex-none">
						<select
							value={selectedGeneration === null ? '' : String(selectedGeneration)}
							onchange={(e) => setGeneration((e.target as HTMLSelectElement).value || null)}
							class="w-full appearance-none px-3 md:px-4 pr-9 md:pr-10 py-1.5 sm:py-2 h-8 sm:h-9 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-full text-xs font-bold text-gray-600 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-pink-500/20 focus:border-pink-500 transition-all shadow-sm cursor-pointer hover:border-pink-300 dark:hover:border-zinc-500"
						>
							<option value="">{t('common.all')} Gen</option>
							{#each generations as gen}
								<option value={gen}>Gen {gen}</option>
							{/each}
						</select>
						<ChevronDown
							class="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
						/>
					</div>

					<!-- Team Select -->
					<div class="relative flex-1 md:flex-none">
						<select
							value={selectedType === null ? '' : selectedType}
							onchange={(e) => setType((e.target as HTMLSelectElement).value || null)}
							class="w-full appearance-none px-3 md:px-4 pr-9 md:pr-10 py-1.5 sm:py-2 h-8 sm:h-9 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-full text-xs font-bold text-gray-600 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-pink-500/20 focus:border-pink-500 transition-all shadow-sm cursor-pointer hover:border-pink-300 dark:hover:border-zinc-500"
						>
							<option value="">{t('theater.members.allTeams')}</option>
							{#each teamOrder as type}
								<option value={type}>{teamNames[type] || type}</option>
							{/each}
						</select>
						<ChevronDown
							class="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
						/>
					</div>
				</div>

				<!-- Search Bar -->
				<div class="relative w-full md:w-64 shrink-0 hidden md:block">
					<Search
						class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400"
					/>
					<input
						type="text"
						placeholder={t('common.search')}
						value={searchQuery}
						oninput={handleSearch}
						class="w-full pl-9 pr-4 py-1.5 sm:py-2 h-8 sm:h-9 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-full text-xs font-semibold text-themed placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-pink-500/20 focus:border-pink-500 transition-all shadow-sm"
					/>
				</div>
			</div>
		{/snippet}
	</PageHeader>
</div>

<!-- Members Grid -->
{#if (!mounted || isMembersLoading.value) && membersList.length === 0}
	<div
		class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-3 sm:gap-4"
	>
		<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
		{#each Array(14)}
			<MemberCardSkeleton />
		{/each}
	</div>
{:else if error && membersList.length === 0}
	<ErrorState
		title={t('theater.members.errorTitle') || 'Failed to load members'}
		description={t('theater.members.errorDesc') || error || ''}
		onRetry={() => fetchMembers(true)}
	/>
{:else if membersList.length === 0}
	<EmptyState
		icon={Search}
		title={t('member.emptyState.title')}
		description={t('member.emptyState.description')}
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
				{t('common.clearFilters')}
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
	{#if isMembersLoading.value && membersList.length > 0}
		<div
			class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-3 sm:gap-4 mt-3 sm:mt-4"
		>
			<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
			{#each Array(7)}
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
