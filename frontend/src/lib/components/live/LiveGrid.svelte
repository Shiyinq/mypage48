<script lang="ts">
	import { fade } from 'svelte/transition';
	import { Tv, Users } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { LiveStatus } from '$lib/types';
	import LiveCard from './LiveCard.svelte';

	const { t } = useTranslation();

	interface Props {
		liveList?: LiveStatus[];
		loading?: boolean;
		initialLoading?: boolean;
		variant?: 'default' | 'theater';
		/** When set, show a multiview shortcut button above the grid */
		multiviewHref?: string;
	}

	let {
		liveList = [],
		loading = false,
		initialLoading = false,
		variant = 'default',
		multiviewHref = ''
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
			{$t('theater.live.emptyTitle')}
		</h2>
		<p class="text-slate-500 dark:text-slate-400 font-medium max-w-md">
			{$t('theater.live.empty')}
		</p>
	</div>
{:else}
	{#if multiviewHref && liveList.length > 0}
		<div class="flex justify-end mb-4 {variant === 'theater' ? 'px-0' : 'px-4'}" in:fade>
			<a
				href={multiviewHref}
				class="group relative flex items-center gap-2 px-4 py-2 rounded-2xl bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300 overflow-hidden"
			>
				<div
					class="absolute inset-0 bg-gradient-to-r from-red-500/0 via-red-500/5 to-red-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"
				></div>
				<div
					class="w-7 h-7 rounded-xl bg-red-50 dark:bg-red-500/10 flex items-center justify-center text-red-600 group-hover:bg-red-600 group-hover:text-white transition-all duration-300"
				>
					<Users size={16} />
				</div>
				<div class="flex flex-col items-start leading-none gap-0.5">
					<span
						class="text-[9px] font-black uppercase tracking-widest text-slate-400 group-hover:text-red-600 transition-colors"
						>{$t('theater.live.multiview.title')}</span
					>
					<span class="text-xs font-black tracking-tight text-slate-900 dark:text-white"
						>{$t('theater.live.switchMultiview')}</span
					>
				</div>
				<div
					class="ml-1 w-5 h-5 rounded-lg bg-slate-100 dark:bg-zinc-800 flex items-center justify-center text-[10px] font-black text-slate-500"
				>
					{liveList.length}
				</div>
			</a>
		</div>
	{/if}
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
