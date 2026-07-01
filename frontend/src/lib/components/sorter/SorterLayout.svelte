<script lang="ts">
	import { isImmersive } from '$lib/stores';
	import {
		X,
		ArrowLeft,
		ArrowUpDown,
		History,
		LayoutGrid,
		List,
		RotateCcw,
		Save,
		Check
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import NavPills from '$lib/components/navigation/NavPills.svelte';
	import { sorterNavbarStore } from '$lib/stores/sorterNavbar.svelte';
	import type { Snippet } from 'svelte';
	import { AppBackground } from '$lib/components/common';

	const { t } = useTranslation();

	interface Props {
		children: Snippet;
		basePath: string;
		backPath: string;
	}

	let { children, basePath, backPath }: Props = $props();

	// If basePath is for public jkt48, hide history
	const isPublic = $derived(basePath.includes('/jkt48'));

	const navItems = $derived.by(() => {
		const isSorterActive =
			sorterNavbarStore.pageType === 'sorter' &&
			(sorterNavbarStore.sorterState === 'sorting' || sorterNavbarStore.sorterState === 'results');

		const items: Array<{
			label: string;
			mobileLabel: string;
			href: string;
			exact: boolean;
			match?: (path: string) => boolean;
			icon: typeof ArrowUpDown;
			disabled?: boolean;
		}> = [
			{
				label: t('nav.startSorter') || 'Mulai Sorter',
				mobileLabel: t('nav.sorter') || 'Sorter',
				href: basePath,
				exact: true,
				icon: ArrowUpDown,
				disabled: isSorterActive
			}
		];

		items.push({
			label: t('nav.sorterHistory') || 'Riwayat Sorter',
			mobileLabel: t('nav.history') || 'History',
			href: `${basePath}/history`,
			exact: false,
			match: (path: string) => path.startsWith(`${basePath}/history`),
			icon: History,
			disabled: isSorterActive
		});

		return items;
	});

	$effect(() => {
		isImmersive.set(true);
		return () => {
			isImmersive.set(false);
		};
	});

	const isBackIcon = $derived(
		sorterNavbarStore.pageType === 'history-detail' ||
			(sorterNavbarStore.pageType === 'sorter' &&
				(sorterNavbarStore.sorterState === 'sorting' ||
					sorterNavbarStore.sorterState === 'results'))
	);

	const showBottomNav = $derived(
		!(
			sorterNavbarStore.pageType === 'history-detail' ||
			(sorterNavbarStore.pageType === 'sorter' &&
				(sorterNavbarStore.sorterState === 'sorting' ||
					sorterNavbarStore.sorterState === 'results'))
		)
	);

	function handleBackClick(e: MouseEvent) {
		const isSorterActive =
			sorterNavbarStore.pageType === 'sorter' &&
			(sorterNavbarStore.sorterState === 'sorting' || sorterNavbarStore.sorterState === 'results');

		if (isSorterActive) {
			e.preventDefault();
			if (sorterNavbarStore.onRestart) {
				sorterNavbarStore.onRestart();
			} else {
				goto(basePath);
			}
		} else if (isBackIcon) {
			e.preventDefault();
			window.history.back();
		}
	}
</script>

<div class="flex flex-col min-h-screen w-full relative bg-red-50/30 dark:bg-zinc-950">
	<AppBackground hideDecorationsOnMobile={true} />

	<!-- Main Sorter Navbar -->
	<div
		class="fixed top-0 left-0 right-0 w-full z-[50] border-b border-black/5 dark:border-white/5 bg-white/85 dark:bg-zinc-950/60 backdrop-blur-xl"
	>
		<div
			class="max-w-7xl mx-auto w-full h-16 flex items-center justify-between px-4 sm:px-6 lg:px-8"
		>
			<div class="flex-1 min-w-0">
				<a
					href={backPath}
					onclick={handleBackClick}
					class="flex items-center gap-2 sm:gap-3 text-slate-900 dark:text-white hover:text-red-600 transition-colors cursor-pointer inline-flex group"
				>
					<div
						class="w-8 h-8 flex items-center justify-center rounded-full bg-white dark:bg-zinc-900 shadow-sm border border-gray-200 dark:border-zinc-800 group-hover:border-red-200 dark:group-hover:border-red-900/50 group-hover:shadow-md transition-all"
					>
						{#if isBackIcon}
							<ArrowLeft
								size={16}
								class="shrink-0 text-slate-500 dark:text-slate-400 group-hover:text-red-600 dark:group-hover:text-red-600"
							/>
						{:else}
							<X
								size={16}
								class="shrink-0 text-slate-500 dark:text-slate-400 group-hover:text-red-600 dark:group-hover:text-red-600"
							/>
						{/if}
					</div>
					<span class="font-extrabold tracking-tight text-lg whitespace-nowrap"
						>Oshi <span class="text-red-600 italic">Sorter</span></span
					>
				</a>
			</div>

			<div class="hidden sm:flex items-center justify-center">
				<NavPills
					items={navItems}
					currentPath={$page.url.pathname}
					className="bg-white/50 dark:bg-zinc-900/50 border-gray-200 dark:border-zinc-800 shadow-sm shrink-0"
				/>
			</div>

			<!-- Right: Page Specific Actions (rendered from store data, no Snippets) -->
			<div class="flex-1 flex justify-end items-center">
				{#if (sorterNavbarStore.pageType === 'sorter' && sorterNavbarStore.sorterState === 'results') || sorterNavbarStore.pageType === 'history-detail'}
					<div class="flex items-center gap-2 sm:gap-3">
						{#if sorterNavbarStore.pageType === 'sorter'}
							{#if !isPublic}
								{#if !sorterNavbarStore.savedHistoryId}
									<button
										onclick={() => sorterNavbarStore.onSave?.()}
										disabled={sorterNavbarStore.isSaving}
										class="w-8 h-8 bg-green-600 hover:bg-green-700 text-white font-black rounded-full transition-all shadow-lg flex items-center justify-center cursor-pointer disabled:opacity-50"
										title={t('theater.sorter.save') || 'Save Results'}
									>
										{#if sorterNavbarStore.isSaving}
											<div
												class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"
											></div>
										{:else}
											<Save size={14} />
										{/if}
									</button>
								{:else}
									<div
										class="w-8 h-8 bg-green-500/20 text-green-600 dark:text-green-400 font-black rounded-full flex items-center justify-center cursor-default"
										title={t('theater.sorter.saveSuccess') || 'Tersimpan'}
									>
										<Check size={14} />
									</div>
								{/if}
							{/if}

							<button
								onclick={() => sorterNavbarStore.onRestart?.()}
								class="w-8 h-8 bg-white dark:bg-zinc-800 font-black rounded-full transition-all shadow-md border flex items-center justify-center cursor-pointer text-themed border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-700"
								title={t('theater.sorter.restart')}
							>
								<RotateCcw size={14} />
							</button>
						{/if}

						<div
							class="flex bg-gray-50/50 dark:bg-zinc-800/30 backdrop-blur-md rounded-full p-1 border shadow-inner border-zinc-200 dark:border-zinc-800"
						>
							<button
								onclick={() => sorterNavbarStore.onSetLayout?.('card')}
								class={`p-1.5 rounded-full transition-all cursor-pointer ${sorterNavbarStore.layoutMode === 'card' ? 'bg-red-600 text-white shadow-lg shadow-red-600/20' : 'text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}
								title={t('theater.sorter.gridView')}
							>
								<LayoutGrid size={16} />
							</button>
							<button
								onclick={() => sorterNavbarStore.onSetLayout?.('list')}
								class={`p-1.5 rounded-full transition-all cursor-pointer ${sorterNavbarStore.layoutMode === 'list' ? 'bg-red-600 text-white shadow-lg shadow-red-600/20' : 'text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}
								title={t('theater.sorter.listView')}
							>
								<List size={16} />
							</button>
						</div>
					</div>
				{:else if sorterNavbarStore.pageType === 'sorter' && sorterNavbarStore.sorterState === 'sorting'}
					<div class="flex items-center gap-2">
						<div
							class="hidden xs:flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 dark:bg-red-600/10"
						>
							<span
								class="text-[10px] font-black uppercase tracking-widest text-red-600 dark:text-red-400"
							>
								{t('theater.sorter.sorting')}
							</span>
						</div>
						<span
							class="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest"
						>
							{t('theater.sorter.questionLabel', { num: sorterNavbarStore.numQuestion })}
						</span>
					</div>
				{/if}
			</div>
		</div>
	</div>

	<!-- Content Area -->
	<div class="flex-1 relative w-full pt-16">
		{@render children()}
	</div>

	<!-- Mobile Specific Sorter Navbar (Bottom) -->
	{#if showBottomNav}
		<nav
			class="sm:hidden fixed bottom-0 left-0 right-0 z-[50] backdrop-blur-xl border-t pb-safe shadow-[0_-4px_20px_rgba(0,0,0,0.03)] dark:shadow-none transition-all duration-300 ease-in-out bg-white/85 dark:bg-zinc-950/60 border-black/5 dark:border-white/5"
		>
			<div
				class="flex h-16 items-center justify-around w-full overflow-x-auto no-scrollbar px-2 max-w-[420px] mx-auto"
			>
				{#each navItems as item}
					{@const isActive = item.match
						? item.match($page.url.pathname)
						: item.exact
							? $page.url.pathname === item.href
							: $page.url.pathname.startsWith(item.href)}
					<a
						href={item.href}
						class="flex flex-col items-center justify-center gap-0.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 active:scale-90 active:opacity-70 transition-all duration-200 group min-w-[60px] shrink-0"
					>
						<item.icon
							class={`w-5 h-5 sm:w-6 sm:h-6 transition-all ${isActive ? 'text-red-600 dark:text-red-400 scale-110' : ''}`}
						/>
						<span
							class={`text-[10px] sm:text-[11px] transition-all truncate w-full text-center ${isActive ? 'text-red-600 dark:text-red-400 font-bold' : 'font-medium'}`}
						>
							{item.mobileLabel || item.label}
						</span>
					</a>
				{/each}
			</div>
		</nav>
	{/if}
</div>
