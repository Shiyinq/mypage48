<script lang="ts">
	import TrendingTags from './TrendingTags.svelte';
	import ActiveUsers from './ActiveUsers.svelte';
	import MemberXTags from './MemberXTags.svelte';
	import SearchBox from './SearchBox.svelte';

	interface Props {
		/** Hide the Trending card (e.g. on the trending page, where it would be redundant). */
		showTrending?: boolean;
		/** Hide the search box where the page already provides its own input. */
		showSearch?: boolean;
	}

	let { showTrending = true, showSearch = true }: Props = $props();
</script>

<!-- Left: member hashtags (fixed so it stays put while the feed scrolls) -->
<aside class="hidden xl:block fixed top-20 right-[calc(50%_+_326px)] w-[300px] z-40">
	<MemberXTags />
</aside>

<!-- Right: trending tags + most active users (fixed so they stay put while the feed scrolls) -->
<aside
	class="hidden xl:block fixed top-20 left-[calc(50%_+_326px)] w-[300px] z-40 max-h-[calc(100vh-6rem)] overflow-y-auto no-scrollbar space-y-4 pb-4"
>
	{#if showSearch}
		<SearchBox />
	{/if}
	{#if showTrending}
		<TrendingTags />
	{/if}
	<ActiveUsers />
</aside>
