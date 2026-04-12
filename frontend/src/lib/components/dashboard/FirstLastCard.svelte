<script lang="ts">
	import { Calendar, Maximize2, Star, Camera } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		/**
		 * First & Last Item Card (Generic for Shows and 2-Shots)
		 */
		title: string;
		type: 'theater' | 'twoShot';
		loading?: boolean;
		onExpand: () => void;
		// Data items
		first: {
			image?: string | null;
			title: string;
			subtitle?: string | null;
			date: string;
			detail?: string;
		} | null;
		last: {
			image?: string | null;
			title: string;
			subtitle?: string | null;
			date: string;
			detail?: string;
		} | null;
	}

	let { title, type, loading = false, onExpand, first, last }: Props = $props();

	let theme = $derived(type === 'theater' ? 'purple' : 'pink');
	let PlaceholderIcon = $derived(type === 'theater' ? Star : Camera);

	let themeClasses = $derived(
		theme === 'purple'
			? {
					bg: 'bg-purple-50/20 dark:bg-transparent',
					border: 'border-purple-100 dark:border-purple-500/20',
					iconBg: 'bg-purple-100 dark:bg-purple-800/40',
					text: 'text-purple-500',
					textLight: 'text-purple-400',
					hoverText: 'hover:text-purple-600 dark:hover:text-purple-300',
					hoverBg: 'hover:bg-purple-100 dark:hover:bg-purple-800/30',
					date: 'text-purple-600 dark:text-purple-400',
					divider: 'bg-purple-200 dark:bg-purple-800/30',
					placeholderText: 'text-purple-300',
					placeholderBg: 'bg-gray-200 dark:bg-gray-800',
					placeholderEmptyBg: 'bg-gray-50 dark:bg-gray-800/50',
					placeholderEmptyText: 'text-purple-200 dark:text-purple-800/30',
					label: 'text-gray-400'
				}
			: {
					bg: 'bg-pink-50/20 dark:bg-transparent',
					border: 'border-pink-100 dark:border-pink-500/20',
					iconBg: 'bg-pink-50 dark:bg-pink-800/40',
					text: 'text-pink-400', // Note: 2shot uses pink-400 in code
					textLight: 'text-pink-300',
					hoverText: 'hover:text-pink-500 dark:hover:text-pink-300',
					hoverBg: 'hover:bg-pink-50 dark:hover:bg-pink-800/30',
					date: 'text-pink-400',
					divider: 'bg-pink-200 dark:bg-pink-800/30',
					placeholderText: 'text-pink-300',
					placeholderBg: 'bg-gray-200 dark:bg-gray-800',
					placeholderEmptyBg: 'bg-gray-50 dark:bg-gray-800/50',
					placeholderEmptyText: 'text-pink-200 dark:text-pink-800/30',
					label: 'text-gray-400'
				}
	);

	let labels = $derived(
		type === 'theater'
			? { first: $t('dashboard.theater.first'), last: $t('dashboard.theater.last') }
			: { first: $t('dashboard.twoShot.first'), last: $t('dashboard.twoShot.last') }
	);
</script>

<div
	class={`glass-card rounded-3xl p-5 relative overflow-hidden group hover:shadow-lg transition-all duration-300 sm:col-span-2 ${themeClasses.bg} ${themeClasses.border}`}
>
	<div class="flex justify-between items-start mb-4">
		<div class={`flex items-center gap-2 ${themeClasses.text}`}>
			<div class={`p-1.5 rounded-lg ${themeClasses.iconBg}`}>
				<Calendar class="w-4 h-4" />
			</div>
			<span class="font-bold text-xs tracking-wider text-gray-800 dark:text-gray-100">
				{title}
			</span>
		</div>
		<button
			onclick={onExpand}
			class={`p-2 -mr-2 -mt-2 ${themeClasses.textLight} ${themeClasses.hoverText} ${themeClasses.hoverBg} rounded-full transition-colors cursor-pointer`}
			title="View Fullscreen"
		>
			<Maximize2 class="w-4 h-4" />
		</button>
	</div>

	{#if loading}
		<div class="grid grid-cols-2 gap-4">
			<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
			{#each Array(2) as _}
				<div class="space-y-2">
					<div class="h-3 w-12 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
					<div class="h-5 w-24 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
					<div class="h-3 w-20 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
				</div>
			{/each}
		</div>
	{:else}
		<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">
			<!-- Divider -->
			<div
				class={`hidden sm:block absolute left-1/2 top-0 bottom-0 w-px ${themeClasses.divider}`}
			></div>

			<!-- First Item -->
			<div class="flex items-start gap-3">
				{#if first}
					<div
						class={`w-12 h-16 rounded-lg overflow-hidden flex-shrink-0 shadow-sm border ${themeClasses.border} ${themeClasses.placeholderBg}`}
					>
						{#if first.image}
							<img src={first.image} alt={first.title} class="w-full h-full object-cover" />
						{:else}
							<div
								class={`w-full h-full flex items-center justify-center ${themeClasses.placeholderText}`}
							>
								<PlaceholderIcon class="w-4 h-4" />
							</div>
						{/if}
					</div>
					<div class="min-w-0 flex-1">
						<p
							class={`text-[10px] font-bold uppercase tracking-wider mb-0.5 ${themeClasses.label}`}
						>
							{labels.first}
						</p>
						<p class="font-bold text-themed text-sm leading-tight truncate">
							{first.title}
						</p>
						<p class={`text-xs font-bold ${themeClasses.date}`}>
							{first.date}
						</p>
						{#if first.detail}
							<p class="text-[10px] text-gray-500 mt-0.5">
								{first.detail}
							</p>
						{/if}
					</div>
				{:else}
					<div
						class={`w-12 h-16 rounded-lg overflow-hidden flex-shrink-0 shadow-sm border ${themeClasses.border} ${themeClasses.placeholderEmptyBg}`}
					>
						<div
							class={`w-full h-full flex items-center justify-center ${themeClasses.placeholderEmptyText}`}
						>
							<PlaceholderIcon class="w-4 h-4" />
						</div>
					</div>
					<div class="min-w-0 flex-1">
						<p
							class={`text-[10px] font-bold uppercase tracking-wider mb-0.5 ${themeClasses.label}`}
						>
							{labels.first}
						</p>
						<p class="font-bold text-themed text-sm leading-tight truncate">-</p>
						<p class={`text-xs font-bold ${themeClasses.date}`}>-</p>
						<p class="text-[10px] text-gray-500 mt-0.5">-</p>
					</div>
				{/if}
			</div>

			<!-- Last Item -->
			<div class="flex items-start gap-3 relative sm:pl-2">
				{#if last}
					<div
						class={`w-12 h-16 rounded-lg overflow-hidden flex-shrink-0 shadow-sm border ${themeClasses.border} ${themeClasses.placeholderBg}`}
					>
						{#if last.image}
							<img src={last.image} alt={last.title} class="w-full h-full object-cover" />
						{:else}
							<div
								class={`w-full h-full flex items-center justify-center ${themeClasses.placeholderText}`}
							>
								<PlaceholderIcon class="w-4 h-4" />
							</div>
						{/if}
					</div>
					<div class="min-w-0 flex-1">
						<p
							class={`text-[10px] font-bold uppercase tracking-wider mb-0.5 ${themeClasses.label}`}
						>
							{labels.last}
						</p>
						<p class="font-bold text-themed text-sm leading-tight truncate">
							{last.title}
						</p>
						<p class={`text-xs font-bold ${themeClasses.date}`}>
							{last.date}
						</p>
						{#if last.detail}
							<p class="text-[10px] text-gray-500 mt-0.5">
								{last.detail}
							</p>
						{/if}
					</div>
				{:else}
					<div
						class={`w-12 h-16 rounded-lg overflow-hidden flex-shrink-0 shadow-sm border ${themeClasses.border} ${themeClasses.placeholderEmptyBg}`}
					>
						<div
							class={`w-full h-full flex items-center justify-center ${themeClasses.placeholderEmptyText}`}
						>
							<PlaceholderIcon class="w-4 h-4" />
						</div>
					</div>
					<div class="min-w-0 flex-1">
						<p
							class={`text-[10px] font-bold uppercase tracking-wider mb-0.5 ${themeClasses.label}`}
						>
							{labels.last}
						</p>
						<p class="font-bold text-themed text-sm leading-tight truncate">-</p>
						<p class={`text-xs font-bold ${themeClasses.date}`}>-</p>
						<p class="text-[10px] text-gray-500 mt-0.5">-</p>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
