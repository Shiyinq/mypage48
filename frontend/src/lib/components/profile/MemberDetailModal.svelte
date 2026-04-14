<script lang="ts">
	import { X, Quote, Instagram, Smartphone, Tv, Globe, Search } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatDate } from '$lib/i18n';
	import type { Member } from '$lib/apis/members';
	import { fade, scale } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import { portal } from '$lib/actions/portal';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { tick } from 'svelte';
	import { getMemberFrame } from '$lib/constants';

	let sidebarScrollContainer: HTMLDivElement | undefined = $state();
	interface Props {
		show?: boolean;
		member?: Member | null;
		members?: Member[];
		loading?: boolean;
		onClose: () => void;
	}

	let { show = false, member = null, members = [], loading = false, onClose }: Props = $props();

	const { t } = useTranslation();

	let internalMemberId: string | number | null = $state(null);
	let direction = $state(1);

	function selectMember(m: Member) {
		if (internalMemberId === m.id) return;
		const currentIndex = members.findIndex((item) => item.id === internalMemberId);
		const nextIndex = members.findIndex((item) => item.id === m.id);
		direction = nextIndex > currentIndex ? 1 : -1;
		internalMemberId = m.id;
	}

	let activeTab: 'Member' | 'Trainee' = $state('Member');
	let activeTabSetFor: string | number | null = $state(null);

	function switchTab(tab: 'Member' | 'Trainee') {
		if (activeTab === tab) return;
		activeTab = tab;
		const firstInTab = members.find((m) => {
			const type = m.member_type?.toLowerCase() || 'member';
			if (tab === 'Trainee') return type === 'trainee';
			return type !== 'trainee';
		});
		if (firstInTab) {
			selectMember(firstInTab);
		}
	}

	// Custom Tinder-like swipe transition
	function tinderSwipe(node: HTMLElement, { duration = 500, isOut = false, dir = 1 }) {
		return {
			duration,
			css: (t: number, u: number) => {
				// u goes from 0 to 1 during the transition
				// t goes from 1 to 0 during 'out', and 0 to 1 during 'in'

				if (dir === 1) {
					// Forward (Next): Top card swipes away RIGHT, new card SCALE UP from behind
					if (isOut) {
						const xMove = u * 500;
						const rotate = u * 30;
						const yMove = u * 50; // slight drop
						return `
							transform: translateX(${xMove}px) translateY(${yMove}px) rotate(${rotate}deg);
							opacity: ${t};
							z-index: 20;
						`;
					} else {
						// Incoming card scale up from center/bottom (Keep opaque to cover background)
						const scale = 0.9 + t * 0.1;
						return `
							transform: scale(${scale});
							opacity: 1;
							z-index: 10;
						`;
					}
				} else {
					// Backward (Previous): Top card swiped back IN from RIGHT, current card SCALE DOWN to behind
					if (isOut) {
						// Outgoing card scales down to go behind
						const scale = 1 - u * 0.1;
						return `
							transform: scale(${scale});
							opacity: ${t};
							z-index: 10;
						`;
					} else {
						// Incoming card swipes in from right and tilts (Keep opaque to cover current)
						const xMove = (1 - t) * 500;
						const rotate = (1 - t) * 30;
						const yMove = (1 - t) * 50;
						return `
							transform: translateX(${xMove}px) translateY(${yMove}px) rotate(${rotate}deg);
							opacity: 1;
							z-index: 20;
						`;
					}
				}
			}
		};
	}

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
	$effect(() => {
		if (show && member && !internalMemberId) {
			internalMemberId = member.id;
		}
	});
	$effect(() => {
		if (!show) {
			internalMemberId = null;
		}
	});
	let currentMember = $derived(members.find((m) => m.id === internalMemberId) || member);
	$effect(() => {
		if (show && currentMember && activeTabSetFor !== currentMember.id) {
			const type = currentMember.member_type?.toLowerCase() || 'member';
			activeTab = type === 'trainee' ? 'Trainee' : 'Member';
			activeTabSetFor = currentMember.id;
		}
	});
	$effect(() => {
		if (activeTab && sidebarScrollContainer) {
			tick().then(() => {
				sidebarScrollContainer?.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
			});
		}
	});
	$effect(() => {
		if (!show) activeTabSetFor = null;
	});
	let displayMembers = $derived(
		members.filter((m) => {
			const type = m.member_type?.toLowerCase() || 'member';
			if (activeTab === 'Trainee') return type === 'trainee';
			return type !== 'trainee';
		})
	);
	let currentIndex = $derived(displayMembers.findIndex((m) => m.id === currentMember?.id));
	let nextMember = $derived(
		displayMembers.length > 1 ? displayMembers[(currentIndex + 1) % displayMembers.length] : null
	);
	let nextNextMember = $derived(
		displayMembers.length > 2 ? displayMembers[(currentIndex + 2) % displayMembers.length] : null
	);
	let frameImg = $derived(getMemberFrame(currentMember?.member_type));
</script>

{#if show}
	<div
		class="fixed inset-0 z-[9999] flex items-center justify-center p-4 overflow-hidden"
		use:portal
	>
		<div
			class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
			onclick={onClose}
			onkeydown={(e) => e.key === 'Escape' && onClose()}
			transition:fade={{ duration: 200 }}
			role="button"
			tabindex="-1"
			aria-label="Close details"
		></div>

		<!-- Modal Container -->
		<div
			class="relative w-[95vw] max-w-6xl bg-white dark:bg-zinc-900 rounded-[40px] shadow-[0_32px_128px_-16px_rgba(0,0,0,0.3)] overflow-hidden flex flex-col md:flex-row h-[85vh] md:h-[75vh] border border-white/20 dark:border-zinc-800/50"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
			transition:scale={{ duration: 400, start: 0.95, easing: quintOut }}
			role="dialog"
			aria-modal="true"
			tabindex="-1"
		>
			<!-- Sidebar (Left) -->
			{#if members.length > 0}
				<div
					class="w-full md:w-64 bg-gray-50/80 dark:bg-zinc-950/40 backdrop-blur-xl border-b md:border-b-0 md:border-r border-gray-100 dark:border-zinc-800/80 flex flex-col h-auto md:h-full overflow-hidden shrink-0"
				>
					<div
						class="p-4 pb-2 flex items-center justify-around border-b border-gray-100 dark:border-zinc-800/50"
					>
						<button
							class="px-4 py-2 text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-300 cursor-pointer {activeTab ===
							'Member'
								? 'text-red-500 border-b-2 border-red-500'
								: 'text-gray-400 dark:text-zinc-500 hover:text-gray-600'}"
							onclick={() => switchTab('Member')}
						>
							Member
						</button>
						<button
							class="px-4 py-2 text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-300 cursor-pointer {activeTab ===
							'Trainee'
								? 'text-red-500 border-b-2 border-red-500'
								: 'text-gray-400 dark:text-zinc-500 hover:text-gray-600'}"
							onclick={() => switchTab('Trainee')}
						>
							Trainee
						</button>
					</div>
					<div
						bind:this={sidebarScrollContainer}
						class="flex-1 overflow-x-auto md:overflow-y-auto custom-scrollbar p-2 md:p-3 pt-1 md:pt-2"
					>
						<div class="flex flex-row md:flex-col gap-1.5 md:space-y-1">
							{#each displayMembers as m (m.id)}
								<button
									class="text-left px-3 md:px-4 py-1.5 md:py-2 rounded-xl md:rounded-2xl transition-all duration-300 group relative flex items-center justify-between cursor-pointer select-none shrink-0 md:shrink {internalMemberId ===
									m.id
										? 'bg-red-500 text-white shadow-lg shadow-red-500/20'
										: 'bg-white/50 dark:bg-zinc-900/50 md:bg-transparent hover:bg-gray-100 dark:hover:bg-zinc-800/50 text-themed opacity-70 hover:opacity-100 border border-gray-100 dark:border-zinc-800 md:border-none'}"
									onclick={() => selectMember(m)}
								>
									<div class="flex items-center gap-2 md:gap-3 whitespace-nowrap">
										{#if internalMemberId === m.id}
											<div
												class="w-1 md:w-1.5 h-1 md:h-1.5 rounded-full bg-white animate-pulse"
											></div>
										{/if}
										<span class="text-[11px] md:text-sm font-bold tracking-tight">{m.name}</span>
									</div>
								</button>
							{/each}
						</div>
					</div>
				</div>
			{/if}

			<!-- Main Content -->
			<div
				class="flex-1 flex flex-col md:flex-row overflow-y-auto custom-scrollbar md:overflow-hidden relative bg-white dark:bg-zinc-900"
			>
				{#if loading}
					<div class="flex-1 p-12 flex items-center justify-center">
						<div
							class="w-12 h-12 border-4 border-red-500 border-t-transparent rounded-full animate-spin"
						></div>
					</div>
				{:else if currentMember}
					<!-- Card Section (Middle) -->
					<div
						class="relative w-full aspect-[4/5] md:aspect-auto md:h-full shrink-0 md:w-1/2 overflow-hidden bg-gray-50/20 dark:bg-zinc-900/30 flex items-center justify-center border-b border-gray-100 dark:border-zinc-800 md:border-b-0"
					>
						<div
							class="relative w-full md:max-w-[420px] aspect-[4/5] group transition-transform duration-500 hover:scale-[1.02]"
						>
							<!-- Background Stacks (Next Member) - Stable behind the keyed active card -->
							{#if nextNextMember}
								<div
									class="absolute inset-0 bg-zinc-200 dark:bg-zinc-800 rounded-3xl transform -rotate-3 translate-x-2 translate-y-1 md:-rotate-6 md:translate-x-4 md:translate-y-2 opacity-40 shadow-xl transition-all duration-700 overflow-hidden border-[3px] border-white/50 dark:border-zinc-700/50"
								>
									<img
										src={getExternalMediaUrl(nextNextMember.img)}
										alt=""
										class="w-full h-full object-cover object-top grayscale opacity-50"
									/>
								</div>
							{/if}
							{#if nextMember}
								<div
									class="absolute inset-0 bg-zinc-300 dark:bg-zinc-700 rounded-3xl transform rotate-2 -translate-x-2 translate-y-1 md:rotate-3 md:-translate-x-3 md:translate-y-1 opacity-60 shadow-xl transition-all duration-700 overflow-hidden border-[3px] border-white/50 dark:border-zinc-700/50"
								>
									<img
										src={getExternalMediaUrl(nextMember.img)}
										alt=""
										class="w-full h-full object-cover object-top grayscale opacity-50"
									/>
								</div>
							{/if}

							{#key currentMember.id}
								<div
									class="absolute inset-0 flex items-center justify-center p-0"
									in:tinderSwipe={{ duration: 600, dir: direction }}
									out:tinderSwipe={{ duration: 600, isOut: true, dir: direction }}
								>
									<!-- Main Image Container -->
									<div
										class="relative w-full h-full z-10 rounded-3xl overflow-hidden border-x-0 md:border-[6px] border-white dark:border-zinc-800 shadow-2xl bg-white dark:bg-zinc-800"
									>
										<img
											src={getExternalMediaUrl(currentMember.img)}
											alt={currentMember.name}
											class="w-full h-full object-cover object-top grayscale-[10%] group-hover:grayscale-0 transition-all duration-700"
										/>
										<img
											src={frameImg}
											alt="frame"
											class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10 scale-[1.05]"
										/>
									</div>
								</div>
							{/key}
						</div>

						<!-- Mobile Close Button (Top Right of Content) -->
						<button
							class="absolute top-4 right-4 bg-white/10 hover:bg-red-600 text-white p-2 rounded-full backdrop-blur-md transition-all duration-300 cursor-pointer md:hidden z-50 shadow-lg border border-white/20"
							onclick={onClose}
						>
							<X class="w-4 h-4" />
						</button>
					</div>

					<!-- Details Section (Right) -->
					<div
						class="flex-none md:flex-1 md:w-1/2 relative bg-white dark:bg-zinc-900 md:border-l border-gray-100 dark:border-zinc-800 shadow-[-10px_0_30px_rgba(0,0,0,0.02)] flex flex-col"
					>
						<!-- Desktop Close Button -->
						<button
							class="absolute top-6 right-6 text-gray-300 hover:text-red-500 transition-all duration-300 cursor-pointer hidden md:block hover:rotate-90 z-50"
							onclick={onClose}
						>
							<X class="w-6 h-6" />
						</button>

						<div class="flex-1 flex flex-col">
							{#key currentMember.id}
								<div
									class="w-full p-6 md:p-10 space-y-6 flex flex-col md:overflow-y-auto custom-scrollbar pb-24 md:pb-32"
									in:fade={{ duration: 400 }}
									out:fade={{ duration: 300 }}
								>
									<!-- Name Header -->
									<div class="space-y-1">
										<div class="flex items-center gap-3">
											<span
												class="px-2 py-0.5 rounded-md bg-red-600 text-[10px] font-black text-white uppercase tracking-wider"
											>
												{currentMember.member_type || 'Member'}
											</span>
											<span
												class="text-xs font-bold text-gray-400 dark:text-zinc-500 uppercase tracking-widest"
											>
												Gen {currentMember.generation}
											</span>
										</div>
										<h2 class="text-3xl font-black text-themed tracking-tight">
											{currentMember.name}
											<span class="text-red-500 text-xl ml-1">✦</span>
										</h2>
										<p class="text-lg font-bold text-gray-500 dark:text-zinc-400">
											({currentMember.nickname})
										</p>
									</div>

									<!-- Jikoshoukai -->
									<div
										class="bg-gray-50 dark:bg-zinc-800/30 p-6 rounded-[28px] relative border border-gray-100 dark:border-zinc-800/50 group transition-all duration-500"
									>
										<Quote
											class="w-8 h-8 text-red-500/10 dark:text-red-900/20 absolute -top-3 -left-2 transform -scale-x-100"
										/>
										<p
											class="text-sm md:text-base text-gray-700 dark:text-gray-300 italic text-center leading-relaxed font-medium"
										>
											"{currentMember.jiko}"
										</p>
									</div>

									<!-- Stats Grid -->
									<div class="grid grid-cols-2 gap-4">
										<div
											class="bg-gray-50/50 dark:bg-zinc-800/20 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800/50 group hover:border-red-200 dark:hover:border-red-900/30 transition-all duration-300"
										>
											<p
												class="text-[9px] font-black text-gray-400 dark:text-zinc-500 uppercase tracking-widest mb-1.5 group-hover:text-red-500 transition-colors"
											>
												{$t('member.birthdate')}
											</p>
											<p class="text-sm font-black text-themed leading-tight">
												{$formatDate(parseIndonesianDate(currentMember.birthdate), {
													dateStyle: 'medium'
												})}
												<span
													class="text-[10px] text-gray-500 dark:text-zinc-400 font-bold block mt-1 px-2 py-0.5 bg-gray-200/50 dark:bg-zinc-700/50 w-max rounded-full"
													>{calculateAge(currentMember.birthdate)} {$t('member.yearsOld')}</span
												>
											</p>
										</div>
										<div
											class="bg-gray-50/50 dark:bg-zinc-800/20 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800/50 group hover:border-red-200 dark:hover:border-red-900/30 transition-all duration-300"
										>
											<p
												class="text-[9px] font-black text-gray-400 dark:text-zinc-500 uppercase tracking-widest mb-1.5 group-hover:text-red-500 transition-colors"
											>
												{$t('member.horoscope')}
											</p>
											<p class="text-sm font-black text-themed leading-tight">
												{currentMember.horoscope}
											</p>
										</div>
										<div
											class="bg-gray-50/50 dark:bg-zinc-800/20 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800/50 group hover:border-red-200 dark:hover:border-red-900/30 transition-all duration-300"
										>
											<p
												class="text-[9px] font-black text-gray-400 dark:text-zinc-500 uppercase tracking-widest mb-1.5 group-hover:text-red-500 transition-colors"
											>
												{$t('member.bloodType')}
											</p>
											<p class="text-sm font-black text-themed leading-tight">
												{currentMember.bloodType}
											</p>
										</div>
										<div
											class="bg-gray-50/50 dark:bg-zinc-800/20 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800/50 group hover:border-red-200 dark:hover:border-red-900/30 transition-all duration-300"
										>
											<p
												class="text-[9px] font-black text-gray-400 dark:text-zinc-500 uppercase tracking-widest mb-1.5 group-hover:text-red-500 transition-colors"
											>
												{$t('member.height')}
											</p>
											<p class="text-sm font-black text-themed leading-tight">
												{currentMember.height?.toString().toLowerCase().includes('cm')
													? currentMember.height
													: currentMember.height + 'cm'}
											</p>
										</div>
									</div>
								</div>

								<!-- Sticky Social Footer -->
								<div
									class="absolute bottom-0 inset-x-0 p-4 md:p-6 bg-gradient-to-t from-white via-white/95 to-transparent dark:from-zinc-900 dark:via-zinc-900/95 dark:to-transparent border-t border-gray-100/50 dark:border-zinc-800/50 flex items-center justify-center gap-4 z-40"
									in:fade={{ delay: 200, duration: 400 }}
								>
									{#if currentMember.socials.twitter}
										<a
											href={currentMember.socials.twitter}
											target="_blank"
											rel="noopener noreferrer"
											aria-label="Twitter / X profile"
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-black hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm"
											><svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"
												><path
													d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
												/></svg
											></a
										>
									{/if}
									{#if currentMember.socials.instagram}
										<a
											href={currentMember.socials.instagram}
											target="_blank"
											rel="noopener noreferrer"
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-pink-600 hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm"
											><Instagram class="w-4 h-4" /></a
										>
									{/if}
									{#if currentMember.socials.tiktok}
										<a
											href={currentMember.socials.tiktok}
											target="_blank"
											rel="noopener noreferrer"
											aria-label="TikTok profile"
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-black hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm font-bold"
										>
											<svg class="w-4 h-4 fill-current" viewBox="0 0 24 24"
												><path
													d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.06-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.1-3.34-3.12-3.35-5.47-.03-2.43 1.4-4.71 3.61-5.7 1.11-.53 2.33-.78 3.56-.7v4.26c-.15-.05-.31-.07-.46-.09-1.49-.22-3.08.75-3.39 2.22-.2 1.05.21 2.18 1.03 2.87.89.73 2.15.8 3.2.4 1.18-.5 1.88-1.76 1.87-3.01.01-6.19-.01-12.38.01-18.57z"
												/></svg
											>
										</a>
									{/if}
									{#if currentMember.socials.idn_app}
										<a
											href={currentMember.socials.idn_app}
											target="_blank"
											rel="noopener noreferrer"
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-red-600 hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm"
											><Smartphone class="w-4 h-4" /></a
										>
									{/if}
									{#if currentMember.socials.showroom}
										<a
											href={currentMember.socials.showroom}
											target="_blank"
											rel="noopener noreferrer"
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-blue-600 hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm"
											><Tv class="w-4 h-4" /></a
										>
									{/if}
									{#if currentMember.href}
										<a
											href={currentMember.href.startsWith('http')
												? currentMember.href
												: `https://jkt48.com${currentMember.href}`}
											target="_blank"
											rel="noopener noreferrer"
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-red-700 hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm"
											title="Official Profile"><Globe class="w-4 h-4" /></a
										>
									{/if}
								</div>
							{/key}
						</div>
					</div>
				{:else}
					<div
						class="col-span-2 p-12 flex flex-col items-center justify-center min-h-[400px] text-center"
					>
						<div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
							<Search class="w-8 h-8 text-red-500" />
						</div>
						<h3 class="text-xl font-bold text-gray-900 mb-2">{$t('member.notFound')}</h3>
						<p class="text-gray-500 max-w-xs mx-auto mb-6">{$t('member.notFoundMessage')}</p>
						<button
							class="px-6 py-2.5 bg-gray-900 text-white rounded-xl hover:bg-black transition-colors font-medium cursor-pointer"
							onclick={onClose}>{$t('member.close')}</button
						>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(0, 0, 0, 0.1);
		border-radius: 10px;
	}
	:global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.1);
	}
</style>
