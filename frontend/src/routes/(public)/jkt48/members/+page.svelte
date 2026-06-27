<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { Member } from '$lib/apis/members';
	import { MemberDetailModal } from '$lib/components/profile';
	import { EmptyState, ErrorState } from '$lib/components';
	import { showToast } from '$lib/stores';
	import { Search, Heart, Flame, Star, Sprout, Bot, ChevronDown, Filter, X } from 'lucide-svelte';
	import { membersStore, isMembersLoading } from '$lib/stores/theater.svelte';
	import MemberCard from '$lib/components/theater/MemberCard.svelte';
	import MemberCardSkeleton from '$lib/components/theater/MemberCardSkeleton.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import SEO from '$lib/components/SEO.svelte';
	import { getTeamColors } from '$lib/constants/teamColors';

	const { t } = useTranslation();

	// State
	let searchQuery = $state('');
	let selectedGeneration: string | null = $state(null);
	let selectedType: string | null = $state(null);
	let generations: string[] = $state([]);
	let showMemberDetail = $state(false);
	let selectedMember: Member | null = $state(null);

	const teamOrder = ['LOVE', 'DREAM', 'PASSION', 'TRAINEE', 'JKT48_VIRTUAL'];

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
			showToast(t('theater.members.errorTitle') || 'Failed to load members', 'error');
		}
	}

	/*
	let searchTimeout: ReturnType<typeof setTimeout>;
	function handleSearch(e: Event) {
		const target = e.target as HTMLInputElement;
		searchQuery = target.value;
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			fetchMembers(true);
		}, 300);
	}
	*/

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
		selectedGeneration = null;
		await membersStore.load({ limit: 100 }, true);

		const idFromUrl = $page.url.searchParams.get('id');
		if (idFromUrl) {
			const member = membersList.find((m) => m.id.toString() === idFromUrl);
			if (member) {
				openMemberDetail(member);
			}
		}

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

	let emptyStateTitle = $derived(
		selectedGeneration && selectedType
			? t('member.emptyState.titleGenTeam', {
					gen: selectedGeneration,
					team: teamNames[selectedType] || selectedType
				})
			: selectedType
				? t('member.emptyState.titleTeam', { team: teamNames[selectedType] || selectedType })
				: selectedGeneration
					? t('member.emptyState.titleGen', { gen: selectedGeneration })
					: t('member.emptyState.title')
	);
</script>

<SEO title={t('theater.members.title')} path="/jkt48/members" description={t('seo.members')} />

<div class="space-y-8 pt-4 md:pt-6 pb-12 px-0 sm:px-0">
	<div class="text-center space-y-4 mb-8">
		<h1
			class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter uppercase mb-3"
		>
			{t('theater.members.title')}
		</h1>
		<p
			class="text-base md:text-lg text-slate-500 dark:text-slate-400 font-medium max-w-2xl mx-auto uppercase tracking-widest"
		>
			{t('theater.members.subtitle')}
		</p>
	</div>

	<!-- Search and Filters -->
	<div
		class="flex flex-col md:flex-row gap-3 items-center justify-center mb-8 w-full max-w-4xl mx-auto px-4 md:px-0"
	>
		<!-- Filter Pill -->
		<div
			class="flex items-center bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md rounded-full px-2 py-1 shadow-sm border border-gray-100 dark:border-zinc-800 shrink-0 w-full md:w-auto h-[46px] sm:h-[50px]"
		>
			<div class="flex items-center px-2 sm:px-4 text-gray-400">
				{#if selectedGeneration || selectedType}
					<button
						class="text-red-500 hover:text-red-700 hover:bg-red-500/10 p-1.5 -m-1.5 rounded-full cursor-pointer transition-all"
						onclick={() => {
							selectedGeneration = null;
							selectedType = null;
							fetchMembers(true);
						}}
						aria-label={t('common.clearFilters')}
					>
						<X class="w-4 sm:w-4.5 h-4 sm:h-4.5" />
					</button>
				{:else}
					<Filter class="w-4 sm:w-4.5 h-4 sm:h-4.5" />
				{/if}
			</div>

			<div class="h-6 w-px bg-gray-200 dark:bg-zinc-800 mx-1"></div>

			<!-- Generation -->
			<div class="relative flex-1 md:flex-none">
				<select
					id="public-member-gen-select"
					name="generation"
					class="w-full appearance-none bg-transparent pl-2 sm:pl-4 pr-7 sm:pr-9 py-2 text-[13px] sm:text-sm font-bold text-slate-700 dark:text-slate-200 focus:outline-none cursor-pointer hover:text-red-600 dark:hover:text-red-400 transition-colors"
					value={selectedGeneration === null ? '' : selectedGeneration}
					onchange={(e) =>
						setGeneration(e.currentTarget.value === '' ? null : e.currentTarget.value)}
					aria-label="Generation"
				>
					<option value="" class="dark:bg-zinc-800">{t('common.all')} Gen</option>
					{#each generations as gen}
						<option value={gen} class="dark:bg-zinc-800">Gen {gen}</option>
					{/each}
				</select>
				<ChevronDown
					class="absolute right-2 sm:right-3.5 top-1/2 transform -translate-y-1/2 w-3.5 sm:w-4 h-3.5 sm:h-4 text-gray-400 pointer-events-none"
				/>
			</div>

			<div class="h-6 w-px bg-gray-200 dark:bg-zinc-800 mx-1"></div>

			<!-- Team -->
			<div class="relative flex-1 md:flex-none">
				<select
					id="public-member-team-select"
					name="team"
					class="w-full appearance-none bg-transparent pl-2 sm:pl-4 pr-7 sm:pr-9 py-2 text-[13px] sm:text-sm font-bold text-slate-700 dark:text-slate-200 focus:outline-none cursor-pointer hover:text-red-600 dark:hover:text-red-400 transition-colors"
					value={selectedType === null ? '' : selectedType}
					onchange={(e) => setType(e.currentTarget.value === '' ? null : e.currentTarget.value)}
					aria-label="Team"
				>
					<option value="" class="dark:bg-zinc-800">{t('theater.members.allTeams')}</option>
					{#each teamOrder as type}
						<option value={type} class="dark:bg-zinc-800">{teamNames[type] || type}</option>
					{/each}
				</select>
				<ChevronDown
					class="absolute right-2 sm:right-3.5 top-1/2 transform -translate-y-1/2 w-3.5 sm:w-4 h-3.5 sm:h-4 text-gray-400 pointer-events-none"
				/>
			</div>
		</div>

		<!-- Search Pill (Hidden temporarily) -->
		<!-- 
		<div class="relative w-full md:w-72 shrink-0">
			<Search class="absolute left-5 top-1/2 transform -translate-y-1/2 w-4.5 h-4.5 text-gray-400 z-10 pointer-events-none" />
			<input
				type="text"
				placeholder={t('common.search')}
				value={searchQuery}
				oninput={handleSearch}
				class="w-full pl-12 pr-5 py-3 sm:py-3.5 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md rounded-full text-sm font-bold text-slate-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500/20 shadow-sm border border-gray-100 dark:border-zinc-800 transition-all"
			/>
		</div>
		-->
	</div>

	<!-- Members Grid -->
	{#if (!mounted || isMembersLoading.value) && membersList.length === 0}
		<div
			class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-6"
		>
			{#each Array(12)}
				<MemberCardSkeleton />
			{/each}
		</div>
	{:else if error && membersList.length === 0}
		<ErrorState
			title={t('theater.members.errorTitle') || 'Failed to load members'}
			description={t('theater.members.errorDesc') || error || ''}
			onRetry={fetchMembers}
		/>
	{:else if filteredList.length === 0}
		<EmptyState
			icon={Search}
			title={emptyStateTitle}
			description={t('member.emptyState.description')}
		>
			{#if searchQuery || selectedGeneration || selectedType}
				<button
					onclick={() => {
						searchQuery = '';
						selectedGeneration = null;
						selectedType = null;
						fetchMembers(true);
					}}
					class="mt-4 px-6 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-full text-sm font-bold hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors cursor-pointer"
				>
					{t('common.clearFilters')}
				</button>
			{/if}
		</EmptyState>
	{:else}
		{#each allSortedTypes as type}
			<div class="mb-10 last:mb-0">
				<!-- Group Header -->
				<div class="flex items-center gap-3 mb-2 group/header">
					<span
						class="flex items-center drop-shadow-md"
						style:color={getTeamColors(type).badgeText}
					>
						{#if type?.toUpperCase() === 'LOVE'}
							<Heart class="w-8 h-8 fill-current" />
						{:else if type?.toUpperCase() === 'PASSION'}
							<Flame class="w-8 h-8 fill-current" />
						{:else if type?.toUpperCase() === 'DREAM'}
							<Star class="w-8 h-8 fill-current" />
						{:else if type?.toUpperCase() === 'TRAINEE'}
							<Sprout class="w-8 h-8" />
						{:else if type?.toUpperCase() === 'JKT48_VIRTUAL'}
							<Bot class="w-8 h-8" />
						{:else}
							<Star class="w-8 h-8 fill-current" />
						{/if}
					</span>
					<h2
						class="text-2xl font-black tracking-tight uppercase"
						style:color={getTeamColors(type).badgeText}
					>
						{teamNames[type] || type}
					</h2>
					<span
						class="px-3 py-1 rounded-full bg-white dark:bg-zinc-900 text-xs font-black text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-800 shadow-sm"
					>
						{groupedMembers[type].length}
					</span>
				</div>

				<!-- Grid -->
				<div
					class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-6"
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
				class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-6 mt-6"
			>
				{#each Array(6)}
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
</div>

<!-- Member Detail Modal -->
<MemberDetailModal
	show={showMemberDetail}
	member={selectedMember}
	members={membersList}
	loading={false}
	onClose={closeMemberDetail}
/>
