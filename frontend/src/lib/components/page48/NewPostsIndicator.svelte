<script lang="ts">
	import { ArrowUp } from 'lucide-svelte';
	import { portal } from '$lib/actions/portal';
	import { t } from '$lib/i18n';

	interface Props {
		/** How many new posts are waiting. Renders nothing when zero. */
		count: number;
		/** Up to a few author avatars shown inside the floating pill. */
		avatars: string[];
		/** True when the timeline is scrolled to the very top. */
		atTop: boolean;
		onApply: () => void;
		/**
		 * `feed` (default) puts an inline row above the first post when at the top;
		 * `overlay` keeps a floating pill in both states, for grids where a
		 * full-width row would not line up with the layout.
		 */
		variant?: 'feed' | 'overlay';
	}

	let { count, avatars, atTop, onApply, variant = 'feed' }: Props = $props();
</script>

{#snippet pillContent(withArrow: boolean)}
	{#if withArrow}
		<ArrowUp size={16} class="shrink-0" />
	{/if}
	{#if withArrow && avatars.length > 0}
		<span class="flex items-center -space-x-2">
			{#each avatars as avatar, i (i)}
				<img
					src={avatar}
					alt=""
					class="h-6 w-6 rounded-full border-2 border-red-600 object-cover"
				/>
			{/each}
		</span>
	{/if}
	<span class="text-[13px] font-semibold">
		{withArrow ? t('page48.feed.posted') : t('page48.feed.newPosts', { count })}
	</span>
{/snippet}

{#if count > 0}
	{#if variant === 'overlay' || !atTop}
		<!--
			Floating pill. Portalled to <body> so `position: fixed` stays
			viewport-relative — an ancestor with `backdrop-filter` (the feed's
			backdrop blur) would otherwise become its containing block and make
			the pill scroll away behind the navbar.
		-->
		<div
			use:portal
			class="pointer-events-none fixed left-0 right-0 top-20 z-[60] flex justify-center"
		>
			<button
				type="button"
				class="pointer-events-auto flex items-center gap-2 rounded-full bg-red-600 px-3.5 py-2 text-white shadow-lg transition-transform cursor-pointer hover:scale-105 active:scale-95"
				onclick={onApply}
				aria-label={t('page48.feed.newPosts', { count })}
			>
				{@render pillContent(!atTop)}
			</button>
		</div>
	{:else}
		<!-- Feed, at the very top: an inline row above the first post. -->
		<button
			type="button"
			class="w-full py-3.5 text-center text-[14px] font-semibold text-blue-500 transition-colors cursor-pointer hover:bg-blue-50/70 dark:hover:bg-blue-500/10"
			onclick={onApply}
		>
			{t('page48.feed.newPosts', { count })}
		</button>
	{/if}
{/if}
