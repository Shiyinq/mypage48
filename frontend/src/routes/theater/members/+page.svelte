<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { members as membersApi, type Member } from '$lib/apis/members';
	import { MemberDetailModal } from '$lib/components/profile';
	import { EmptyState } from '$lib/components';
	import { Search } from 'lucide-svelte';

	const { t } = useTranslation();

	// State
	let membersList: Member[] = [];
	let isLoading = true;
	let searchQuery = '';
	let selectedGeneration: string | null = null;
	let generations: string[] = [];
	let error: string | null = null;
	let showMemberDetail = false;
	let selectedMember: Member | null = null;

	// Fetch members
	async function fetchMembers() {
		isLoading = true;
		error = null;
		try {
			const response = await membersApi.getAll({
				limit: 100,
				generation: selectedGeneration || undefined,
				search: searchQuery || undefined
			});
			membersList = response.members;

			// Extract unique generations from members
			if (generations.length === 0) {
				const uniqueGens = [...new Set(response.members.map((m) => m.generation).filter(Boolean))];
				generations = uniqueGens.sort((a, b) => parseInt(a) - parseInt(b));
			}
		} catch (err) {
			console.error('Failed to fetch members:', err);
			error = 'Failed to load members';
		} finally {
			isLoading = false;
		}
	}

	// Debounced search
	let searchTimeout: ReturnType<typeof setTimeout>;
	function handleSearch(e: Event) {
		const target = e.target as HTMLInputElement;
		searchQuery = target.value;
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			fetchMembers();
		}, 300);
	}

	// Filter by generation
	function setGeneration(gen: string | null) {
		selectedGeneration = gen;
		fetchMembers();
	}

	function openMemberDetail(member: Member) {
		selectedMember = member;
		showMemberDetail = true;
	}

	function closeMemberDetail() {
		showMemberDetail = false;
	}

	onMount(() => {
		fetchMembers();
	});
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
	<div class="text-center py-12">
		<p class="text-red-500">{error}</p>
		<button
			on:click={fetchMembers}
			class="mt-4 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors cursor-pointer"
		>
			{$t('errors.tryAgain')}
		</button>
	</div>
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
			<button
				class="group relative flex flex-col bg-white dark:bg-zinc-900 rounded-xl overflow-hidden border-2 border-pink-100 dark:border-pink-900/30 shadow-sm hover:shadow-lg hover:shadow-pink-500/10 hover:border-pink-300 dark:hover:border-pink-500/50 transition-all duration-300 cursor-pointer text-left"
				on:click={() => openMemberDetail(member)}
			>
				<!-- Member Photo Container -->
				<div class="relative w-full aspect-[2/3] overflow-hidden bg-gray-100 dark:bg-zinc-800">
					{#if member.img}
						<img
							src={member.img}
							alt={member.name}
							class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
							loading="lazy"
						/>
						<!-- subtle gradient overlay at bottom for depth -->
						<div
							class="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"
						></div>
					{:else}
						<div
							class="w-full h-full bg-gradient-to-br from-pink-100 to-purple-100 dark:from-pink-900/30 dark:to-purple-900/30 flex items-center justify-center"
						>
							<span class="text-2xl font-bold text-pink-400">
								{member.nickname.charAt(0)}
							</span>
						</div>
					{/if}
				</div>

				<!-- Content Area -->
				<div
					class="flex-1 p-2.5 flex flex-col items-center justify-center bg-pink-50/50 dark:bg-zinc-900 group-hover:bg-gradient-to-b group-hover:from-white group-hover:to-pink-50/50 dark:group-hover:from-zinc-900 dark:group-hover:to-pink-900/10 transition-colors relative z-10"
				>
					<h3
						class="font-bold text-gray-900 dark:text-gray-100 text-sm tracking-tight group-hover:text-pink-600 dark:group-hover:text-pink-400 transition-colors"
					>
						{member.nickname}
					</h3>
					<p
						class="text-[10px] text-gray-400 dark:text-gray-500 font-medium text-center line-clamp-1 mt-0.5 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors"
					>
						{member.name}
					</p>
				</div>
			</button>
		{/each}
	</div>
{/if}

<!-- Member Detail Modal -->
<MemberDetailModal
	show={showMemberDetail}
	member={selectedMember}
	loading={false}
	onClose={closeMemberDetail}
/>
