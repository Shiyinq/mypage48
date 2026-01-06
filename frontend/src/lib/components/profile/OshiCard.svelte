<script lang="ts">
	import { Dices, Cake, Search, Plus, Heart, Info, Instagram, Smartphone, Tv } from 'lucide-svelte';
	import Button from '$lib/components/Button.svelte';
	import type { User } from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let profile: User | null = null;
	export let loading: boolean = true;
	export let rouletteCount: number = 0;
	export let birthdayCount: number = 0;
	export let onOpenOshiModal: () => void;
	export let onOpenMemberDetail: () => void;

	const { t } = useTranslation();
</script>

<div class="glass-panel p-0 rounded-3xl overflow-hidden relative">
	<!-- Banner -->
	<div
		class="h-32 w-full bg-[url('https://upload.wikimedia.org/wikipedia/commons/5/53/JKT48_Logo_-_Red_Background_%282016%29.png')] bg-cover bg-center relative"
	>
		<div class="absolute inset-0 bg-gradient-to-t from-white via-white/50 to-transparent"></div>
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
					<div class="h-16 w-full bg-gray-100 dark:bg-zinc-800 rounded-xl animate-pulse mt-2"></div>

					<!-- Socials Skeleton -->
					<div class="flex gap-2 mt-3 justify-center md:justify-start">
						<div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
						<div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
						<div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
					</div>
				</div>
			</div>
		{:else if profile?.oshi}
			<div class="flex flex-col md:flex-row items-center md:items-end gap-6 -mt-16">
				<!-- Avatar with Glow -->
				<div class="relative">
					<button
						class="relative w-28 h-28 rounded-full border-4 border-white shadow-xl overflow-hidden flex-shrink-0 cursor-pointer transition-transform hover:scale-105 active:scale-95"
						on:click={onOpenMemberDetail}
					>
						<img
							src={profile?.oshi?.profilePicture || '/placeholder-user.jpg'}
							alt={profile?.oshi?.name}
							class="w-full h-full object-cover"
						/>
						<div
							class="absolute inset-0 bg-black/0 hover:bg-black/10 transition-colors flex items-center justify-center opacity-0 hover:opacity-100"
						>
							<Info class="w-8 h-8 text-white drop-shadow-md" />
						</div>
					</button>
					<div
						class="absolute -bottom-3 left-1/2 transform -translate-x-1/2 z-20 pointer-events-none"
					>
						<div
							class="bg-pink-500 text-white pl-2 pr-3 py-1 rounded-full text-[10px] font-bold shadow-lg flex items-center gap-1 whitespace-nowrap border-2 border-white dark:border-gray-800"
						>
							<Heart class="w-3 h-3 fill-current animate-pulse" />
							<span>My Oshi</span>
						</div>
					</div>
				</div>

				<!-- Info -->
				<div class="text-center md:text-left flex-1 min-w-0">
					<div class="flex flex-col items-center md:items-start gap-1 mb-2">
						<div class="flex items-center gap-2">
							<h3 class="text-2xl font-black text-gray-800 leading-tight">
								{profile?.oshi?.name}
							</h3>
							<button
								on:click={onOpenOshiModal}
								class="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors cursor-pointer"
								title="Change Oshi"
							>
								<Search class="w-4 h-4" />
							</button>
						</div>
						<span
							class="px-2 py-0.5 bg-red-100 text-red-600 text-[10px] font-bold rounded-md uppercase tracking-wide border border-red-200 whitespace-nowrap"
						>
							Generation {profile?.oshi?.generation}
						</span>
					</div>

					<!-- Catchphrase Bubble -->
					<div
						class="relative bg-gray-50 dark:bg-zinc-900 p-3 rounded-xl rounded-tl-none border border-gray-100 dark:border-zinc-800 shadow-sm mt-2 inline-block"
					>
						<p class="text-xs text-gray-600 dark:text-gray-400 italic font-medium">
							"{profile?.oshi?.catchphrase}"
						</p>
					</div>

					<!-- Socials -->
					{#if profile?.oshi?.socials}
						<div class="flex flex-wrap justify-center md:justify-start gap-2 mt-3">
							{#if profile?.oshi?.socials?.twitter}
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
							{#if profile?.oshi?.socials?.instagram}
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
							{#if profile?.oshi?.socials?.tiktok}
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
							{#if profile?.oshi?.socials?.idn_app}
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
							{#if profile?.oshi?.socials?.showroom}
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
				<div class="relative mb-4 group cursor-pointer">
					<button
						on:click={onOpenOshiModal}
						class="w-24 h-24 rounded-full bg-white dark:bg-zinc-800 shadow-lg flex items-center justify-center border-4 border-dashed border-gray-200 dark:border-zinc-700 group-hover:border-red-300 transition-colors cursor-pointer"
					>
						<Plus class="w-8 h-8 text-gray-300 group-hover:text-red-400" />
					</button>
					<div
						class="absolute -bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 bg-red-500 text-white text-xs font-bold rounded-full shadow-lg transform scale-90 group-hover:scale-100 transition-transform pointer-events-none"
					>
						Select Oshi
					</div>
				</div>
				<h3 class="text-lg font-bold text-gray-700 dark:text-gray-300">Who is your Oshi?</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400 max-w-xs mx-auto mt-1">
					Select your favorite member to display them on your profile card.
				</p>
				<div class="mt-4">
					<Button size="sm" variant="outline" on:click={onOpenOshiModal}>Browse Members</Button>
				</div>
			</div>
		{/if}

		{#if profile?.oshi}
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
								{rouletteCount}
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
								{birthdayCount}
							{/if}
						</p>
						<p class="text-[10px] font-bold text-gray-400 uppercase">
							{$t('profile.oshi.birthday')}
						</p>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>
