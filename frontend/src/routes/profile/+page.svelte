<script lang="ts">
	import { onMount } from 'svelte';
	import {
		isAuthenticated,
		showToast,
		userProfile,
		tickets as ticketsStore,
		isInitialDataLoaded
	} from '$lib/stores';
	import { get } from 'svelte/store';
	import { goto } from '$app/navigation';
	import { members, type Member } from '$lib/apis/members';
	import Button from '$lib/components/Button.svelte';
	import { User as UserIcon, LogOut, Settings } from 'lucide-svelte';
	import { auth } from '$lib/apis/auth';
	import SEO from '$lib/components/SEO.svelte';
	import { PageHeader } from '$lib/components';

	import type { Ticket, User } from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		DigitalMemberCard,
		LevelProgress,
		QuickStats,
		OshiCard,
		RecentActivity,
		OshiSelectionModal,
		MemberDetailModal
	} from '$lib/components/profile';
	import { calculateTotalAchievements } from '$lib/utils/achievements';
	import { calculateLevel } from '$lib/utils/level';

	const { t, locale } = useTranslation();

	// Profile data from API
	interface ProfileData {
		userId: string;
		profilePicture: string | null;
		name: string;
		email: string;
		username: string;
		memberId?: string;
		ofcStatus?: string;
		oshi: import('$lib/types').UserOshi | null;
	}

	let profile: ProfileData | null = null;
	let tickets: Ticket[] = [];
	let recentShows: Ticket[] = [];

	// Loading state now depends on the central isInitialDataLoaded store
	$: loading = !$isInitialDataLoaded;

	// Oshi Selection State
	let showOshiModal = false;
	let allMembers: Member[] = [];
	let loadingMembers = false;
	let savingOshi = false;

	// Computed stats
	$: totalShows = tickets.length;
	$: totalAchievements = calculateTotalAchievements(tickets);

	$: twoShotRouletteCount = tickets.filter(
		(t) => t.two_shot?.type === 'Roulette' && t.two_shot?.member_name === profile?.oshi?.name
	).length;
	$: twoShotBirthdayCount = tickets.filter(
		(t) => t.two_shot?.type === 'Birthday' && t.two_shot?.member_name === profile?.oshi?.name
	).length;

	$: level = calculateLevel(totalShows);

	$: progressPercent = Math.min((level.xp / level.nextLevelXp) * 100, 100);

	// Format date for {$t('profile.recentActivity.title')}

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

	// Helper to update recent shows from tickets
	function updateRecentShows(ticketsList: Ticket[]) {
		recentShows = [...ticketsList]
			.sort((a, b) => new Date(b.event.date).getTime() - new Date(a.event.date).getTime())
			.slice(0, 5);
	}

	onMount(() => {
		// Data sync handled by reactive statements below
	});

	// Subscribe to store changes to keep local state in sync
	$: {
		const storeTickets = $ticketsStore;
		tickets = storeTickets;
		updateRecentShows(tickets);
	}

	$: {
		const storeProfile = $userProfile;
		if (storeProfile) {
			profile = mapProfileData(storeProfile);
		}
	}

	const logout = async () => {
		try {
			await auth.logout();
			showToast($t('auth.logout.success'), 'success');
		} catch (e) {
			console.error('Logout error', e);
			// Even if backend fails, force local logout
		} finally {
			// Clear all stores
			userProfile.set(null);
			ticketsStore.set([]);
			isAuthenticated.set(false);
			goto('/login');
		}
	};

	// Oshi Modal Logic
	const openOshiModal = async () => {
		showOshiModal = true;
		if (allMembers.length === 0) {
			loadingMembers = true;
			try {
				const res = await members.getAll({ limit: 100 });
				allMembers = res.members.filter((m) => m.active); // Only show active members?
			} catch (e) {
				console.error('Failed to load members', e);
				showToast('Failed to load members list', 'error');
			} finally {
				loadingMembers = false;
			}
		}
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
			// First check if we have it in allMembers
			const found = allMembers.find((m) => m.name === profile!.oshi!.name);
			if (found) {
				memberDetail = found;
			} else {
				// Otherwise fetch it
				const res = await members.getAll({ search: profile!.oshi!.name });
				if (res.members.length > 0) {
					// Fuzzy match might return others, try to find exact name match first
					const exact = res.members.find((m) => m.name === profile!.oshi!.name);
					memberDetail = exact || res.members[0];
				}
			}
		} catch (e) {
			console.error('Failed to fetch member details', e);
			showToast('Failed to load member details', 'error');
		} finally {
			loadingMemberDetail = false;
		}
	};

	const closeMemberDetail = () => {
		showMemberDetail = false;
	};

	const saveOshi = async (memberId: number) => {
		savingOshi = true;
		try {
			await auth.updateOshi(memberId);
			showToast('Oshi updated successfully!', 'success');

			// Update local profile
			const member = allMembers.find((m) => m.id === memberId);
			if (member && profile) {
				profile.oshi = {
					name: member.name,
					nickname: member.nickname,
					generation: member.generation,
					profilePicture: member.img,
					catchphrase: member.jiko,
					socials: member.socials
				};
				// Update global store for Header
				userProfile.update((u) => (u ? { ...u, oshi: profile!.oshi } : null));
			}
			closeOshiModal();
		} catch (e) {
			console.error('Failed to save oshi', e);
			showToast('Failed to save oshi', 'error');
		} finally {
			savingOshi = false;
		}
	};
</script>

<SEO title={$t('profile.title')} path="/profile" description={$t('seo.profile')} />

<div class="max-w-5xl mx-auto p-4 animate-fade-in pb-24">
	<!-- Page Header -->
	<div class="mb-8">
		<PageHeader title={$t('profile.title')} subtitle={$t('profile.subtitle')} icon={UserIcon}>
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

	<div class="grid lg:grid-cols-12 gap-8">
		<!-- LEFT COLUMN: Identity & Level (Span 5) -->
		<div class="lg:col-span-5 space-y-6">
			<DigitalMemberCard {profile} {loading} />
			<LevelProgress {level} {progressPercent} {loading} />
			<QuickStats {totalShows} {totalAchievements} {loading} />
		</div>

		<!-- RIGHT COLUMN: Oshimen & Feed (Span 7) -->
		<div class="lg:col-span-7 space-y-6">
			<OshiCard
				{profile}
				{loading}
				rouletteCount={twoShotRouletteCount}
				birthdayCount={twoShotBirthdayCount}
				onOpenOshiModal={openOshiModal}
				onOpenMemberDetail={openMemberDetail}
			/>
			<RecentActivity {recentShows} {loading} />
		</div>
	</div>
</div>

<!-- Oshi Selection Modal -->
<OshiSelectionModal
	show={showOshiModal}
	members={allMembers}
	loading={loadingMembers}
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
