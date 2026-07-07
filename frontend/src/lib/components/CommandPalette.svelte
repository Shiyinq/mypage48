<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { fade, scale } from 'svelte/transition';
	import {
		Search,
		Moon,
		Sun,
		Home,
		User,
		UserCheck,
		Settings,
		LogOut,
		Command,
		Laptop,
		Globe,
		Plus,
		ScanLine,
		AudioLines, // Theater
		Users, // Members
		Calendar, // Shows
		Trophy, // Achievements
		History, // History
		Music, // Admin Setlists
		MessageSquare, // Feedback
		Terminal, // Playground
		ShieldCheck, // Admin Dashboard
		Book,
		Target,
		Radio,
		LayoutGrid,
		ListOrdered,
		Share2,
		Play,
		MonitorPlay,
		Newspaper,
		Info,
		Shield,
		FileText,
		Cookie
	} from 'lucide-svelte';
	import { setTheme } from '$lib/stores';
	import { setLocale, getAllTranslations } from '$lib/i18n';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { auth } from '$lib/apis/auth';
	import { userProfile } from '$lib/stores/profile.svelte';

	interface Props {
		open?: boolean;
	}

	let { open = $bindable(false) }: Props = $props();

	const { t } = useTranslation();

	let inputEl: HTMLInputElement | undefined = $state();
	let searchQuery = $state('');
	let selectedIndex = $state(0);
	let listContainer: HTMLDivElement | undefined = $state();

	// Actions definition
	type Action = {
		id: string;
		title: string;
		translationKey?: string;
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		icon: any;
		shortcut?: string[];
		section: 'navigation' | 'theme' | 'account' | 'ticketing' | 'language' | 'admin';
		perform: () => void;
	};

	let actions: Action[] = $state([]);

	$effect(() => {
		actions = [
			// Admin (Conditional)
			...(userProfile.data?.isAdmin
				? ([
						{
							id: 'admin-dashboard',
							title: t('command.actions.adminDashboard'),
							translationKey: 'command.actions.adminDashboard',
							icon: ShieldCheck,
							section: 'admin',
							perform: () => goto('/admin')
						},
						{
							id: 'admin-users',
							title: t('command.actions.adminUsers'),
							translationKey: 'command.actions.adminUsers',
							icon: UserCheck,
							section: 'admin',
							perform: () => goto('/admin/users')
						},
						{
							id: 'admin-members',
							title: t('command.actions.adminMembers'),
							translationKey: 'command.actions.adminMembers',
							icon: Users,
							section: 'admin',
							perform: () => goto('/admin/members')
						},
						{
							id: 'admin-setlists',
							title: t('command.actions.adminSetlists'),
							translationKey: 'command.actions.adminSetlists',
							icon: Music,
							section: 'admin',
							perform: () => goto('/admin/setlists')
						},
						{
							id: 'admin-feedback',
							title: t('command.actions.adminFeedback'),
							translationKey: 'command.actions.adminFeedback',
							icon: MessageSquare,
							section: 'admin',
							perform: () => goto('/admin/feedback')
						}
					] as Action[])
				: []),

			// Navigation
			...(userProfile.data?.username
				? ([
						{
							id: 'nav-public-profile',
							title: t('command.actions.publicProfile'),
							translationKey: 'command.actions.publicProfile',
							icon: Share2,
							section: 'navigation',
							perform: () => goto(`/u/${userProfile.data?.username}`)
						}
					] as Action[])
				: []),
			{
				id: 'nav-home',
				title: t('command.actions.home'),
				translationKey: 'command.actions.home',
				icon: Home,
				section: 'navigation',
				perform: () => goto('/')
			},
			{
				id: 'nav-theater',
				title: t('command.actions.theater'),
				translationKey: 'command.actions.theater',
				icon: AudioLines,
				section: 'navigation',
				perform: () => goto('/theater')
			},
			{
				id: 'nav-members',
				title: t('command.actions.members'),
				translationKey: 'command.actions.members',
				icon: Users,
				section: 'navigation',
				perform: () => goto('/theater/members')
			},
			{
				id: 'nav-news',
				title: t('command.actions.news'),
				translationKey: 'command.actions.news',
				icon: Newspaper,
				section: 'navigation',
				perform: () => goto('/theater/news')
			},
			{
				id: 'nav-events',
				title: t('command.actions.events'),
				translationKey: 'command.actions.events',
				icon: Calendar,
				section: 'navigation',
				perform: () => goto('/theater/events')
			},
			{
				id: 'nav-calendar',
				title: t('command.actions.calendar'),
				translationKey: 'command.actions.calendar',
				icon: Calendar,
				section: 'navigation',
				perform: () => goto('/theater/events/calendar')
			},
			{
				id: 'nav-event-history',
				title: t('command.actions.eventHistory'),
				translationKey: 'command.actions.eventHistory',
				icon: History,
				section: 'navigation',
				perform: () => goto('/theater/events/history')
			},
			{
				id: 'nav-history',
				title: t('command.actions.history'),
				translationKey: 'command.actions.history',
				icon: History,
				section: 'navigation',
				perform: () => goto('/history')
			},
			{
				id: 'nav-achievements',
				title: t('command.actions.achievements'),
				translationKey: 'command.actions.achievements',
				icon: Trophy,
				section: 'navigation',
				perform: () => goto('/achievements')
			},
			{
				id: 'nav-memories',
				title: t('command.actions.memories'),
				translationKey: 'command.actions.memories',
				icon: Command, // Placeholder icon
				section: 'navigation',
				perform: () => goto('/memories')
			},
			{
				id: 'nav-profile',
				title: t('command.actions.profile'),
				translationKey: 'command.actions.profile',
				icon: User,
				section: 'navigation',
				perform: () => goto('/profile')
			},
			{
				id: 'nav-settings',
				title: t('command.actions.settings'),
				translationKey: 'command.actions.settings',
				icon: Settings,
				section: 'navigation',
				perform: () => goto('/settings')
			},
			{
				id: 'nav-playground',
				title: t('playground.title'),
				translationKey: 'playground.title',
				icon: Terminal,
				section: 'navigation',
				perform: () => goto('/playground')
			},
			{
				id: 'nav-feedback',
				title: t('command.actions.feedback'),
				translationKey: 'command.actions.feedback',
				icon: MessageSquare,
				section: 'navigation',
				perform: () => goto('/feedback')
			},
			{
				id: 'nav-journal',
				title: t('command.actions.journal'),
				translationKey: 'command.actions.journal',
				icon: Book,
				section: 'navigation',
				perform: () => goto('/journal')
			},
			{
				id: 'nav-top2shot',
				title: t('command.actions.top2shot'),
				translationKey: 'command.actions.top2shot',
				icon: Target,
				section: 'navigation',
				perform: () => goto('/top-2shot')
			},
			{
				id: 'nav-live',
				title: t('command.actions.live'),
				translationKey: 'command.actions.live',
				icon: Radio,
				section: 'navigation',
				perform: () => goto('/live')
			},
			{
				id: 'nav-multiview',
				title: t('command.actions.multiview'),
				translationKey: 'command.actions.multiview',
				icon: LayoutGrid,
				section: 'navigation',
				perform: () => goto('/live/multiview')
			},
			{
				id: 'nav-live-history',
				title: t('command.actions.liveHistory'),
				translationKey: 'command.actions.liveHistory',
				icon: History,
				section: 'navigation',
				perform: () => goto('/live/history')
			},
			{
				id: 'nav-watch-history',
				title: t('command.actions.watchHistory'),
				translationKey: 'command.actions.watchHistory',
				icon: History,
				section: 'navigation',
				perform: () => goto('/live/history/watched')
			},
			{
				id: 'nav-live-replay',
				title: t('command.actions.liveReplay'),
				translationKey: 'command.actions.liveReplay',
				icon: Play,
				section: 'navigation',
				perform: () => goto('/live/replay')
			},
			{
				id: 'nav-live-pc',
				title: t('command.actions.livePc'),
				translationKey: 'command.actions.livePc',
				icon: MonitorPlay,
				section: 'navigation',
				perform: () => goto('/live/pc')
			},
			{
				id: 'nav-sorter',
				title: t('command.actions.sorter'),
				translationKey: 'command.actions.sorter',
				icon: ListOrdered,
				section: 'navigation',
				perform: () => goto('/sorter')
			},
			{
				id: 'nav-sorter-history',
				title: t('command.actions.sorterHistory'),
				translationKey: 'command.actions.sorterHistory',
				icon: History,
				section: 'navigation',
				perform: () => goto('/sorter/history')
			},
			{
				id: 'nav-about',
				title: t('command.actions.about'),
				translationKey: 'command.actions.about',
				icon: Info,
				section: 'navigation',
				perform: () => goto('/about')
			},
			{
				id: 'nav-privacy',
				title: t('command.actions.privacy'),
				translationKey: 'command.actions.privacy',
				icon: Shield,
				section: 'navigation',
				perform: () => goto('/privacy')
			},
			{
				id: 'nav-terms',
				title: t('command.actions.terms'),
				translationKey: 'command.actions.terms',
				icon: FileText,
				section: 'navigation',
				perform: () => goto('/terms')
			},
			{
				id: 'nav-cookies',
				title: t('command.actions.cookies'),
				translationKey: 'command.actions.cookies',
				icon: Cookie,
				section: 'navigation',
				perform: () => goto('/cookies')
			},

			// Actions
			{
				id: 'ticket-scan',
				title: t('command.actions.scanTicket'),
				translationKey: 'command.actions.scanTicket',
				icon: ScanLine,
				section: 'ticketing',
				perform: () => goto('/upload?mode=scan')
			},
			{
				id: 'ticket-manual',
				title: t('command.actions.manualTicket'),
				translationKey: 'command.actions.manualTicket',
				icon: Plus,
				section: 'ticketing',
				perform: () => goto('/upload?mode=manual')
			},

			// Theme
			{
				id: 'theme-light',
				title: t('command.actions.lightMode'),
				translationKey: 'command.actions.lightMode',
				icon: Sun,
				section: 'theme',
				perform: () => setTheme('light')
			},
			{
				id: 'theme-dark',
				title: t('command.actions.darkMode'),
				translationKey: 'command.actions.darkMode',
				icon: Moon,
				section: 'theme',
				perform: () => setTheme('dark')
			},
			{
				id: 'theme-auto',
				title: t('command.actions.autoMode'),
				translationKey: 'command.actions.autoMode',
				icon: Laptop,
				section: 'theme',
				perform: () => setTheme('auto')
			},

			// Language
			{
				id: 'lang-id',
				title: t('command.actions.langId'),
				translationKey: 'command.actions.langId',
				icon: Globe,
				section: 'language',
				perform: () => setLocale('id')
			},
			{
				id: 'lang-en',
				title: t('command.actions.langEn'),
				translationKey: 'command.actions.langEn',
				icon: Globe,
				section: 'language',
				perform: () => setLocale('en')
			},
			{
				id: 'lang-ja',
				title: t('command.actions.langJa'),
				translationKey: 'command.actions.langJa',
				icon: Globe,
				section: 'language',
				perform: () => setLocale('ja')
			},

			// Account
			{
				id: 'account-logout',
				title: t('command.actions.logout'),
				translationKey: 'command.actions.logout',
				icon: LogOut,
				section: 'account',
				perform: async () => {
					await auth.logout();
					window.location.href = '/login';
				}
			}
		];
	});

	let filteredActions = $derived(
		searchQuery
			? actions.filter((a) => {
					const query = searchQuery.toLowerCase();
					return (
						a.title.toLowerCase().includes(query) ||
						(a.translationKey &&
							getAllTranslations(a.translationKey).some((t) => t.toLowerCase().includes(query)))
					);
				})
			: actions
	);

	// Reset selection when search changes or when opening
	$effect(() => {
		if (searchQuery || open) {
			selectedIndex = 0;
		}
	});

	function handleKeydown(e: KeyboardEvent) {
		// Disable on login/register/auth pages
		const path = $page.url.pathname;
		if (path === '/login' || path === '/register' || path.startsWith('/auth')) {
			return;
		}

		if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
			e.preventDefault();
			open = !open;
		}

		if (!open) return;

		if (e.key === 'Escape') {
			open = false;
		} else if (e.key === 'ArrowDown') {
			e.preventDefault();
			selectedIndex = (selectedIndex + 1) % filteredActions.length;
			scrollToSelected();
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			selectedIndex = (selectedIndex - 1 + filteredActions.length) % filteredActions.length;
			scrollToSelected();
		} else if (e.key === 'Enter') {
			e.preventDefault();
			if (filteredActions[selectedIndex]) {
				runAction(filteredActions[selectedIndex]);
			}
		}
	}

	function scrollToSelected() {
		if (!listContainer) return;
		const selectedEl = listContainer.children[selectedIndex] as HTMLElement;
		if (selectedEl) {
			// Simple scroll into view logic
			if (
				selectedEl.offsetTop + selectedEl.offsetHeight >
				listContainer.scrollTop + listContainer.offsetHeight
			) {
				listContainer.scrollTop =
					selectedEl.offsetTop + selectedEl.offsetHeight - listContainer.offsetHeight + 8; // 8px buffer
			} else if (selectedEl.offsetTop < listContainer.scrollTop) {
				listContainer.scrollTop = selectedEl.offsetTop - 8;
			}
		}
	}

	function runAction(action: Action) {
		action.perform();
		open = false;
		searchQuery = '';
	}

	// Focus input when opened
	$effect(() => {
		if (open && inputEl) {
			const el = inputEl;
			setTimeout(() => el.focus(), 10); // Tiny delay to ensure visibility
		}
	});
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<div
		class="fixed inset-0 z-[99999] flex items-start justify-center pt-[20vh] px-4"
		role="dialog"
		aria-modal="true"
	>
		<!-- Backdrop -->
		<button
			type="button"
			aria-label="Close command palette"
			class="absolute inset-0 w-full h-full bg-black/40 backdrop-blur-sm transition-opacity border-none cursor-default"
			onclick={() => (open = false)}
			transition:fade={{ duration: 150 }}
			tabindex="-1"
		></button>

		<!-- Palette Window -->
		<div
			class="glass-panel relative w-full max-w-lg rounded-xl shadow-2xl overflow-hidden flex flex-col ring-1 ring-white/10"
			transition:scale={{ duration: 150, start: 0.95 }}
		>
			<!-- Input Area -->
			<div class="flex items-center px-4 py-3 border-b border-themed gap-3">
				<Search class="w-5 h-5 text-themed-muted" />
				<input
					bind:this={inputEl}
					bind:value={searchQuery}
					type="text"
					placeholder={t('command.placeholder')}
					class="flex-1 bg-transparent border-none outline-none text-themed placeholder:text-themed-muted h-6 text-base"
				/>
				<div
					class="text-[10px] font-medium bg-black/5 dark:bg-white/5 border border-themed rounded px-1.5 py-0.5 text-themed-muted"
				>
					ESC
				</div>
			</div>

			<!-- List -->
			<div class="max-h-[300px] overflow-y-auto py-2 command-list" bind:this={listContainer}>
				{#if filteredActions.length === 0}
					<div class="px-4 py-8 text-center text-themed-muted text-sm">
						{t('command.noResults')}
					</div>
				{:else}
					{#each filteredActions as action, i}
						<button
							class="w-full text-left px-4 py-2.5 flex items-center gap-3 text-sm transition-colors
                                   {i === selectedIndex
								? 'bg-red-500/10 text-red-600 dark:text-red-400 border-l-2 border-red-500'
								: 'text-themed-secondary border-l-2 border-transparent hover:bg-black/5 dark:hover:bg-white/5'} cursor-pointer"
							onclick={() => runAction(action)}
							onmouseenter={() => (selectedIndex = i)}
						>
							<action.icon
								class="w-4 h-4 {i === selectedIndex ? 'text-red-500' : 'text-themed-muted'}"
							/>
							<span class="flex-1">{action.title}</span>
							<span class="text-xs text-themed-muted capitalize"
								>{t(`command.sections.${action.section}`)}</span
							>
						</button>
					{/each}
				{/if}
			</div>

			<!-- Footer -->
			<div
				class="px-4 py-2 bg-black/5 dark:bg-white/5 border-t border-themed text-[10px] text-themed-muted flex justify-between"
			>
				<span>{t('command.footer.navigate')} <span class="text-themed-secondary">↑↓</span></span>
				<span>{t('command.footer.select')} <span class="text-themed-secondary">↵</span></span>
			</div>
		</div>
	</div>
{/if}

<style>
	/* Custom scrollbar for the list */
	.command-list::-webkit-scrollbar {
		width: 6px;
	}
	.command-list::-webkit-scrollbar-track {
		background: transparent;
	}
	.command-list::-webkit-scrollbar-thumb {
		background: var(--color-scrollbar, rgba(150, 150, 150, 0.3));
		border-radius: 3px;
	}
	.command-list::-webkit-scrollbar-thumb:hover {
		background: var(--color-scrollbar-hover, rgba(150, 150, 150, 0.5));
	}
</style>
