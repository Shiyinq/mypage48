<script lang="ts">
	import TrendingTags from './TrendingTags.svelte';
	import MemberXTags from './MemberXTags.svelte';
</script>

<!-- Left: member hashtags (fixed so it stays put while the feed scrolls) -->
<aside class="hidden xl:block fixed top-20 right-[calc(50%_+_326px)] w-[300px] z-40">
	<MemberXTags />
</aside>

<!-- Right: trending tags (fixed so it stays put while the feed scrolls) -->
<aside
	class="hidden xl:block fixed top-20 left-[calc(50%_+_326px)] w-[300px] z-40 max-h-[calc(100vh-6rem)] overflow-y-auto no-scrollbar space-y-4 pb-4"
>
	<TrendingTags />
</aside>
