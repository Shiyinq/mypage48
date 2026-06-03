<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import { liveHistoryFilterStore } from '$lib/stores/liveHistoryFilter.svelte';
	import { History, Trophy } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { isImmersive } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { spring } from 'svelte/motion';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { EmptyState } from '$lib/components';
	import HistoryTopBar from '$lib/components/live/history/shared/HistoryTopBar.svelte';
	import LiveRankingSkeleton from '$lib/components/live/history/shared/LiveRankingSkeleton.svelte';
	import LiveRankingCard from '$lib/components/live/history/shared/LiveRankingCard.svelte';

	const basePath = '/jkt48/live/history/members';

	let scrollY = $state(0);
	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));

	const { t } = useTranslation();

	let rankingList = $derived(liveHistoryStore.globalMembersRanking);
	let pagination = $derived(liveHistoryStore.globalRankingPagination);
	let isLoading = $derived(liveHistoryStore.isLoading);
	let hasMore = $derived(pagination.current_page < pagination.last_page);

	let mounted = $state(false);

	onMount(() => {
		mounted = true;
		isImmersive.set(true);
		document.body.style.overflow = 'hidden';
		loadRanking(1, true);
		membersStore.load({ limit: 100 });

		return () => {
			isImmersive.set(false);
			document.body.style.overflow = '';
		};
	});

	async function loadRanking(page: number, force: boolean = false) {
		await liveHistoryStore.loadGlobalMembersRanking(page, force);
	}

	$effect(() => {
		const _trigger =
			liveHistoryFilterStore.filterType +
			liveHistoryFilterStore.customRange.start +
			liveHistoryFilterStore.customRange.end;
		if (mounted) {
			untrack(() => {
				loadRanking(1, true);
			});
		}
	});

	function handleIntersect() {
		if (isLoading || !hasMore) return;
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

<SEO title={t('liveHistory.globalRankingTitle')} path={basePath} />

<div
	role="presentation"
	class="fixed inset-0 bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 flex flex-col overflow-hidden z-[9999]"
	onmousemove={(e) => {
		const { clientX, clientY } = e;
		const { innerWidth, innerHeight } = window;
		mouse.set({ x: clientX / innerWidth - 0.5, y: clientY / innerHeight - 0.5 });
	}}
>
	<AnimatedBackground interactive={true} bind:mouse bind:scrollY />

	<HistoryTopBar
		title={t('liveHistory.jkt48RankingTitle')}
		subtitle={t('liveHistory.globalRankingSubtitle')}
		icon={Trophy}
		iconColor="text-purple-500"
		showDateFilter={true}
	/>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-32 relative z-10">
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
							href={`${basePath}/${item.member_id}`}
							mode="global"
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
