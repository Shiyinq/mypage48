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
	}

	let { count, avatars, atTop, onApply }: Props = $props();
</script>

{#if count > 0}
	{#if atTop}
		<!-- At the very top: an inline row above the first post. -->
		<button
			type="button"
			class="w-full py-3.5 text-center text-[14px] font-semibold text-blue-500 transition-colors cursor-pointer hover:bg-blue-50/70 dark:hover:bg-blue-500/10"
			onclick={onApply}
		>
			{t('page48.feed.newPosts', { count })}
		</button>
	{:else}
		<!--
			Scrolled down: a floating pill pinned over the timeline. Portalled to
			<body> so `position: fixed` stays viewport-relative — an ancestor with
			`backdrop-filter` (the feed's backdrop blur) would otherwise become its
			containing block and make the pill scroll away behind the navbar.
		-->
		<div
			use:portal
			class="pointer-events-none fixed left-0 right-0 top-20 z-[60] flex justify-center"
		>
			<button
				type="button"
				class="pointer-events-auto flex items-center gap-2 rounded-full bg-red-600 px-3 py-1.5 text-white shadow-lg transition-transform cursor-pointer hover:scale-105 active:scale-95"
				onclick={onApply}
				aria-label={t('page48.feed.newPosts', { count })}
			>
				<ArrowUp size={16} class="shrink-0" />
				{#if avatars.length > 0}
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
				<span class="text-[13px] font-semibold">{t('page48.feed.posted')}</span>
			</button>
		</div>
	{/if}
{/if}
