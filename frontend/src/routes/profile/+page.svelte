<script lang="ts">
	import { onMount } from 'svelte';
	import { isAuthenticated, showToast, userProfile, authStore } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { goto } from '$app/navigation';
	import { members, type Member } from '$lib/apis/members';
	import { User as UserIcon, LogOut, Settings, LoaderCircle } from 'lucide-svelte';
	import { scale } from 'svelte/transition';
	import SEO from '$lib/components/SEO.svelte';
	import { PageHeader, ErrorState } from '$lib/components';

	import type {
		ProfileRecentActivity,
		RankInfo,
		User,
		UserOshi,
		OshiTwoShotCounts
	} from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		DigitalMemberCard,
		LevelProgress,
		QuickStats,
		OshiCard,
		RecentActivity,
		OshiShows,
		OshiSelectionModal,
		MemberDetailModal
	} from '$lib/components/profile';
	interface Props {
		params?: Record<string, string> | undefined;
	}

	let { params: _params = undefined }: Props = $props();

	const { t } = useTranslation();

	// Profile data from API (consolidated response)
	interface ProfileData {
		userId: string;
		profilePicture: string | null;
		name: string;
		email: string;
		username: string;
		memberId?: string;
		ofcStatus?: string;
		oshis?: UserOshi[];
	}

	let profile: ProfileData | null = $state(null);
	let oshis: UserOshi[] = $state([]);
	let oshiTwoShotsList: OshiTwoShotCounts[] = $state([]);
	let oshiMeetingsList: number[] = $state([]);
	let currentOshiIndex = $state(0);
	let recentActivity: ProfileRecentActivity[] = $state([]);
	let level: RankInfo = $state({
		current: 'Newcomer',
		xp: 0,
		nextLevelXp: 1,
		nextRankTitle: 'First Step'
	});
	let totalShows = $state(0);
	let totalAchievements = $state(0);
	let totalTwoShots = $state(0);
	let totalLiveWatched = $state(0);

	let error = $derived(userProfile.error);

	// Oshi Selection State
	let showOshiModal = $state(false);
	let savingOshi = $state(false);

	// Confirm remove state
	let showRemoveConfirm = $state(false);
	let removeTargetId = $state<string | null>(null);

	let isLoggingOut = $derived(authStore.isLoggingOut);

	// Progress percent derived from level
	let progressPercent = $derived(
		level.nextLevelXp > 0 ? Math.min((level.xp / level.nextLevelXp) * 100, 100) : 0
	);

	// Current oshi schedule for OshiShows
	let currentUpcomingSchedule = $derived(oshis[currentOshiIndex]?.upcomingSchedule || []);
	let currentPastSchedule = $derived(oshis[currentOshiIndex]?.pastSchedule || []);

	// Helper to map profile data from User store to local ProfileData
	function mapProfileData(profileData: User): ProfileData {
		return {
			userId: profileData.userId || '',
			profilePicture: profileData.profilePicture || null,
			name: profileData.name || '',
			email: profileData.email || '',
			username: profileData.username || '',
			memberId: profileData.memberId || undefined,
			ofcStatus: profileData.ofcStatus || undefined,
			oshis: profileData.oshis || []
		};
	}

	onMount(() => {
		if (isAuthenticated.value) {
			// Check if store already has data with stats
			if (!userProfile.data?.profileRank) {
				fetchProfile();
			}
		}
	});

	// Subscribe to store changes to keep local state in sync
	$effect(() => {
		const storeProfile = userProfile.data;

		if (storeProfile) {
			profile = mapProfileData(storeProfile);

			oshis = storeProfile.oshis || [];
			oshiTwoShotsList = storeProfile.profileOshiTwoShotsList || [];
			oshiMeetingsList = storeProfile.profileOshiMeetingsList || [];

			// Reset index if out of bounds
			if (currentOshiIndex >= oshis.length) {
				currentOshiIndex = 0;
			}

			// Extract profile stats from typed store
			if (storeProfile.profileRank) {
				level = storeProfile.profileRank;
			}
			if (storeProfile.profileStats) {
				totalShows = storeProfile.profileStats.totalShows;
				totalAchievements = storeProfile.profileStats.totalAchievements;
				totalTwoShots = storeProfile.profileStats.totalTwoShots || 0;
				totalLiveWatched = storeProfile.profileStats.totalLiveWatched || 0;
			}
			if (storeProfile.profileRecentActivity) {
				recentActivity = storeProfile.profileRecentActivity;
			}
		}
	});

	async function fetchProfile() {
		try {
			await userProfile.load();
		} catch {
			showToast(t('profile.errorTitle'), 'error');
		}
	}

	const logout = async () => {
		try {
			await authStore.logout();
			showToast(t('auth.logout.success'), 'success');
			goto('/login');
		} catch (e) {
			logger.error('Logout error', e, { context: 'ProfilePage' });
		}
	};

	// Oshi Modal Logic
	const openOshiModal = () => {
		showOshiModal = true;
	};

	const closeOshiModal = () => {
		showOshiModal = false;
	};

	let memberDetail: Member | null = $state(null);
	let showMemberDetail = $state(false);
	let loadingMemberDetail = $state(false);

	const openMemberDetail = async (memberName: string) => {
		if (!memberName) return;
		showMemberDetail = true;

		if (memberDetail && memberDetail.name === memberName) {
			return;
		}

		memberDetail = null;
		loadingMemberDetail = true;
		try {
			const res = await members.getAll({ search: memberName });
			if (res.data.length > 0) {
				const exact = res.data.find((m) => m.name === memberName);
				memberDetail = exact || res.data[0];
			}
		} catch (e) {
			logger.error('Failed to fetch member details', e, { context: 'ProfilePage' });
			showToast('Failed to load member details', 'error');
		} finally {
			loadingMemberDetail = false;
		}
	};

	const closeMemberDetail = () => {
		showMemberDetail = false;
	};

	const saveOshi = async (members: Member[]) => {
		savingOshi = true;
		try {
			await userProfile.addOshi(members.map((m) => String(m.id)));
			showToast(t('profile.oshiModal.addedToast'), 'success');
			closeOshiModal();
		} catch (e) {
			logger.error('Failed to add oshi', e, { context: 'ProfilePage' });
			showToast(t('profile.oshiModal.addErrorToast'), 'error');
		} finally {
			savingOshi = false;
		}
	};

	const confirmRemoveOshi = (oshiId: string) => {
		removeTargetId = oshiId;
		showRemoveConfirm = true;
	};

	const handleRemoveOshi = async () => {
		if (!removeTargetId) return;
		savingOshi = true;
		try {
			await userProfile.removeOshi(removeTargetId);
			showToast(t('profile.oshiModal.removedToast'), 'success');
			showRemoveConfirm = false;
			removeTargetId = null;
		} catch (e) {
			logger.error('Failed to remove oshi', e, { context: 'ProfilePage' });
			showToast(t('profile.oshiModal.removeErrorToast'), 'error');
		} finally {
			savingOshi = false;
		}
	};
</script>

<SEO title={t('profile.title')} path="/profile" description={t('seo.profile')} />

<div class="max-w-5xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 pb-32 space-y-4 sm:space-y-8">
	<!-- Top Section: Header & Quick Stats -->
	<div class="mb-0 sm:mb-8">
		<PageHeader
			title={t('profile.title')}
			subtitle={t('profile.subtitle')}
			icon={UserIcon}
			actionItems={[
				{
					icon: Settings,
					label: 'Settings',
					onClick: () => goto('/settings')
				},
				{
					icon: LogOut,
					label: t('common.logout'),
					onClick: logout,
					theme: 'red',
					loading: isLoggingOut
				}
			]}
		>
			{#snippet actions()}
				<!-- Settings Button -->
				<button
					onclick={() => goto('/settings')}
					class="p-2 rounded-full bg-gray-100 dark:bg-zinc-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-zinc-700 hover:text-gray-700 dark:hover:text-gray-300 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-zinc-600 cursor-pointer"
					title="Settings"
				>
					<Settings class="w-5 h-5" />
				</button>
				<!-- Logout Button -->
				<button
					onclick={logout}
					disabled={isLoggingOut}
					class="p-2 rounded-full bg-red-50 dark:bg-red-500/10 text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 transition-colors border border-red-100/50 dark:border-red-500/30 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
					title={t('common.logout')}
				>
					{#if isLoggingOut}
						<LoaderCircle class="w-5 h-5 animate-spin" />
					{:else}
						<LogOut class="w-5 h-5" />
					{/if}
				</button>
			{/snippet}
		</PageHeader>
	</div>

	<!-- Error State -->
	<!-- Error State -->
	{#if error}
		<ErrorState
			title={t('profile.errorTitle')}
			description={t('profile.errorDesc')}
			onRetry={fetchProfile}
		/>
	{:else}
		<div class="grid lg:grid-cols-12 gap-8 min-w-0">
			<!-- LEFT COLUMN: Identity & Level (Span 5) -->
			<div class="lg:col-span-5 space-y-6 min-w-0">
				<DigitalMemberCard
					{profile}
					loading={userProfile.isLoading}
					activeOshiMemberType={oshis[currentOshiIndex]?.memberType}
				/>
				<LevelProgress {level} {progressPercent} loading={userProfile.isLoading} />
				<QuickStats
					{totalShows}
					{totalAchievements}
					{totalTwoShots}
					{totalLiveWatched}
					loading={userProfile.isLoading}
				/>
				<RecentActivity {recentActivity} loading={userProfile.isLoading} />
			</div>

			<!-- RIGHT COLUMN: Oshimen & Feed (Span 7) -->
			<div class="lg:col-span-7 space-y-6 min-w-0">
				<OshiCard
					{oshis}
					{oshiTwoShotsList}
					{oshiMeetingsList}
					bind:currentIndex={currentOshiIndex}
					loading={userProfile.isLoading}
					onOpenOshiModal={openOshiModal}
					onOpenMemberDetail={openMemberDetail}
					onRemoveOshi={confirmRemoveOshi}
				/>
				<OshiShows
					upcomingSchedule={currentUpcomingSchedule}
					pastSchedule={currentPastSchedule}
					loading={userProfile.isLoading}
				/>
			</div>
		</div>
	{/if}
</div>

<!-- Oshi Selection Modal -->
<OshiSelectionModal
	show={showOshiModal}
	saving={savingOshi}
	currentOshiIds={oshis.map((o) => o.id)}
	maxCount={5}
	onClose={closeOshiModal}
	onSave={saveOshi}
/>

<!-- Member Detail Modal -->
<MemberDetailModal
	show={showMemberDetail}
	member={memberDetail}
	loading={loadingMemberDetail}
	onClose={closeMemberDetail}
/>

<!-- Remove Oshi Confirmation -->
{#if showRemoveConfirm}
	<div class="fixed inset-0 z-[1100] flex items-center justify-center p-4">
		<div
			class="absolute inset-0 bg-black/60 backdrop-blur-sm"
			onclick={() => {
				showRemoveConfirm = false;
				removeTargetId = null;
			}}
			onkeydown={(e) =>
				e.key === 'Escape' && (showRemoveConfirm = false) && (removeTargetId = null)}
			role="button"
			tabindex="-1"
			aria-label={t('common.close')}
		></div>
		<div
			class="relative w-full max-w-sm bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl p-6"
			transition:scale={{ duration: 200, start: 0.95 }}
		>
			<h3 class="text-lg font-black text-gray-800 dark:text-white mb-2">
				{t('profile.oshiModal.confirmTitle')}
			</h3>
			<p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
				{t('profile.oshiModal.confirmDesc')}
			</p>
			<div class="flex justify-end gap-3">
				<button
					onclick={() => {
						showRemoveConfirm = false;
						removeTargetId = null;
					}}
					class="px-4 py-2 rounded-xl bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-zinc-700 font-bold text-sm transition-colors cursor-pointer"
				>
					{t('profile.oshiModal.cancel')}
				</button>
				<button
					onclick={handleRemoveOshi}
					disabled={savingOshi}
					class="px-4 py-2 rounded-xl bg-red-500 hover:bg-red-600 text-white font-bold text-sm transition-colors cursor-pointer disabled:opacity-50"
				>
					{#if savingOshi}
						<LoaderCircle class="w-4 h-4 animate-spin" />
					{:else}
						{t('profile.oshiModal.confirmRemove')}
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}
