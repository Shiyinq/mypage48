<script lang="ts">
	import { fade } from 'svelte/transition';
	import { Tv } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { LiveStatus } from '$lib/types';
	import LiveCard from './LiveCard.svelte';

	const { t } = useTranslation();

	interface Props {
		liveList?: LiveStatus[];
		loading?: boolean;
		initialLoading?: boolean;
		variant?: 'default' | 'theater' | 'public';
	}

	let {
		liveList = [],
		loading = false,
		initialLoading = false,
		variant = 'default'
	}: Props = $props();
</script>

{#if (initialLoading || loading) && liveList.length === 0}
	<div
		class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 {variant ===
		'theater'
			? 'px-0'
			: 'px-0 sm:px-4'}"
	>
		{#each Array(10)}
			<div
				class="aspect-[3/4] bg-slate-100 dark:bg-zinc-900 rounded-xl overflow-hidden relative shadow-sm border border-slate-100 dark:border-zinc-800"
			>
				<div
					class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 dark:via-white/5 to-transparent -translate-x-full animate-shimmer"
				></div>
				<div class="absolute bottom-0 left-0 right-0 p-4 space-y-2">
					<div class="h-4 w-2/3 bg-slate-200 dark:bg-zinc-800 rounded"></div>
					<div class="h-3 w-1/2 bg-slate-200 dark:bg-zinc-800 rounded"></div>
				</div>
			</div>
		{/each}
	</div>
{:else if liveList.length === 0}
	<div class="flex flex-col items-center justify-center py-24 text-center px-6" in:fade>
		<div
			class="w-24 h-24 rounded-full bg-slate-100 dark:bg-zinc-900 flex items-center justify-center mb-6 text-slate-300 dark:text-zinc-800"
		>
			<Tv size={48} />
		</div>
		<h2 class="text-2xl font-black text-slate-900 dark:text-white mb-2 italic">
			{t('theater.live.emptyTitle')}
		</h2>
		<p class="text-slate-500 dark:text-slate-400 font-medium max-w-md">
			{t('theater.live.empty')}
		</p>
	</div>
{:else}
	<div
		class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 {variant ===
		'theater'
			? 'px-0'
			: 'px-0 sm:px-4'}"
	>
		{#each liveList as stream, i (stream.platform + (stream.room_id || stream.live_id))}
			<LiveCard {stream} {i} {variant} />
		{/each}
	</div>
{/if}

<style>
	@keyframes shimmer {
		100% {
			transform: translateX(100%);
		}
	}
	.animate-shimmer {
		animation: shimmer 2s infinite;
	}
</style>
