<script lang="ts">
	import { untrack, onMount } from 'svelte';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import { liveHistoryFilterStore } from '$lib/stores/liveHistoryFilter.svelte';
	import { Trophy, History } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { isImmersive } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { spring } from 'svelte/motion';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { EmptyState } from '$lib/components';
	import HistoryTopBar from '$lib/components/live/history/shared/HistoryTopBar.svelte';
	import LiveRankingSkeleton from '$lib/components/live/history/shared/LiveRankingSkeleton.svelte';
	import LiveRankingCard from '$lib/components/live/history/shared/LiveRankingCard.svelte';

	let scrollY = $state(0);
	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));

	const { t } = useTranslation();

	let rankingList = $derived(liveHistoryStore.membersRanking);
	let pagination = $derived(liveHistoryStore.rankingPagination);
	let isLoading = $derived(liveHistoryStore.isLoading);
	let hasMore = $derived(pagination.current_page < pagination.last_page);

	let mounted = $state(false);

	onMount(() => {
		mounted = true;
		isImmersive.set(true);
		document.body.style.overflow = 'hidden';
		membersStore.load({ limit: 100 });

		return () => {
			isImmersive.set(false);
			document.body.style.overflow = '';
		};
	});

	$effect(() => {
		// React to dateRange changes
		const _range = liveHistoryFilterStore.dateRange;
		if (mounted) {
			untrack(() => {
				loadRanking(1);
			});
		}
	});

	async function loadRanking(page: number) {
		await liveHistoryStore.loadMembersRanking(page);
	}

	function handleIntersect() {
		if (!mounted || isLoading || !hasMore) return;
		loadRanking(pagination.current_page + 1);
	}

	function getMemberImageStr(memberId: string, memberName?: string) {
		const member = membersStore.list.find(
			(m) =>
				String(m.id) === String(memberId) ||
				(memberName && m.name === memberName) ||
				(memberName && m.nickname === memberName) ||
				(m.socials?.idn_app && String(memberId).includes(m.socials.idn_app)) ||
				(m.socials?.showroom && String(memberId) === String(m.socials.showroom))
		);
		return member?.img || '';
	}
</script>

<SEO title={t('liveHistory.rankingTitle')} path="/theater/live/history/watched/members" />

<div
	role="presentation"
	class="fixed inset-0 bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 flex flex-col overflow-hidden z-[9999]"
	onmousemove={(e) => {
		const { clientX, clientY } = e;
		const { innerWidth, innerHeight } = window;
		const x = clientX / innerWidth - 0.5;
		const y = clientY / innerHeight - 0.5;
		mouse.set({ x, y });
	}}
>
	<AppBackground interactive={true} bind:mouse bind:scrollY />

	<HistoryTopBar
		title={t('liveHistory.rankingTitle')}
		subtitle={t('liveHistory.rankingSubtitle')}
		icon={Trophy}
		iconColor="text-purple-500"
		showDateFilter={true}
	/>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 pb-32 relative z-10">
			{#if isLoading && rankingList.length === 0}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each Array(6) as _}
						<LiveRankingSkeleton />
					{/each}
				</div>
			{:else if rankingList.length === 0}
				<EmptyState
					icon={History}
					title={t('liveHistory.noHistory')}
					description={t('liveHistory.noHistoryDesc')}
				/>
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each rankingList as item, index}
						<LiveRankingCard
							{item}
							{index}
							href={`/theater/live/history/watched/${item.member_id}`}
							mode="watched"
							memberImage={getMemberImageStr(item.member_id, item.member_name)}
							timesLabel={t('liveHistory.times')}
						/>
					{/each}
				</div>

				{#if hasMore}
					<div
						use:infiniteScroll
						onintersect={handleIntersect}
						class="w-full py-6 flex justify-center"
					>
						{#if isLoading}
							<div
								class="w-8 h-8 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin"
							></div>
						{/if}
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
