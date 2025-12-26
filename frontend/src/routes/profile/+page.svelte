<script lang="ts">
	import { onMount } from 'svelte';
	import { isAuthenticated } from '$lib/stores';
	import { goto } from '$app/navigation';
	import {
		User,
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
		Award
	} from 'lucide-svelte';
	import { auth } from '$lib/apis/auth';
	import { theater } from '$lib/apis/theater';
	import { showToast } from '$lib/stores';
	import type { Ticket } from '$lib/types';

	// Profile data from API
	interface ProfileData {
		userId: string;
		profilePicture: string | null;
		name: string;
		email: string;
		username: string;
		memberId: string | null;
		ofcStatus: string | null;
	}

	let profile: ProfileData | null = null;
	let tickets: Ticket[] = [];
	let recentShows: Ticket[] = [];
	let loading = true;

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

	$: oshiVisits = tickets.length; // For now, same as total shows

	// Static data for level (can be dynamic later)
	const level = {
		current: 'Wota Elite',
		xp: 2450,
		nextLevelXp: 3000,
		rank: 12
	};

	// Static oshimen data (can be dynamic later)
	const oshimen = {
		name: 'Oline Manuel',
		nickname: 'Oline',
		generation: '12th Gen',
		imageUrl: 'https://jkt48.com/profile/oline_manuel.jpg',
		catchphrase:
			'Seperti kembang api yang bersinar indah, aku ingin menerangi harimu! Halo aku Oline!'
	};

	// Calculate Progress
	$: progressPercent = (level.xp / level.nextLevelXp) * 100;

	// Format date for Recent Activity
	function formatActivityDate(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

		if (diffDays === 0) return 'Today';
		if (diffDays === 1) return 'Yesterday';
		if (diffDays < 7) return `${diffDays} days ago`;
		if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	onMount(async () => {
		try {
			// Fetch profile and tickets in parallel
			const [profileData, ticketsData] = await Promise.all([
				auth.getProfile(),
				theater.getMyTickets()
			]);

			// Map profile data
			profile = {
				userId: (profileData as any).userId || '',
				profilePicture: (profileData as any).profilePicture || null,
				name: (profileData as any).name || '',
				email: (profileData as any).email || '',
				username: (profileData as any).username || '',
				memberId: (profileData as any).memberId || null,
				ofcStatus: (profileData as any).ofcStatus || null
			};

			tickets = ticketsData || [];

			// Sort tickets by event date descending and get 5 most recent
			recentShows = [...tickets]
				.sort((a, b) => new Date(b.event.date).getTime() - new Date(a.event.date).getTime())
				.slice(0, 5);
		} catch (e) {
			console.error('Error loading profile data:', e);
		} finally {
			loading = false;
		}
	});

	const logout = async () => {
		try {
			await auth.logout();
			showToast('Logged out successfully', 'success');
		} catch (e) {
			console.error('Logout error', e);
			// Even if backend fails, force local logout
		} finally {
			isAuthenticated.set(false);
			goto('/login');
		}
	};
</script>

<div class="max-w-5xl mx-auto p-4 animate-fade-in pb-24">
	<!-- Page Header -->
	<div class="flex items-center justify-between mb-8">
		<div class="flex items-center gap-3">
			<div
				class="p-3 rounded-2xl bg-red-50 text-red-600 shadow-lg shadow-red-100 border-2 border-white transform -rotate-6"
			>
				<User class="w-6 h-6" />
			</div>
			<div>
				<h2 class="text-2xl font-black idol-text-gradient leading-none relative w-fit">
					My Profile
					<span
						class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 -z-10 transform -skew-x-12 rounded-sm"
					></span>
				</h2>
				<p class="text-sm text-gray-500 mt-1">Fan Identity & Stats</p>
			</div>
		</div>
		<div class="flex items-center gap-3">
			<div
				class="hidden md:flex items-center gap-2 bg-white px-3 py-1.5 rounded-full border border-gray-200 shadow-sm"
			>
				<span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
				<span class="text-xs font-bold text-gray-600">OFC Active</span>
			</div>

			<!-- Logout Button -->
			<button
				on:click={logout}
				class="p-2 rounded-full bg-gray-100 text-gray-500 hover:bg-red-50 hover:text-red-600 transition-colors border border-transparent hover:border-red-100"
				title="Logout"
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
					class="relative h-56 w-full rounded-3xl overflow-hidden shadow-2xl transition-transform duration-500 group-hover:scale-[1.02]"
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
										Official Fan Club
									</p>
									<h3 class="font-black text-lg tracking-tight">
										MYPAGE<span class="text-red-500">48</span>
									</h3>
								</div>
							</div>
							<div class="text-right">
								<p class="text-[10px] text-gray-400 font-bold">MEMBER ID</p>
								<p class="font-mono font-bold text-shadow">
									{#if loading}
										<span class="inline-block w-20 h-4 bg-white/20 rounded animate-pulse"></span>
									{:else}
										{profile?.memberId || 'N/A'}
									{/if}
								</p>
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
								<p class="text-[10px] text-gray-400 font-bold uppercase mb-0.5">Card Holder</p>
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
			<div class="glass-panel p-6 rounded-3xl relative overflow-hidden">
				<div class="flex justify-between items-end mb-2">
					<div>
						<p class="text-xs font-bold text-gray-400 uppercase">Current Rank</p>
						<h3 class="text-2xl font-black idol-text-gradient">{level.current}</h3>
					</div>
					<div class="text-right">
						<p class="text-xs font-bold text-gray-500">
							<span class="text-red-600">{level.xp}</span> / {level.nextLevelXp} XP
						</p>
					</div>
				</div>

				<!-- Progress Bar -->
				<div class="h-3 w-full bg-gray-100 rounded-full overflow-hidden shadow-inner mb-4">
					<div class="h-full idol-gradient rounded-full relative" style="width: {progressPercent}%">
						<div
							class="absolute inset-0 bg-[linear-gradient(45deg,rgba(255,255,255,0.2)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.2)_50%,rgba(255,255,255,0.2)_75%,transparent_75%,transparent)] bg-[length:1rem_1rem] animate-[pulse_1s_linear_infinite]"
						></div>
					</div>
				</div>

				<div
					class="flex items-center gap-2 text-xs text-gray-500 font-medium bg-gray-50 p-2 rounded-lg border border-gray-100"
				>
					<Sparkles class="w-3.5 h-3.5 text-yellow-500" />
					<span>550 XP needed for <span class="font-bold text-gray-700">Legendary Wota</span></span>
				</div>
			</div>

			<!-- QUICK STATS -->
			<div class="grid grid-cols-2 gap-4">
				<div
					class="glass-panel p-4 rounded-2xl flex flex-col items-center justify-center text-center"
				>
					<div
						class="w-8 h-8 rounded-full bg-red-50 text-red-600 flex items-center justify-center mb-2"
					>
						<Trophy class="w-4 h-4" />
					</div>
					{#if loading}
						<span class="inline-block w-10 h-7 bg-gray-200 rounded animate-pulse"></span>
					{:else}
						<span class="text-2xl font-black text-gray-800">{totalShows}</span>
					{/if}
					<span class="text-[10px] font-bold text-gray-400 uppercase">Total Shows</span>
				</div>
				<div
					class="glass-panel p-4 rounded-2xl flex flex-col items-center justify-center text-center"
				>
					<div
						class="w-8 h-8 rounded-full bg-yellow-50 text-yellow-600 flex items-center justify-center mb-2"
					>
						<Star class="w-4 h-4" />
					</div>
					{#if loading}
						<span class="inline-block w-10 h-7 bg-gray-200 rounded animate-pulse"></span>
					{:else}
						<span class="text-2xl font-black text-gray-800">{totalAchievements}</span>
					{/if}
					<span class="text-[10px] font-bold text-gray-400 uppercase">Achievements</span>
				</div>
			</div>
		</div>

		<!-- RIGHT COLUMN: Oshimen & Feed (Span 7) -->
		<div class="lg:col-span-7 space-y-6">
			<!-- OSHI SHRINE -->
			<div class="glass-panel p-0 rounded-3xl overflow-hidden relative">
				<!-- Banner -->
				<div
					class="h-32 w-full bg-[url('https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80/https://jkt48.com/images/banner.home.jpg')] bg-cover bg-center relative"
				>
					<div
						class="absolute inset-0 bg-gradient-to-t from-white via-white/50 to-transparent"
					></div>
				</div>

				<div class="px-6 md:px-8 pb-6 relative">
					<div class="flex flex-col md:flex-row items-center md:items-end gap-6 -mt-16">
						<!-- Avatar with Glow -->
						<div class="relative">
							<div
								class="absolute inset-0 bg-red-500 rounded-full blur-md opacity-30 animate-pulse"
							></div>
							<div class="w-32 h-32 rounded-full p-1 bg-white shadow-xl relative z-10">
								<img
									src={oshimen.imageUrl}
									alt={oshimen.name}
									class="w-full h-full rounded-full object-cover"
								/>
								<div
									class="absolute bottom-1 right-1 bg-red-500 text-white p-1.5 rounded-full border-2 border-white shadow-md"
								>
									<Heart class="w-4 h-4 fill-current" />
								</div>
							</div>
						</div>

						<!-- Info -->
						<div class="text-center md:text-left flex-1">
							<div class="flex flex-col md:flex-row items-center gap-2 mb-1">
								<h3 class="text-2xl font-black text-gray-800">{oshimen.name}</h3>
								<span
									class="px-2 py-0.5 bg-red-100 text-red-600 text-[10px] font-bold rounded-md uppercase tracking-wide border border-red-200"
								>
									{oshimen.generation}
								</span>
							</div>

							<!-- Catchphrase Bubble -->
							<div
								class="relative bg-gray-50 p-3 rounded-xl rounded-tl-none border border-gray-100 shadow-sm mt-2 inline-block"
							>
								<p class="text-xs text-gray-600 italic font-medium">
									"{oshimen.catchphrase}"
								</p>
							</div>
						</div>
					</div>

					<div class="mt-6 grid grid-cols-3 gap-3 border-t border-gray-100 pt-4">
						<!-- StatItem Inline -->
						<div class="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 transition-colors">
							<div class="p-2 rounded-full bg-white shadow-sm border border-gray-100 text-red-500">
								<MapPin class="w-4 h-4" />
							</div>
							<div>
								<p class="text-lg font-black text-gray-800 leading-none">
									{#if loading}
										<span class="inline-block w-6 h-5 bg-gray-200 rounded animate-pulse"></span>
									{:else}
										{oshiVisits}
									{/if}
								</p>
								<p class="text-[10px] font-bold text-gray-400 uppercase">Oshi Visits</p>
							</div>
						</div>
						<div class="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 transition-colors">
							<div class="p-2 rounded-full bg-white shadow-sm border border-gray-100 text-pink-500">
								<Heart class="w-4 h-4" />
							</div>
							<div>
								<p class="text-lg font-black text-gray-800 leading-none">8</p>
								<p class="text-[10px] font-bold text-gray-400 uppercase">Handshakes</p>
							</div>
						</div>
						<div class="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 transition-colors">
							<div
								class="p-2 rounded-full bg-white shadow-sm border border-gray-100 text-yellow-500"
							>
								<Zap class="w-4 h-4" />
							</div>
							<div>
								<p class="text-lg font-black text-gray-800 leading-none">3</p>
								<p class="text-[10px] font-bold text-gray-400 uppercase">2-Shot</p>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- RECENT ACTIVITY FEED -->
			<div class="glass-panel p-6 rounded-3xl">
				<h4 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
					<TrendingUp class="w-4 h-4 text-red-500" /> Recent Activity
				</h4>

				<div
					class="space-y-4 relative before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-100"
				>
					{#if loading}
						<!-- Skeleton Loading for Activity Items -->
						{#each [1, 2, 3] as _}
							<div class="flex gap-4 relative z-10">
								<div class="w-10 h-10 rounded-full flex-shrink-0 bg-gray-200 animate-pulse"></div>
								<div class="flex-1 bg-white/50 p-3 rounded-xl border border-gray-50">
									<div class="flex justify-between items-start mb-2">
										<div class="h-4 bg-gray-200 rounded w-2/3 animate-pulse"></div>
										<div class="h-3 bg-gray-200 rounded w-16 animate-pulse"></div>
									</div>
									<div class="h-3 bg-gray-200 rounded w-1/3 animate-pulse"></div>
								</div>
							</div>
						{/each}
					{:else if recentShows.length === 0}
						<div class="text-center py-8 text-gray-500">
							<Music class="w-8 h-8 mx-auto mb-2 text-gray-300" />
							<p class="text-sm">No shows attended yet</p>
							<p class="text-xs text-gray-400">Start tracking your theater visits!</p>
						</div>
					{:else}
						{#each recentShows as show}
							<div class="flex gap-4 relative z-10">
								<div
									class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 border-4 border-white shadow-sm {show.two_shot
										? 'bg-yellow-100 text-yellow-600'
										: 'bg-red-100 text-red-600'}"
								>
									{#if show.two_shot}
										<Zap class="w-4 h-4" />
									{:else}
										<Music class="w-4 h-4" />
									{/if}
								</div>
								<div
									class="flex-1 bg-white/50 p-3 rounded-xl border border-gray-50 hover:bg-white transition-colors"
								>
									<div class="flex justify-between items-start">
										<p class="text-sm font-bold text-gray-800">
											{show.two_shot ? '2-Shot at' : 'Attended'} '{show.event.title}'
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
