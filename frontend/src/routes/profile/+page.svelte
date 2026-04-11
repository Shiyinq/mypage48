<script lang="ts">
	export let params: Record<string, string> | undefined = undefined;
	import { onMount } from 'svelte';
	import { isAuthenticated, showToast, userProfile, isUserProfileLoading } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { goto } from '$app/navigation';
	import { members, type Member } from '$lib/apis/members';
	import { User as UserIcon, LogOut, Settings } from 'lucide-svelte';
	import { auth } from '$lib/apis/auth';
	import SEO from '$lib/components/SEO.svelte';
	import { PageHeader, ErrorState } from '$lib/components';

	import type { ProfileRecentActivity, RankInfo, User, UserOshi, OshiShow } from '$lib/types';
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
		oshi: UserOshi | null;
	}

	let profile: ProfileData | null = null;
	let recentActivity: ProfileRecentActivity[] = [];
	let level: RankInfo = { current: 'Newcomer', xp: 0, nextLevelXp: 1, nextRankTitle: 'First Step' };
	let totalShows = 0;
	let totalAchievements = 0;
	let twoShotRouletteCount = 0;
	let twoShotBirthdayCount = 0;
	let oshiMeetings = 0;
	let upcomingSchedule: OshiShow[] = [];
	let pastSchedule: OshiShow[] = [];

	$: error = $userProfile.error;

	// Oshi Selection State
	let showOshiModal = false;
	let savingOshi = false;

	// Progress percent derived from level
	$: progressPercent =
		level.nextLevelXp > 0 ? Math.min((level.xp / level.nextLevelXp) * 100, 100) : 0;

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
			oshi: profileData.oshi || null
		};
	}

	onMount(() => {
		if ($isAuthenticated) {
			// Check if store already has data with stats
			if (!$userProfile.data?.profileRank) {
				fetchProfile();
			}
		}
	});

	// Subscribe to store changes to keep local state in sync
	// The userProfile store now contains UserWithProfileStats with profile stats
	$: {
		const storeState = $userProfile;
		const storeProfile = storeState.data;
		// loading state is handled by top-level reactive declaration

		if (storeProfile) {
			profile = mapProfileData(storeProfile);

			// Extract profile stats from typed store
			if (storeProfile.profileRank) {
				level = storeProfile.profileRank;
			}
			if (storeProfile.profileStats) {
				totalShows = storeProfile.profileStats.totalShows;
				totalAchievements = storeProfile.profileStats.totalAchievements;
				oshiMeetings = storeProfile.profileStats.oshiMeetings || 0;
			}
			if (storeProfile.profileOshiTwoShots) {
				twoShotRouletteCount = storeProfile.profileOshiTwoShots.roulette;
				twoShotBirthdayCount = storeProfile.profileOshiTwoShots.birthday;
			}
			if (storeProfile.oshi) {
				upcomingSchedule = storeProfile.oshi.upcomingSchedule || [];
				pastSchedule = storeProfile.oshi.pastSchedule || [];
			}
			if (storeProfile.profileRecentActivity) {
				recentActivity = storeProfile.profileRecentActivity;
			}
		}
	}

	async function fetchProfile() {
		try {
			// Use store action
			await userProfile.load();
		} catch (e) {
			showToast($t('profile.errorTitle'), 'error');
		}
	}

	const logout = async () => {
		try {
			await auth.logout();
			showToast($t('auth.logout.success'), 'success');
		} catch (e) {
			logger.error('Logout error', e, { context: 'ProfilePage' });
			// Even if backend fails, force local logout
		} finally {
			// Clear all stores handled by index.ts subscription to isAuthenticated
			isAuthenticated.set(false);
			goto('/login');
		}
	};

	// Oshi Modal Logic
	const openOshiModal = () => {
		showOshiModal = true;
	};

	const closeOshiModal = () => {
		showOshiModal = false;
	};

	let memberDetail: Member | null = null;
	let showMemberDetail = false;
	let loadingMemberDetail = false;

	const openMemberDetail = async () => {
		if (!profile?.oshi?.name) return;
		showMemberDetail = true;

		// If we already have the detail loaded and it matches
		if (memberDetail && memberDetail.name === profile.oshi.name) {
			return;
		}

		memberDetail = null;
		loadingMemberDetail = true;
		try {
			const res = await members.getAll({ search: profile!.oshi!.name });
			if (res.data.length > 0) {
				// Fuzzy match might return others, try to find exact name match first
				const exact = res.data.find((m) => m.name === profile!.oshi!.name);
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

	const saveOshi = async (member: Member) => {
		savingOshi = true;
		try {
			// Use store action
			await userProfile.updateOshi(String(member.id));
			showToast('Oshi updated successfully!', 'success');
			closeOshiModal();
		} catch (e) {
			logger.error('Failed to save oshi', e, { context: 'ProfilePage' });
			showToast('Failed to save oshi', 'error');
		} finally {
			savingOshi = false;
		}
	};
</script>

<SEO title={$t('profile.title')} path="/profile" description={$t('seo.profile')} />

<div class="max-w-5xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 animate-fade-in pb-32">
	<!-- Page Header -->
	<div class="mb-8">
		<PageHeader 
			title={$t('profile.title')} 
			subtitle={$t('profile.subtitle')} 
			icon={UserIcon}
			actions={[
				{
					icon: Settings,
					label: 'Settings',
					onClick: () => goto('/settings')
				},
				{
					icon: LogOut,
					label: $t('common.logout'),
					onClick: logout,
					theme: 'red'
				}
			]}
		>
			<svelte:fragment slot="actions">
				<!-- Settings Button -->
				<button
					on:click={() => goto('/settings')}
					class="p-2 rounded-full bg-gray-100 dark:bg-zinc-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-zinc-700 hover:text-gray-700 dark:hover:text-gray-300 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-zinc-600 cursor-pointer"
					title="Settings"
				>
					<Settings class="w-5 h-5" />
				</button>
				<!-- Logout Button -->
				<button
					on:click={logout}
					class="p-2 rounded-full bg-gray-100 dark:bg-zinc-800 text-gray-500 dark:text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/30 hover:text-red-600 transition-colors border border-transparent hover:border-red-100 dark:hover:border-red-500/30 cursor-pointer"
					title={$t('common.logout')}
				>
					<LogOut class="w-5 h-5" />
				</button>
			</svelte:fragment>
		</PageHeader>
	</div>

	<!-- Error State -->
	<!-- Error State -->
	{#if error}
		<ErrorState
			title={$t('profile.errorTitle')}
			description={$t('profile.errorDesc')}
			onRetry={fetchProfile}
		/>
	{:else}
		<div class="grid lg:grid-cols-12 gap-8 min-w-0">
			<!-- LEFT COLUMN: Identity & Level (Span 5) -->
			<div class="lg:col-span-5 space-y-6 min-w-0">
				<DigitalMemberCard {profile} loading={$isUserProfileLoading} />
				<LevelProgress {level} {progressPercent} loading={$isUserProfileLoading} />
				<QuickStats {totalShows} {totalAchievements} loading={$isUserProfileLoading} />
				<RecentActivity {recentActivity} loading={$isUserProfileLoading} />
			</div>

			<!-- RIGHT COLUMN: Oshimen & Feed (Span 7) -->
			<div class="lg:col-span-7 space-y-6 min-w-0">
				<OshiCard
					{profile}
					loading={$isUserProfileLoading}
					rouletteCount={twoShotRouletteCount}
					birthdayCount={twoShotBirthdayCount}
					{oshiMeetings}
					onOpenOshiModal={openOshiModal}
					onOpenMemberDetail={openMemberDetail}
				/>
				<OshiShows {upcomingSchedule} {pastSchedule} loading={$isUserProfileLoading} />
			</div>
		</div>
	{/if}
</div>

<!-- Oshi Selection Modal -->
<OshiSelectionModal
	show={showOshiModal}
	saving={savingOshi}
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
