<script lang="ts">
	import { adminStore } from '$lib/stores/admin.svelte';
	import { onMount } from 'svelte';
	import {
		Users,
		UserCheck,
		ShieldCheck,
		MessageSquare,
		Activity,
		Globe,
		Ticket,
		Camera,
		BookOpen,
		Heart,
		Wallet,
		Star,
		Music,
		Calendar,
		MonitorPlay,
		Radio,
		Newspaper,
		Gift,
		Video,
		ListOrdered
	} from 'lucide-svelte';
	import AdminDashboardSkeleton from '$lib/components/skeletons/AdminDashboardSkeleton.svelte';

	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	onMount(() => {
		adminStore.loadDashboardStats();
	});

	let usersStats = $derived(adminStore.dashboardStats.users);
	let mypageStats = $derived(adminStore.dashboardStats.mypage);
	let theaterStats = $derived(adminStore.dashboardStats.theater);

	function formatCurrency(amount: number) {
		return new Intl.NumberFormat('id-ID', {
			style: 'currency',
			currency: 'IDR',
			maximumFractionDigits: 0
		}).format(amount);
	}
</script>

<div class="space-y-8 pb-10">
	{#if adminStore.isDashboardStatsLoading || !usersStats || !mypageStats || !theaterStats}
		<AdminDashboardSkeleton />
	{:else}
		<!-- DATA USERS SECTION -->
		<section>
			<div class="flex items-center gap-3 mb-4">
				<div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-xl text-blue-500">
					<Users class="w-6 h-6" />
				</div>
				<h2 class="text-xl font-bold text-gray-900 dark:text-white">
					{t('admin.dashboard.stats.dataUsers')}
				</h2>
			</div>

			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
				<!-- Total Users -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-blue-50 dark:bg-blue-500/10 rounded-xl text-blue-500 shrink-0">
							<Users class="w-6 h-6" />
						</div>
						<div>
							<div class="flex items-baseline gap-2 mb-0.5">
								<div class="text-2xl font-black text-gray-900 dark:text-white leading-none">
									{usersStats.total_users}
								</div>
								<span class="text-xs font-medium text-gray-400"
									>{t('admin.dashboard.stats.totalUsers')}</span
								>
							</div>
							<div
								class="flex items-center gap-1 text-[11px] text-blue-500 dark:text-blue-400 font-medium mt-1"
							>
								{t('admin.dashboard.stats.joinedToday', { count: usersStats.users_joined_today })}
							</div>
						</div>
					</div>
				</div>

				<!-- Active & Public -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-green-50 dark:bg-green-500/10 rounded-xl text-green-500 shrink-0">
							<Activity class="w-6 h-6" />
						</div>
						<div>
							<div class="flex items-baseline gap-2 mb-1">
								<span class="text-2xl font-black text-gray-900 dark:text-white leading-none"
									>{usersStats.active_users_last_days}</span
								>
								<span class="text-xs font-medium text-gray-400"
									>{t('admin.dashboard.stats.active7d')}</span
								>
							</div>
							<div
								class="flex items-center gap-1 text-[11px] font-medium text-gray-500 dark:text-gray-400 mt-0.5"
							>
								<Globe class="w-3 h-3" />
								{usersStats.public_profiles}
								{t('admin.dashboard.stats.publicProfiles')}
							</div>
						</div>
					</div>
				</div>

				<!-- Verified/Unverified -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-purple-50 dark:bg-purple-500/10 rounded-xl text-purple-500 shrink-0">
							<UserCheck class="w-6 h-6" />
						</div>
						<div class="flex-1 space-y-1.5">
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
									<div class="w-1.5 h-1.5 rounded-full bg-green-500"></div>
									{t('admin.dashboard.stats.verified')}
								</div>
								<span class="font-bold text-gray-900 dark:text-white text-sm"
									>{usersStats.verified_users}</span
								>
							</div>
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
									<div class="w-1.5 h-1.5 rounded-full bg-yellow-500"></div>
									{t('admin.dashboard.stats.unverified')}
								</div>
								<span class="font-bold text-gray-900 dark:text-white text-sm"
									>{usersStats.unverified_users}</span
								>
							</div>
						</div>
					</div>
				</div>

				<!-- Admins & Feedback -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-orange-50 dark:bg-orange-500/10 rounded-xl text-orange-500 shrink-0">
							<ShieldCheck class="w-6 h-6" />
						</div>
						<div class="flex-1 space-y-1.5">
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
									<ShieldCheck class="w-3.5 h-3.5" />
									{t('admin.dashboard.stats.admins')}
								</div>
								<span class="font-bold text-gray-900 dark:text-white text-sm"
									>{usersStats.total_admins}</span
								>
							</div>
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
									<MessageSquare class="w-3.5 h-3.5" />
									{t('admin.dashboard.stats.feedback')}
								</div>
								<span class="font-bold text-gray-900 dark:text-white text-sm"
									>{usersStats.total_feedback}</span
								>
							</div>
						</div>
					</div>
				</div>
			</div>
		</section>

		<!-- DATA MYPAGE SECTION -->
		<section>
			<div class="flex items-center gap-3 mb-4 mt-8">
				<div class="p-2 bg-pink-100 dark:bg-pink-900/30 rounded-xl text-pink-500">
					<Heart class="w-6 h-6" />
				</div>
				<h2 class="text-xl font-bold text-gray-900 dark:text-white">
					{t('admin.dashboard.stats.dataMyPage')}
				</h2>
			</div>

			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
				<!-- Tickets -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-pink-50 dark:bg-pink-500/10 rounded-xl text-pink-500 shrink-0">
							<Ticket class="w-6 h-6" />
						</div>
						<div>
							<div class="text-2xl font-black text-gray-900 dark:text-white leading-none mb-1">
								{mypageStats.total_tickets}
							</div>
							<div class="text-xs font-medium text-gray-500 dark:text-gray-400">
								{t('admin.dashboard.stats.ticketsLogged')}
							</div>
						</div>
					</div>
				</div>

				<!-- 2-Shot -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-indigo-50 dark:bg-indigo-500/10 rounded-xl text-indigo-500 shrink-0">
							<Camera class="w-6 h-6" />
						</div>
						<div>
							<div class="text-2xl font-black text-gray-900 dark:text-white leading-none mb-1">
								{mypageStats.total_2shot}
							</div>
							<div class="text-xs font-medium text-gray-500 dark:text-gray-400">
								{t('admin.dashboard.stats.total2Shot')}
							</div>
						</div>
					</div>
				</div>

				<!-- Journals & Favorites -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-teal-50 dark:bg-teal-500/10 rounded-xl text-teal-500 shrink-0">
							<BookOpen class="w-6 h-6" />
						</div>
						<div class="flex-1 space-y-1.5">
							<div class="flex items-center gap-4">
								<div class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
									<BookOpen class="w-3.5 h-3.5" />
									{t('admin.dashboard.stats.journals')}
									<span class="font-bold text-gray-900 dark:text-white text-sm ml-0.5"
										>{mypageStats.total_journal}</span
									>
								</div>
								<div class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
									<Star class="w-3.5 h-3.5 text-yellow-400" />
									{t('admin.dashboard.stats.favorites')}
									<span class="font-bold text-gray-900 dark:text-white text-sm ml-0.5"
										>{mypageStats.total_favorites}</span
									>
								</div>
							</div>
							<div class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
								<ListOrdered class="w-3.5 h-3.5 text-blue-400" />
								{t('admin.dashboard.stats.sorters')}
								<span class="font-bold text-gray-900 dark:text-white text-sm ml-0.5"
									>{mypageStats.total_sorter}</span
								>
							</div>
						</div>
					</div>
				</div>

				<!-- Money Spent -->
				<div
					class="bg-gradient-to-br from-green-400 to-emerald-600 p-4 rounded-2xl shadow-md text-white"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-white/20 rounded-xl shrink-0">
							<Wallet class="w-6 h-6" />
						</div>
						<div class="overflow-hidden">
							<div
								class="text-xl font-black leading-none mb-1 truncate"
								title={formatCurrency(mypageStats.total_money_spent_idr)}
							>
								{formatCurrency(mypageStats.total_money_spent_idr)}
							</div>
							<div class="text-xs font-medium text-green-50 truncate">
								{t('admin.dashboard.stats.totalEstSpent')}
							</div>
						</div>
					</div>
				</div>
			</div>
		</section>

		<!-- DATA THEATER SECTION -->
		<section>
			<div class="flex items-center gap-3 mb-4 mt-8">
				<div class="p-2 bg-red-100 dark:bg-red-900/30 rounded-xl text-red-500">
					<Star class="w-6 h-6" />
				</div>
				<h2 class="text-xl font-bold text-gray-900 dark:text-white">
					{t('admin.dashboard.stats.dataTheater')}
				</h2>
			</div>

			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
				<!-- Members -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-red-50 dark:bg-red-500/10 rounded-xl text-red-500 shrink-0">
							<Users class="w-6 h-6" />
						</div>
						<div>
							<div class="flex items-baseline gap-2 mb-0.5">
								<div class="text-2xl font-black text-gray-900 dark:text-white leading-none">
									{theaterStats.total_members_jkt}
								</div>
								<span class="text-xs font-medium text-gray-400"
									>{t('admin.dashboard.stats.members')}</span
								>
							</div>
							<div
								class="flex items-center gap-3 text-[11px] text-gray-500 dark:text-gray-400 mt-1"
							>
								<span class="flex items-center gap-1.5"
									><div class="w-1.5 h-1.5 rounded-full bg-green-500"></div>
									{theaterStats.active_members_count}
									{t('admin.dashboard.stats.active')}</span
								>
								<span class="flex items-center gap-1.5"
									><div class="w-1.5 h-1.5 rounded-full bg-gray-400"></div>
									{theaterStats.graduated_members_count}
									{t('admin.dashboard.stats.grad')}</span
								>
							</div>
						</div>
					</div>
				</div>

				<!-- Setlists -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-purple-50 dark:bg-purple-500/10 rounded-xl text-purple-500 shrink-0">
							<Music class="w-6 h-6" />
						</div>
						<div>
							<div class="flex items-baseline gap-2 mb-0.5">
								<div class="text-2xl font-black text-gray-900 dark:text-white leading-none">
									{theaterStats.total_setlists}
								</div>
								<span class="text-xs font-medium text-gray-400"
									>{t('admin.dashboard.stats.setlists')}</span
								>
							</div>
							<div
								class="flex items-center gap-3 text-[11px] text-gray-500 dark:text-gray-400 mt-1"
							>
								<span class="flex items-center gap-1"
									><div class="w-1.5 h-1.5 rounded-full bg-green-500"></div>
									{theaterStats.active_setlists_count}
									{t('admin.dashboard.stats.active')}</span
								>
								<span class="flex items-center gap-1"
									><div class="w-1.5 h-1.5 rounded-full bg-gray-400"></div>
									{theaterStats.inactive_setlists_count}
									{t('admin.dashboard.stats.inactive')}</span
								>
							</div>
						</div>
					</div>
				</div>

				<!-- Shows -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-indigo-50 dark:bg-indigo-500/10 rounded-xl text-indigo-500 shrink-0">
							<MonitorPlay class="w-6 h-6" />
						</div>
						<div>
							<div class="flex items-baseline gap-2 mb-0.5">
								<div class="text-2xl font-black text-gray-900 dark:text-white leading-none">
									{theaterStats.total_show_setlist}
								</div>
								<span class="text-xs font-medium text-gray-400"
									>{t('admin.dashboard.stats.shows')}</span
								>
							</div>
							<div
								class="flex items-center gap-1 text-[11px] text-indigo-500 dark:text-indigo-400 font-medium mt-1"
							>
								{theaterStats.total_upcoming_shows}
								{t('admin.dashboard.stats.upcoming')}
							</div>
						</div>
					</div>
				</div>

				<!-- Events -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-orange-50 dark:bg-orange-500/10 rounded-xl text-orange-500 shrink-0">
							<Calendar class="w-6 h-6" />
						</div>
						<div>
							<div class="flex items-baseline gap-2 mb-0.5">
								<div class="text-2xl font-black text-gray-900 dark:text-white leading-none">
									{theaterStats.total_events}
								</div>
								<span class="text-xs font-medium text-gray-400"
									>{t('admin.dashboard.stats.events')}</span
								>
							</div>
							<div
								class="flex items-center gap-1 text-[11px] text-orange-500 dark:text-orange-400 font-medium mt-1"
							>
								{theaterStats.total_upcoming_events}
								{t('admin.dashboard.stats.upcoming')}
							</div>
						</div>
					</div>
				</div>

				<!-- News -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div
							class="p-3 bg-gray-100 dark:bg-zinc-700 rounded-xl text-gray-600 dark:text-gray-300 shrink-0"
						>
							<Newspaper class="w-6 h-6" />
						</div>
						<div>
							<div class="text-2xl font-black text-gray-900 dark:text-white leading-none mb-1">
								{theaterStats.total_news}
							</div>
							<div class="text-xs font-medium text-gray-500 dark:text-gray-400">
								{t('admin.dashboard.stats.newsPublished')}
							</div>
						</div>
					</div>
				</div>

				<!-- Live -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-cyan-50 dark:bg-cyan-500/10 rounded-xl text-cyan-500 shrink-0">
							<Radio class="w-6 h-6" />
						</div>
						<div>
							<div class="flex items-baseline gap-2 mb-0.5">
								<div class="text-2xl font-black text-gray-900 dark:text-white leading-none">
									{theaterStats.total_live_member}
								</div>
								<span class="text-xs font-medium text-gray-400"
									>{t('admin.dashboard.stats.liveHistory')}</span
								>
							</div>
							<div
								class="flex items-center gap-3 text-[11px] text-gray-500 dark:text-gray-400 mt-1"
							>
								<span class="flex items-center gap-1"
									><div class="w-1.5 h-1.5 rounded-full bg-blue-400"></div>
									{theaterStats.showroom_live_count}
									{t('admin.dashboard.stats.sr')}</span
								>
								<span class="flex items-center gap-1"
									><div class="w-1.5 h-1.5 rounded-full bg-rose-500"></div>
									{theaterStats.idn_live_count}
									{t('admin.dashboard.stats.idn')}</span
								>
							</div>
						</div>
					</div>
				</div>

				<!-- Replay Live -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div
							class="p-3 bg-fuchsia-50 dark:bg-fuchsia-500/10 rounded-xl text-fuchsia-500 shrink-0"
						>
							<Video class="w-6 h-6" />
						</div>
						<div>
							<div class="flex items-baseline gap-2 mb-0.5">
								<div class="text-2xl font-black text-gray-900 dark:text-white leading-none">
									{theaterStats.total_replay_live}
								</div>
								<span class="text-xs font-medium text-gray-400"
									>{t('admin.dashboard.stats.replayLive')}</span
								>
							</div>
							<div
								class="flex items-center gap-3 text-[11px] text-gray-500 dark:text-gray-400 mt-1"
							>
								<span class="flex items-center gap-1"
									><div class="w-1.5 h-1.5 rounded-full bg-blue-400"></div>
									{theaterStats.showroom_replay_count}
									{t('admin.dashboard.stats.sr')}</span
								>
								<span class="flex items-center gap-1"
									><div class="w-1.5 h-1.5 rounded-full bg-rose-500"></div>
									{theaterStats.idn_replay_count}
									{t('admin.dashboard.stats.idn')}</span
								>
							</div>
						</div>
					</div>
				</div>

				<!-- Birthdays -->
				<div
					class="bg-white dark:bg-zinc-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="flex items-center gap-4">
						<div class="p-3 bg-pink-50 dark:bg-pink-500/10 rounded-xl text-pink-500 shrink-0">
							<Gift class="w-6 h-6" />
						</div>
						<div>
							<div class="flex items-baseline gap-2 mb-1">
								<div class="text-2xl font-black text-gray-900 dark:text-white leading-none">
									{theaterStats.upcoming_birthdays_count}
								</div>
								<span class="text-xs font-medium text-gray-400"
									>{t('admin.dashboard.stats.upcoming')}</span
								>
							</div>
							<div class="text-xs font-medium text-gray-500 dark:text-gray-400">
								{t('admin.dashboard.stats.birthdaysThisYear')}
							</div>
						</div>
					</div>
				</div>
			</div>
		</section>
	{/if}
</div>
