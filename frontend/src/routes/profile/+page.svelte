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
	import Input from '$lib/components/Input.svelte';
	import Button from '$lib/components/Button.svelte';
	import {
		User as UserIcon,
		LogOut,
		Crown,
		QrCode,
		Sparkles,
		Trophy,
		Star,
		Heart,
		MapPin,
		Zap,
		TrendingUp,
		Music,
		Calendar,
		Award,
		Plus,
		X,
		Search,
		Check,
		Instagram,
		Smartphone,
		Tv,
		Info,
		Cake,
		Dices,
		Quote,
		Globe,
		Settings
	} from 'lucide-svelte';
	import { auth } from '$lib/apis/auth';
	import SEO from '$lib/components/SEO.svelte';

	import type { Ticket, User } from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t, locale } = useTranslation();

	// Profile data from API
	interface ProfileData {
		userId: string;
		profilePicture: string | null;
		name: string;
		email: string;
		username: string;
		memberId: string | null;
		ofcStatus: string | null;
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
	let filteredMembers: Member[] = [];
	let oshiSearchQuery = '';
	let selectedOshiId: number | null = null;
	let loadingMembers = false;
	let savingOshi = false;

	// Computed stats
	$: totalShows = tickets.length;

	// Calculate achievements based on milestones (same logic as achievements page)
	$: totalAchievements = (() => {
		if (tickets.length === 0) return 0;

		let count = 0;
		const totalShows = tickets.length;

		// Date Calculations
		const sortedDates = [...tickets]
			.map((t) => new Date(t.event.date).getTime())
			.sort((a, b) => a - b);
		const firstDate = sortedDates[0];
		const lastDate = sortedDates[sortedDates.length - 1];
		const timeSpanDays = firstDate && lastDate ? (lastDate - firstDate) / (1000 * 60 * 60 * 24) : 0;

		// Show Counts
		const showCounts: Record<string, number> = {};
		tickets.forEach((t) => {
			const title = t.event.title.trim();
			showCounts[title] = (showCounts[title] || 0) + 1;
		});
		const maxSameShow = Math.max(...Object.values(showCounts), 0);

		// Row Calculations
		const hasRowA = tickets.some((t) => t.seat.section.toUpperCase() === 'A');
		const hasRowJ = tickets.some((t) => t.seat.section.toUpperCase() === 'J');
		const collectedRows = new Set(
			tickets.map((t) => t.seat.section.trim().toUpperCase().charAt(0))
		);
		const targetRows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
		const uniqueRowsCount = targetRows.filter((r) => collectedRows.has(r)).length;

		// Spending
		const totalSpent = tickets.reduce((acc, t) => acc + t.price, 0);

		// Count unlocked milestones
		if (totalShows >= 1) count++; // First Step
		if (totalShows >= 10) count++; // Regular Visitor
		if (totalShows >= 50) count++; // Dedicated Fan
		if (totalShows >= 100) count++; // Century Club
		if (totalShows >= 150) count++; // Theater Icon
		if (totalShows >= 200) count++; // Legendary Wota
		if (maxSameShow >= 10) count++; // Super Fan
		if (maxSameShow >= 20) count++; // Mega Fan
		if (maxSameShow >= 30) count++; // Ultra Fan
		if (timeSpanDays >= 365) count++; // Theater Enthusiast
		if (timeSpanDays >= 730) count++; // Theater Veteran
		if (timeSpanDays >= 1095) count++; // Theater Legend
		if (hasRowA) count++; // Elite Seat
		if (hasRowJ) count++; // Back Row Warrior
		if (uniqueRowsCount >= 10) count++; // Seat Explorer
		if (totalSpent >= 5000000) count++; // Top Supporter

		return count;
	})();

	$: twoShotRouletteCount = tickets.filter(
		(t) => t.two_shot?.type === 'Roulette' && t.two_shot?.member_name === profile?.oshi?.name
	).length;
	$: twoShotBirthdayCount = tickets.filter(
		(t) => t.two_shot?.type === 'Birthday' && t.two_shot?.member_name === profile?.oshi?.name
	).length;

	// Level System
	const milestones = [
		{ xp: 0, title: 'Newcomer' },
		{ xp: 1, title: 'First Step' },
		{ xp: 10, title: 'Regular Visitor' },
		{ xp: 50, title: 'Dedicated Fan' },
		{ xp: 100, title: 'Century Club' },
		{ xp: 150, title: 'Theater Icon' },
		{ xp: 200, title: 'Legendary Wota' },
		{ xp: 300, title: 'Theater Kami' },
		{ xp: 500, title: 'Absolute Legend' }
	];

	$: level = (() => {
		const xp = totalShows;
		let currentRank = milestones[0];
		let nextRank = milestones[1];

		for (let i = 0; i < milestones.length; i++) {
			if (xp >= milestones[i].xp) {
				currentRank = milestones[i];
				nextRank = milestones[i + 1] || { xp: 1000, title: 'Beyond Legend' };
			}
		}

		return {
			current: currentRank.title,
			xp: xp,
			nextLevelXp: nextRank.xp,
			nextRankTitle: nextRank.title
		};
	})();

	$: progressPercent = Math.min((level.xp / level.nextLevelXp) * 100, 100);

	// Format date for {$t('profile.recentActivity.title')}
	// Format date for {$t('profile.recentActivity.title')}
	function formatActivityDate(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
		const $t = get(t);
		const lang = get(locale);

		if (diffDays === 0) return $t('time.relative.today');
		if (diffDays === 1) return $t('time.relative.yesterday');
		if (diffDays < 7) return $t('time.relative.daysAgo', { count: diffDays });
		if (diffDays < 30) return $t('time.relative.weeksAgo', { count: Math.floor(diffDays / 7) });

		const localeMap: Record<string, string> = { id: 'id-ID', ja: 'ja-JP', en: 'en-US' };
		return date.toLocaleDateString(localeMap[lang] || 'en-US', { month: 'short', day: 'numeric' });
	}

	// Helper to map profile data from User store to local ProfileData
	function mapProfileData(profileData: User): ProfileData {
		return {
			userId: profileData.userId || '',
			profilePicture: profileData.profilePicture || null,
			name: profileData.name || '',
			email: profileData.email || '',
			username: profileData.username || '',
			memberId: profileData.memberId || null,
			ofcStatus: profileData.ofcStatus || null,
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
				filteredMembers = allMembers;
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
		oshiSearchQuery = '';
		selectedOshiId = null;
		filteredMembers = allMembers;
	};

	const handleOshiSearch = () => {
		if (!oshiSearchQuery.trim()) {
			filteredMembers = allMembers;
		} else {
			const q = oshiSearchQuery.toLowerCase();
			filteredMembers = allMembers.filter(
				(m) =>
					m.name.toLowerCase().includes(q) ||
					m.nickname.toLowerCase().includes(q) ||
					m.generation.toLowerCase().includes(q)
			);
		}
	};

	const selectOshi = (id: number) => {
		selectedOshiId = id;
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

	const saveOshi = async () => {
		if (!selectedOshiId) return;
		savingOshi = true;
		try {
			await auth.updateOshi(selectedOshiId);
			showToast('Oshi updated successfully!', 'success');

			// Update local profile
			const member = allMembers.find((m) => m.id === selectedOshiId);
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
				userProfile.set(profile as any);
			}
			closeOshiModal();
		} catch (e) {
			console.error('Failed to save oshi', e);
			showToast('Failed to save oshi', 'error');
		} finally {
			savingOshi = false;
		}
	};

	function parseIndonesianDate(dateStr: string): Date {
		const monthMap: { [key: string]: string } = {
			januari: 'January',
			februari: 'February',
			maret: 'March',
			april: 'April',
			mei: 'May',
			juni: 'June',
			juli: 'July',
			agustus: 'August',
			september: 'September',
			oktober: 'October',
			november: 'November',
			desember: 'December'
		};

		const parts = dateStr.split(' ');
		if (parts.length >= 3) {
			const day = parts[0];
			const month = parts[1].toLowerCase();
			const year = parts[2];
			const engMonth = monthMap[month] || month;
			return new Date(`${engMonth} ${day}, ${year}`);
		}
		return new Date(dateStr);
	}

	function calculateAge(birthdateStr: string): number | string {
		const birthDate = parseIndonesianDate(birthdateStr);
		if (isNaN(birthDate.getTime())) return 'N/A';
		const diffMs = Date.now() - birthDate.getTime();
		const ageDate = new Date(diffMs);
		return Math.abs(ageDate.getUTCFullYear() - 1970);
	}
</script>

<SEO title={$t('profile.title')} path="/profile" description={$t('seo.profile')} />

<div class="max-w-5xl mx-auto p-4 animate-fade-in pb-24">
	<!-- Page Header -->
	<div class="flex items-center justify-between mb-8">
		<div class="flex items-center gap-3">
			<div
				class="p-3 rounded-2xl bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 shadow-lg shadow-red-100 dark:shadow-red-900/20 border-2 border-white dark:border-zinc-700 transform -rotate-6"
			>
				<UserIcon class="w-6 h-6" />
			</div>
			<div>
				<h2 class="text-2xl font-black idol-text-gradient leading-none relative w-fit">
					{$t('profile.title')}
					<span
						class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 dark:bg-red-500/30 -z-10 transform -skew-x-12 rounded-sm"
					></span>
				</h2>
				<p class="text-sm text-themed-secondary mt-1">{$t('profile.subtitle')}</p>
			</div>
		</div>
		<div class="flex items-center gap-2">
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
		</div>
	</div>

	<div class="grid lg:grid-cols-12 gap-8">
		<!-- LEFT COLUMN: Identity & Level (Span 5) -->
		<div class="lg:col-span-5 space-y-6">
			<!-- DIGITAL MEMBER CARD -->
			<div class="relative group perspective-1000">
				<!-- Card Container -->
				<div
					class="relative h-56 w-full rounded-3xl overflow-hidden shadow-2xl transition-transform duration-500 group-hover:scale-[1.02] {profile?.ofcStatus ===
					'Active'
						? 'ring-2 ring-green-400/50 ring-offset-2 ring-offset-white'
						: ''}"
				>
					<!-- Background -->
					<div class="absolute inset-0 bg-gradient-to-br from-gray-900 via-red-900 to-black"></div>
					<div
						class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20"
					></div>

					<!-- Holographic Overlay -->
					<div
						class="absolute inset-0 bg-gradient-to-tr from-white/10 via-transparent to-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"
					></div>

					<!-- Active OFC Glow Effect -->
					{#if profile?.ofcStatus === 'Active'}
						<div
							class="absolute -top-2 -right-2 w-20 h-20 bg-green-400 rounded-full blur-2xl opacity-30 animate-pulse"
						></div>
					{/if}

					<!-- Red Accent Curves -->
					<div
						class="absolute -top-10 -right-10 w-40 h-40 bg-red-600 rounded-full blur-3xl opacity-50"
					></div>
					<div
						class="absolute -bottom-10 -left-10 w-40 h-40 bg-red-600 rounded-full blur-3xl opacity-30"
					></div>

					<!-- Card Content -->
					<div class="relative z-10 p-6 h-full flex flex-col justify-between text-white">
						<!-- Top Row -->
						<div class="flex justify-between items-start">
							<div class="flex items-center gap-2">
								<div
									class="w-8 h-8 rounded-lg bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center"
								>
									<Crown class="w-4 h-4 text-yellow-400" />
								</div>
								<div>
									<p class="text-[10px] font-bold text-red-400 tracking-widest uppercase">
										{$t('profile.memberCard.officialFanClub')}
									</p>
									<h3 class="font-black text-lg tracking-tight">
										MYPAGE<span class="text-red-500">48</span>
									</h3>
								</div>
							</div>
							<div class="flex flex-col items-end gap-1">
								<!-- Member ID -->
								<div class="text-right">
									<p class="text-[10px] text-gray-400 font-bold">
										{$t('profile.memberCard.memberId')}
									</p>
									<p class="font-mono font-bold text-shadow">
										{#if loading}
											<span class="inline-block w-20 h-4 bg-white/20 rounded animate-pulse"></span>
										{:else}
											{profile?.memberId || 'N/A'}
										{/if}
									</p>
								</div>
								<!-- OFC Status Badge -->
								{#if loading}
									<div class="h-5 w-16 bg-white/20 rounded-full animate-pulse mt-1"></div>
								{:else}
									<div
										class="flex items-center gap-1.5 px-2.5 py-1 rounded-full backdrop-blur-md mt-1 {profile?.ofcStatus ===
										'Active'
											? 'bg-green-500/20 border border-green-400/30'
											: 'bg-white/10 border border-white/20'}"
									>
										<span
											class="w-1.5 h-1.5 rounded-full {profile?.ofcStatus === 'Active'
												? 'bg-green-400 animate-pulse shadow-[0_0_6px_rgba(74,222,128,0.6)]'
												: 'bg-gray-400'}"
										></span>
										<span
											class="text-[9px] font-bold uppercase tracking-wider {profile?.ofcStatus ===
											'Active'
												? 'text-green-300'
												: 'text-gray-400'}"
										>
											{profile?.ofcStatus === 'Active'
												? $t('profile.memberCard.ofcActive')
												: $t('profile.memberCard.ofcInactive')}
										</span>
									</div>
								{/if}
							</div>
						</div>

						<!-- Chip & Wave -->
						<div class="flex items-center gap-4 my-2 opacity-80">
							<div
								class="w-10 h-8 rounded-md bg-gradient-to-br from-yellow-200 to-yellow-600 border border-yellow-600 shadow-inner flex items-center justify-center"
							>
								<div class="w-6 h-4 border border-yellow-800/30 rounded-sm"></div>
							</div>
							<!-- WifiIcon -->
							<svg viewBox="0 0 24 24" fill="currentColor" class="w-6 h-6 rotate-90 text-gray-500">
								<path
									d="M12 19.5C12 19.5 12 19.5 12 19.5C13.3807 19.5 14.5 18.3807 14.5 17C14.5 15.6193 13.3807 14.5 12 14.5C10.6193 14.5 9.5 15.6193 9.5 17C9.5 18.3807 10.6193 19.5 12 19.5Z"
								/>
								<path
									fill-rule="evenodd"
									clip-rule="evenodd"
									d="M12 3C6.477 3 1.643 6.374 0.192 11.19L1.9 12.63C3.03 8.77 6.93 6 12 6C17.07 6 20.97 8.77 22.1 12.63L23.808 11.19C22.357 6.374 17.523 3 12 3ZM12 7C8.27 7 5.11 8.84 3.9 11.85L5.65 13.11C6.45 11.12 8.65 10 12 10C15.35 10 17.55 11.12 18.35 13.11L20.1 11.85C18.89 8.84 15.73 7 12 7Z"
									opacity="0.5"
								/>
							</svg>
						</div>

						<!-- Bottom Row -->
						<div class="flex justify-between items-end">
							<div>
								<p class="text-[10px] text-gray-400 font-bold uppercase mb-0.5">
									{$t('profile.memberCard.cardHolder')}
								</p>
								<p class="text-lg font-bold tracking-wide uppercase text-shadow-sm">
									{#if loading}
										<span class="inline-block w-40 h-5 bg-white/20 rounded animate-pulse"></span>
									{:else}
										{profile?.name || 'N/A'}
									{/if}
								</p>
							</div>
							<div class="bg-white p-1 rounded-lg">
								<QrCode class="w-8 h-8 text-black" />
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- LEVEL PROGRESS -->
			<div class="glass-panel p-6 rounded-3xl relative">
				{#if loading}
					<div class="flex justify-between items-end mb-2">
						<div>
							<div class="h-3 w-20 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse mb-2"></div>
							<div class="h-8 w-32 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
						</div>
						<div class="text-right">
							<div
								class="h-3 w-16 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse ml-auto"
							></div>
						</div>
					</div>
					<div
						class="h-3 w-full bg-gray-200 dark:bg-zinc-700 rounded-full animate-pulse mb-4"
					></div>
					<div class="h-9 w-full bg-gray-200 dark:bg-zinc-700 rounded-lg animate-pulse"></div>
				{:else}
					<div class="flex justify-between items-end mb-2">
						<div>
							<div class="flex items-center gap-1.5 mb-0.5">
								<p class="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase">
									{$t('profile.level.currentRank')}
								</p>
								<div class="relative group">
									<Info
										class="w-3.5 h-3.5 text-gray-300 cursor-help hover:text-red-400 transition-colors"
									/>
									<div
										class="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-2.5 py-1 bg-gray-800 text-white text-[10px] font-medium rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-all pointer-events-none whitespace-nowrap z-20"
									>
										1 XP = 1 Show
										<div
											class="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-4 border-transparent border-t-gray-800"
										></div>
									</div>
								</div>
							</div>
							<h3 class="text-2xl font-black idol-text-gradient">{level.current}</h3>
						</div>
						<div class="text-right">
							<p class="text-xs font-bold text-gray-500 dark:text-gray-400">
								<span class="text-red-600">{level.xp}</span> / {level.nextLevelXp} XP
							</p>
						</div>
					</div>

					<!-- Progress Bar -->
					<div
						class="h-3 w-full bg-gray-100 dark:bg-zinc-800 rounded-full overflow-hidden shadow-inner mb-4"
					>
						<div
							class="h-full idol-gradient rounded-full relative"
							style="width: {progressPercent}%"
						>
							<div
								class="absolute inset-0 bg-[linear-gradient(45deg,rgba(255,255,255,0.2)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.2)_50%,rgba(255,255,255,0.2)_75%,transparent_75%,transparent)] bg-[length:1rem_1rem] animate-[pulse_1s_linear_infinite]"
							></div>
						</div>
					</div>

					<div
						class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 font-medium bg-gray-50 dark:bg-zinc-800 p-2 rounded-lg border border-gray-100 dark:border-zinc-700"
					>
						<Sparkles class="w-3.5 h-3.5 text-yellow-500" />
						<span>
							<span class="font-bold text-gray-700 dark:text-gray-200"
								>{level.nextLevelXp - level.xp} XP</span
							>
							{$t('profile.level.needed')}
							{$t('profile.level.for')}
							<span class="font-bold text-gray-700 dark:text-gray-200">{level.nextRankTitle}</span>
						</span>
					</div>
				{/if}
			</div>

			<!-- QUICK STATS -->
			<div class="grid grid-cols-2 gap-4">
				<div
					class="glass-panel p-4 rounded-2xl flex flex-col items-center justify-center text-center"
				>
					<div
						class="w-8 h-8 rounded-full bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 flex items-center justify-center mb-2"
					>
						<Trophy class="w-4 h-4" />
					</div>
					{#if loading}
						<span class="inline-block w-10 h-7 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"
						></span>
					{:else}
						<span class="text-2xl font-black text-themed">{totalShows}</span>
					{/if}
					<span class="text-[10px] font-bold text-gray-400 uppercase"
						>{$t('profile.stats.totalShows')}</span
					>
				</div>
				<div
					class="glass-panel p-4 rounded-2xl flex flex-col items-center justify-center text-center"
				>
					<div
						class="w-8 h-8 rounded-full bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400 flex items-center justify-center mb-2"
					>
						<Star class="w-4 h-4" />
					</div>
					{#if loading}
						<span class="inline-block w-10 h-7 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"
						></span>
					{:else}
						<span class="text-2xl font-black text-themed">{totalAchievements}</span>
					{/if}
					<span class="text-[10px] font-bold text-gray-400 uppercase"
						>{$t('profile.stats.achievements')}</span
					>
				</div>
			</div>
		</div>

		<!-- RIGHT COLUMN: Oshimen & Feed (Span 7) -->
		<div class="lg:col-span-7 space-y-6">
			<!-- OSHI SHRINE -->
			<div class="glass-panel p-0 rounded-3xl overflow-hidden relative">
				<!-- Banner -->
				<div
					class="h-32 w-full bg-[url('https://upload.wikimedia.org/wikipedia/commons/5/53/JKT48_Logo_-_Red_Background_%282016%29.png')] bg-cover bg-center relative"
				>
					<div
						class="absolute inset-0 bg-gradient-to-t from-white via-white/50 to-transparent"
					></div>
				</div>

				<div class="px-6 md:px-8 pb-6 relative">
					{#if loading}
						<!-- Oshi Skeleton Loading -->
						<div class="flex flex-col md:flex-row items-center md:items-end gap-6 -mt-16">
							<!-- Avatar Skeleton -->
							<div
								class="w-32 h-32 rounded-full bg-gray-200 dark:bg-zinc-700 border-4 border-white dark:border-zinc-900 shadow-xl animate-pulse relative z-10"
							></div>

							<!-- Info Skeleton -->
							<div class="text-center md:text-left flex-1 w-full max-w-sm">
								<div class="flex flex-col md:flex-row items-center gap-2 mb-2">
									<div class="h-8 w-48 bg-gray-200 dark:bg-zinc-700 rounded-lg animate-pulse"></div>
									<div class="h-5 w-24 bg-gray-200 dark:bg-zinc-700 rounded-md animate-pulse"></div>
								</div>

								<!-- Catchphrase Skeleton -->
								<div
									class="h-16 w-full bg-gray-100 dark:bg-zinc-800 rounded-xl animate-pulse mt-2"
								></div>

								<!-- Socials Skeleton -->
								<div class="flex gap-2 mt-3 justify-center md:justify-start">
									<div
										class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse"
									></div>
									<div
										class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse"
									></div>
									<div
										class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse"
									></div>
								</div>
							</div>
						</div>
					{:else if profile?.oshi}
						<div class="flex flex-col md:flex-row items-center md:items-end gap-6 -mt-16">
							<!-- Avatar with Glow -->
							<div class="relative">
								<button
									class="relative w-28 h-28 rounded-full border-4 border-white shadow-xl overflow-hidden flex-shrink-0 cursor-pointer transition-transform hover:scale-105 active:scale-95"
									on:click={openMemberDetail}
								>
									{#if loading}
										<div class="w-full h-full bg-gray-200 animate-pulse"></div>
									{:else}
										<img
											src={profile?.oshi?.profilePicture || '/placeholder-user.jpg'}
											alt={profile?.oshi?.name}
											class="w-full h-full object-cover"
										/>
									{/if}
									<div
										class="absolute inset-0 bg-black/0 hover:bg-black/10 transition-colors flex items-center justify-center opacity-0 hover:opacity-100"
									>
										<Info class="w-8 h-8 text-white drop-shadow-md" />
									</div>
								</button>
							</div>

							<!-- Info -->
							<div class="text-center md:text-left flex-1 min-w-0">
								<div class="flex flex-col items-center md:items-start gap-1 mb-2">
									<div class="flex items-center gap-2">
										<h3 class="text-2xl font-black text-gray-800 leading-tight">
											{profile.oshi.name}
										</h3>
										<button
											on:click={openOshiModal}
											class="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors cursor-pointer"
											title="Change Oshi"
										>
											<Search class="w-4 h-4" />
										</button>
									</div>
									<span
										class="px-2 py-0.5 bg-red-100 text-red-600 text-[10px] font-bold rounded-md uppercase tracking-wide border border-red-200 whitespace-nowrap"
									>
										Generation {profile.oshi.generation}
									</span>
								</div>

								<!-- Catchphrase Bubble -->
								<div
									class="relative bg-gray-50 dark:bg-zinc-900 p-3 rounded-xl rounded-tl-none border border-gray-100 dark:border-zinc-800 shadow-sm mt-2 inline-block"
								>
									<p class="text-xs text-gray-600 dark:text-gray-400 italic font-medium">
										"{profile.oshi.catchphrase}"
									</p>
								</div>

								<!-- Socials -->
								{#if profile.oshi.socials}
									<div class="flex flex-wrap justify-center md:justify-start gap-2 mt-3">
										{#if profile.oshi.socials.twitter}
											<a
												href={profile.oshi.socials.twitter}
												target="_blank"
												rel="noopener noreferrer"
												class="p-1.5 bg-gray-100 dark:bg-white/5 rounded-full text-gray-500 dark:text-gray-300 hover:bg-black hover:text-white transition-colors cursor-pointer"
												title="Twitter / X"
											>
												<svg
													class="w-3.5 h-3.5"
													viewBox="0 0 24 24"
													fill="currentColor"
													xmlns="http://www.w3.org/2000/svg"
												>
													<path
														d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
													/>
												</svg>
											</a>
										{/if}
										{#if profile.oshi.socials.instagram}
											<a
												href={profile.oshi.socials.instagram}
												target="_blank"
												rel="noopener noreferrer"
												class="p-1.5 bg-gray-100 dark:bg-white/5 rounded-full text-gray-500 dark:text-gray-300 hover:bg-pink-100 dark:hover:bg-pink-900/30 hover:text-pink-600 transition-colors cursor-pointer"
												title="Instagram"
											>
												<Instagram class="w-3.5 h-3.5" />
											</a>
										{/if}
										{#if profile.oshi.socials.tiktok}
											<a
												href={profile.oshi.socials.tiktok}
												target="_blank"
												rel="noopener noreferrer"
												class="p-1.5 bg-gray-100 dark:bg-white/5 rounded-full text-gray-500 dark:text-gray-300 hover:bg-black hover:text-white transition-colors cursor-pointer"
												title="TikTok"
											>
												<svg
													class="w-3.5 h-3.5"
													viewBox="0 0 24 24"
													fill="currentColor"
													xmlns="http://www.w3.org/2000/svg"
												>
													<path
														d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"
													/>
												</svg>
											</a>
										{/if}
										{#if profile.oshi.socials.idn_app}
											<a
												href={profile.oshi.socials.idn_app}
												target="_blank"
												rel="noopener noreferrer"
												class="p-1.5 bg-gray-100 dark:bg-white/5 rounded-full text-gray-500 dark:text-gray-300 hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 transition-colors cursor-pointer"
												title="IDN App"
											>
												<Smartphone class="w-3.5 h-3.5" />
											</a>
										{/if}
										{#if profile.oshi.socials.showroom}
											<a
												href={profile.oshi.socials.showroom}
												target="_blank"
												rel="noopener noreferrer"
												class="p-1.5 bg-gray-100 dark:bg-white/5 rounded-full text-gray-500 dark:text-gray-300 hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:text-blue-600 transition-colors cursor-pointer"
												title="Showroom"
											>
												<Tv class="w-3.5 h-3.5" />
											</a>
										{/if}
									</div>
								{/if}
							</div>
						</div>
					{:else}
						<!-- Empty State: Select Oshi -->
						<div class="flex flex-col items-center justify-center text-center py-8 -mt-12">
							<div class="relative mb-4 group cursor-pointer" on:click={openOshiModal}>
								<div
									class="w-24 h-24 rounded-full bg-white dark:bg-zinc-800 shadow-lg flex items-center justify-center border-4 border-dashed border-gray-200 dark:border-zinc-700 group-hover:border-red-300 transition-colors"
								>
									<Plus class="w-8 h-8 text-gray-300 group-hover:text-red-400" />
								</div>
								<div
									class="absolute -bottom-2 px-3 py-1 bg-red-500 text-white text-xs font-bold rounded-full shadow-lg transform scale-90 group-hover:scale-100 transition-transform"
								>
									Select Oshi
								</div>
							</div>
							<h3 class="text-lg font-bold text-gray-700 dark:text-gray-300">Who is your Oshi?</h3>
							<p class="text-sm text-gray-500 dark:text-gray-400 max-w-xs mx-auto mt-1">
								Select your favorite member to display them on your profile card.
							</p>
							<div class="mt-4">
								<Button size="sm" variant="outline" on:click={openOshiModal}>Browse Members</Button>
							</div>
						</div>
					{/if}

					<div class="mt-6 grid grid-cols-2 gap-3 border-t border-gray-100 pt-4">
						<!-- 2-Shot Roulette -->
						<div
							class="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors"
						>
							<div
								class="p-2 rounded-full bg-yellow-50 dark:bg-yellow-900/20 shadow-sm text-yellow-600 dark:text-yellow-400"
							>
								<Dices class="w-4 h-4" />
							</div>
							<div>
								<p class="text-lg font-black text-gray-800 dark:text-gray-200 leading-none">
									{#if loading}
										<span
											class="inline-block w-6 h-5 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"
										></span>
									{:else}
										{twoShotRouletteCount}
									{/if}
								</p>
								<p class="text-[10px] font-bold text-gray-400 uppercase">
									{$t('profile.oshi.roulette')}
								</p>
							</div>
						</div>
						<!-- 2-Shot Birthday -->
						<div
							class="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors"
						>
							<div
								class="p-2 rounded-full bg-pink-50 dark:bg-pink-900/20 shadow-sm text-pink-600 dark:text-pink-400"
							>
								<Cake class="w-4 h-4" />
							</div>
							<div>
								<p class="text-lg font-black text-gray-800 dark:text-gray-200 leading-none">
									{#if loading}
										<span
											class="inline-block w-6 h-5 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"
										></span>
									{:else}
										{twoShotBirthdayCount}
									{/if}
								</p>
								<p class="text-[10px] font-bold text-gray-400 uppercase">
									{$t('profile.oshi.birthday')}
								</p>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- RECENT ACTIVITY FEED -->
			<div class="glass-panel p-6 rounded-3xl">
				<h4 class="font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
					<TrendingUp class="w-4 h-4 text-red-500" />
					{$t('profile.recentActivity.title')}
				</h4>

				<div
					class="space-y-4 relative before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-100 before:dark:bg-zinc-800"
				>
					{#if loading}
						<!-- Skeleton Loading for Activity Items -->
						{#each [1, 2, 3] as _}
							<div class="flex gap-4 relative z-10">
								<div
									class="w-10 h-10 rounded-full flex-shrink-0 bg-gray-200 dark:bg-zinc-700 animate-pulse"
								></div>
								<div
									class="flex-1 bg-white/50 dark:bg-zinc-800/50 p-3 rounded-xl border border-gray-50 dark:border-zinc-700"
								>
									<div class="flex justify-between items-start mb-2">
										<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-2/3 animate-pulse"></div>
										<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16 animate-pulse"></div>
									</div>
									<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-1/3 animate-pulse"></div>
								</div>
							</div>
						{/each}
					{:else if recentShows.length === 0}
						<div class="text-center py-8 text-gray-500">
							<Music class="w-8 h-8 mx-auto mb-2 text-gray-300" />
							<p class="text-sm">{$t('profile.recentActivity.noActivity')}</p>
							<p class="text-xs text-gray-400">{$t('profile.recentActivity.startTracking')}</p>
						</div>
					{:else}
						{#each recentShows as show}
							<div class="flex gap-4 relative z-10">
								<div
									class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 border-4 border-white dark:border-zinc-950 shadow-sm {show.two_shot
										? 'bg-yellow-100 dark:bg-yellow-950 text-yellow-600 dark:text-yellow-400'
										: 'bg-red-100 dark:bg-red-950 text-red-600 dark:text-red-400'}"
								>
									{#if show.two_shot}
										<Zap class="w-4 h-4" />
									{:else}
										<Music class="w-4 h-4" />
									{/if}
								</div>
								<div
									class="flex-1 bg-white/50 dark:bg-zinc-800/50 p-3 rounded-xl border border-gray-50 dark:border-zinc-700 hover:bg-white dark:hover:bg-zinc-800 transition-colors"
								>
									<div class="flex justify-between items-start">
										<p class="text-sm font-bold text-gray-800 dark:text-gray-200">
											{show.two_shot
												? $t('profile.recentActivity.twoShotAt')
												: $t('profile.recentActivity.attended')} '{show.event.title}'
										</p>
										<span class="text-[10px] font-medium text-gray-400"
											>{formatActivityDate(show.event.date)}</span
										>
									</div>
									<p class="text-xs text-gray-500 mt-0.5">
										Row {show.seat.section}-{show.seat.number}
										{#if show.two_shot}
											• {show.two_shot.member_name}
										{/if}
									</p>
								</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>

<!-- Oshi Selection Modal -->
{#if showOshiModal}
	<div class="fixed inset-0 z-[100] flex items-center justify-center p-4">
		<!-- Backdrop -->
		<div
			class="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
			on:click={closeOshiModal}
		></div>

		<!-- Modal Content -->
		<div
			class="relative w-full max-w-2xl bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl overflow-hidden animate-scale-up flex flex-col max-h-[85vh]"
		>
			<!-- Header -->
			<div
				class="p-6 border-b border-gray-100 dark:border-zinc-800 flex justify-between items-center bg-white dark:bg-zinc-900 z-10"
			>
				<div>
					<h3 class="text-xl font-black text-gray-800 dark:text-white">
						{$t('profile.oshiModal.title')}
					</h3>
					<p class="text-sm text-gray-500 dark:text-gray-400">{$t('profile.oshiModal.subtitle')}</p>
				</div>
				<button
					on:click={closeOshiModal}
					class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-500 dark:text-gray-400 transition-colors"
				>
					<X class="w-5 h-5" />
				</button>
			</div>

			<!-- Search -->
			<div class="p-4 bg-gray-50 dark:bg-zinc-800/50 border-b border-gray-100 dark:border-zinc-800">
				<div class="relative">
					<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
					<input
						type="text"
						bind:value={oshiSearchQuery}
						on:input={handleOshiSearch}
						placeholder={$t('profile.oshiModal.searchPlaceholder')}
						class="w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-gray-900 dark:text-white focus:outline-none focus:border-red-300 focus:ring-4 focus:ring-red-50 dark:focus:ring-red-900/30 transition-all font-medium text-sm"
					/>
				</div>
			</div>

			<!-- Member Grid -->
			<div class="flex-1 overflow-y-auto p-6 scrollbar-hide">
				{#if loadingMembers}
					<div class="flex flex-col items-center justify-center py-12">
						<div
							class="w-10 h-10 border-4 border-red-100 border-t-red-500 rounded-full animate-spin mb-4"
						></div>
						<p class="text-sm text-gray-500">{$t('profile.oshiModal.loading')}</p>
					</div>
				{:else if filteredMembers.length === 0}
					<div class="text-center py-12">
						<Search class="w-12 h-12 text-gray-200 mx-auto mb-3" />
						<p class="text-gray-500">
							{$t('profile.oshiModal.noMembers', { query: oshiSearchQuery })}
						</p>
					</div>
				{:else}
					<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
						{#each filteredMembers as member}
							<button
								class="group relative flex flex-col items-center text-center p-3 rounded-2xl transition-all duration-200 border-2 cursor-pointer
								{selectedOshiId === member.id
									? 'border-red-500 bg-red-50/50 dark:bg-red-900/20'
									: 'border-transparent hover:bg-gray-50 dark:hover:bg-zinc-800 hover:border-gray-100 dark:hover:border-zinc-700'}"
								on:click={() => selectOshi(member.id)}
							>
								<div class="relative w-20 h-20 mb-3">
									<img
										src={member.img}
										alt={member.name}
										class="w-full h-full rounded-full object-cover shadow-sm group-hover:shadow-md transition-shadow {selectedOshiId ===
										member.id
											? 'ring-2 ring-red-500 ring-offset-2 dark:ring-offset-zinc-900'
											: ''}"
									/>
									{#if selectedOshiId === member.id}
										<div
											class="absolute -right-1 -top-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white shadow-sm animate-scale-up"
										>
											<Check class="w-3.5 h-3.5" />
										</div>
									{/if}
								</div>
								<h4 class="font-bold text-gray-800 dark:text-white text-sm leading-tight mb-1">
									{member.name}
								</h4>
								<span
									class="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wide bg-gray-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full group-hover:bg-white dark:group-hover:bg-zinc-700 transition-colors"
									>{$t('profile.oshiModal.generation', { gen: member.generation })}</span
								>
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Footer Action -->
			<div
				class="p-6 border-t border-gray-100 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex justify-end gap-3 z-10"
			>
				<Button variant="outline" on:click={closeOshiModal} class="cursor-pointer"
					>{$t('profile.oshiModal.cancel')}</Button
				>
				<Button
					variant="primary"
					disabled={!selectedOshiId || savingOshi}
					loading={savingOshi}
					on:click={saveOshi}
					class="cursor-pointer"
				>
					{$t('profile.oshiModal.save')}
				</Button>
			</div>
		</div>
	</div>
{/if}

<!-- Member Detail Modal -->
{#if showMemberDetail}
	<div class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
		<div
			class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
			on:click={closeMemberDetail}
			role="button"
			tabindex="0"
			on:keydown={(e) => e.key === 'Escape' && closeMemberDetail()}
		></div>

		<div
			class="bg-white rounded-3xl w-full max-w-3xl overflow-hidden relative z-10 shadow-2xl animate-scale-in grid md:grid-cols-2"
		>
			{#if loadingMemberDetail}
				<!-- Skeleton Loader -->
				<!-- Left Side Skeleton -->
				<div class="relative h-80 md:h-full bg-gray-200 animate-pulse">
					<div class="absolute bottom-6 left-6 right-6 space-y-4">
						<div class="h-6 bg-gray-300 rounded-md w-24"></div>
						<div class="h-10 bg-gray-300 rounded-md w-3/4"></div>
						<div class="h-6 bg-gray-300 rounded-md w-1/2"></div>
					</div>
				</div>

				<!-- Right Side Skeleton -->
				<div class="p-6 space-y-8 flex flex-col justify-center bg-white">
					<!-- Quote Skeleton -->
					<div class="h-32 bg-gray-100 rounded-2xl animate-pulse w-full"></div>

					<!-- Stats Grid Skeleton -->
					<div class="grid grid-cols-2 gap-4">
						<div class="h-20 bg-gray-100 rounded-xl animate-pulse"></div>
						<div class="h-20 bg-gray-100 rounded-xl animate-pulse"></div>
						<div class="h-20 bg-gray-100 rounded-xl animate-pulse"></div>
						<div class="h-20 bg-gray-100 rounded-xl animate-pulse"></div>
					</div>

					<!-- Socials Skeleton -->
					<div class="flex gap-4 justify-center pt-4 border-t border-gray-100">
						<div class="w-10 h-10 bg-gray-100 rounded-full animate-pulse"></div>
						<div class="w-10 h-10 bg-gray-100 rounded-full animate-pulse"></div>
						<div class="w-10 h-10 bg-gray-100 rounded-full animate-pulse"></div>
						<div class="w-10 h-10 bg-gray-100 rounded-full animate-pulse"></div>
					</div>
				</div>
			{:else if memberDetail}
				<!-- Header Image (Left Side) -->
				<div class="relative h-80 md:h-full">
					<img src={memberDetail.img} alt={memberDetail.name} class="w-full h-full object-cover" />
					<div
						class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent"
					></div>

					<!-- Name & Gen -->
					<div class="absolute bottom-0 left-0 w-full p-6">
						<span
							class="inline-block px-2 py-0.5 rounded-md bg-red-600/90 text-[10px] font-bold text-white mb-2"
						>
							Generation {memberDetail.generation}
						</span>
						<h3 class="text-3xl font-black text-white leading-tight mb-1">
							{memberDetail.name}
						</h3>
						<p class="text-gray-300 font-medium text-lg">{memberDetail.nickname}</p>
					</div>

					<button
						class="absolute top-4 left-4 bg-black/20 hover:bg-black/40 text-white p-2 rounded-full backdrop-blur-sm transition-colors cursor-pointer md:hidden"
						on:click={closeMemberDetail}
					>
						<X class="w-5 h-5" />
					</button>
				</div>

				<!-- Details (Right Side) -->
				<div class="p-6 space-y-6 relative bg-white dark:bg-zinc-800 flex flex-col justify-center">
					<!-- Desktop Close Button -->
					<button
						class="absolute top-4 right-4 text-gray-400 hover:text-black dark:hover:text-white transition-colors cursor-pointer hidden md:block"
						on:click={closeMemberDetail}
					>
						<X class="w-6 h-6" />
					</button>

					<!-- Jikoshoukai -->
					<div class="bg-red-50 dark:bg-red-900/20 p-5 rounded-2xl relative mt-8 md:mt-0">
						<Quote
							class="w-8 h-8 text-red-100 dark:text-red-800 absolute -top-3 -left-2 transform -scale-x-100"
						/>
						<p
							class="text-sm text-gray-700 dark:text-gray-300 italic relative z-10 text-center leading-relaxed"
						>
							"{memberDetail.jiko}"
						</p>
					</div>

					<!-- Stats Grid -->
					<div class="grid grid-cols-2 gap-4">
						<div
							class="bg-gray-50 dark:bg-zinc-900 p-3 rounded-xl border border-gray-100 dark:border-zinc-700"
						>
							<p class="text-[10px] font-bold text-gray-400 uppercase mb-1">
								{$t('member.birthdate')}
							</p>
							<p class="text-sm font-bold text-gray-800 dark:text-gray-200">
								{memberDetail.birthdate}
								<span class="text-xs text-gray-500 dark:text-gray-400 font-normal block">
									{calculateAge(memberDetail.birthdate)}
									{$t('member.yearsOld')}
								</span>
							</p>
						</div>
						<div
							class="bg-gray-50 dark:bg-zinc-900 p-3 rounded-xl border border-gray-100 dark:border-zinc-700"
						>
							<p class="text-[10px] font-bold text-gray-400 uppercase mb-1">
								{$t('member.horoscope')}
							</p>
							<p class="text-sm font-bold text-gray-800 dark:text-gray-200">
								{memberDetail.horoscope}
							</p>
						</div>
						<div
							class="bg-gray-50 dark:bg-zinc-900 p-3 rounded-xl border border-gray-100 dark:border-zinc-700"
						>
							<p class="text-[10px] font-bold text-gray-400 uppercase mb-1">
								{$t('member.bloodType')}
							</p>
							<p class="text-sm font-bold text-gray-800 dark:text-gray-200">
								{memberDetail.bloodType}
							</p>
						</div>
						<div
							class="bg-gray-50 dark:bg-zinc-900 p-3 rounded-xl border border-gray-100 dark:border-zinc-700"
						>
							<p class="text-[10px] font-bold text-gray-400 uppercase mb-1">
								{$t('member.height')}
							</p>
							<p class="text-sm font-bold text-gray-800 dark:text-gray-200">
								{memberDetail.height}
							</p>
						</div>
					</div>

					<!-- Socials -->
					<div
						class="flex items-center justify-center gap-2 pt-2 border-t border-gray-100 dark:border-zinc-700"
					>
						{#if memberDetail.socials.twitter}
							<a
								href={memberDetail.socials.twitter}
								target="_blank"
								rel="noopener noreferrer"
								class="p-2 bg-gray-100 dark:bg-zinc-700 rounded-full text-gray-500 dark:text-gray-400 hover:bg-black hover:text-white transition-colors cursor-pointer"
							>
								<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
									<path
										d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
									/>
								</svg>
							</a>
						{/if}
						{#if memberDetail.socials.instagram}
							<a
								href={memberDetail.socials.instagram}
								target="_blank"
								rel="noopener noreferrer"
								class="p-2 bg-gray-100 dark:bg-zinc-700 rounded-full text-gray-500 dark:text-gray-400 hover:bg-pink-100 dark:hover:bg-pink-900/30 hover:text-pink-600 transition-colors cursor-pointer"
							>
								<Instagram class="w-4 h-4" />
							</a>
						{/if}
						{#if memberDetail.socials.tiktok}
							<a
								href={memberDetail.socials.tiktok}
								target="_blank"
								rel="noopener noreferrer"
								class="p-2 bg-gray-100 dark:bg-zinc-700 rounded-full text-gray-500 dark:text-gray-400 hover:bg-black hover:text-white transition-colors cursor-pointer"
							>
								<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
									<path
										d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"
									/>
								</svg>
							</a>
						{/if}
						{#if memberDetail.socials.idn_app}
							<a
								href={memberDetail.socials.idn_app}
								target="_blank"
								rel="noopener noreferrer"
								class="p-2 bg-gray-100 dark:bg-zinc-700 rounded-full text-gray-500 dark:text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/30 hover:text-red-500 transition-colors cursor-pointer"
								title="IDN App"
							>
								<Smartphone class="w-4 h-4" />
							</a>
						{/if}
						{#if memberDetail.socials.showroom}
							<a
								href={memberDetail.socials.showroom}
								target="_blank"
								rel="noopener noreferrer"
								class="p-2 bg-gray-100 dark:bg-zinc-700 rounded-full text-gray-500 dark:text-gray-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:text-blue-500 transition-colors cursor-pointer"
							>
								<Tv class="w-4 h-4" />
							</a>
						{/if}
						{#if memberDetail.href}
							<a
								href={memberDetail.href.startsWith('http')
									? memberDetail.href
									: `https://jkt48.com${memberDetail.href}`}
								target="_blank"
								rel="noopener noreferrer"
								class="p-2 bg-gray-100 dark:bg-zinc-700 rounded-full text-gray-500 dark:text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/30 hover:text-red-600 transition-colors cursor-pointer"
								title="Official Profile"
							>
								<Globe class="w-4 h-4" />
							</a>
						{/if}
					</div>
				</div>
			{:else}
				<!-- Error State -->
				<div
					class="col-span-2 p-12 flex flex-col items-center justify-center min-h-[400px] text-center"
				>
					<div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
						<Search class="w-8 h-8 text-red-500" />
					</div>
					<h3 class="text-xl font-bold text-gray-900 mb-2">{$t('member.notFound')}</h3>
					<p class="text-gray-500 max-w-xs mx-auto mb-6">
						{$t('member.notFoundMessage')}
					</p>
					<button
						class="px-6 py-2.5 bg-gray-900 text-white rounded-xl hover:bg-black transition-colors font-medium cursor-pointer"
						on:click={closeMemberDetail}
					>
						{$t('member.close')}
					</button>
				</div>
			{/if}
		</div>
	</div>
{/if}
