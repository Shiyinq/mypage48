<script lang="ts">
	import { X, Quote, Instagram, Smartphone, Tv, Globe, Search } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { Member } from '$lib/apis/members';
	import { fade, scale } from 'svelte/transition';
	import { portal } from '$lib/actions/portal';

	export let show: boolean = false;
	export let member: Member | null = null;
	export let loading: boolean = false;
	export let onClose: () => void;

	const { t } = useTranslation();

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

{#if show}
	<div class="fixed inset-0 z-[9999] flex items-center justify-center p-4" use:portal>
		<!-- svelte-ignore a11y-click-events-have-key-events  a11y-no-static-element-interactions -->
		<div
			class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
			on:click={onClose}
			transition:fade={{ duration: 200 }}
		></div>

		<div
			class="bg-white rounded-3xl w-full max-w-3xl overflow-hidden relative z-10 shadow-2xl grid md:grid-cols-2"
			transition:scale={{ duration: 200, start: 0.95 }}
		>
			{#if loading}
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
			{:else if member}
				<!-- Header Image (Left Side) -->
				<div class="relative h-80 md:h-full">
					<img src={member.img} alt={member.name} class="w-full h-full object-cover" />
					<div
						class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent"
					></div>

					<!-- Name & Gen -->
					<div class="absolute bottom-0 left-0 w-full p-6">
						<span
							class="inline-block px-2 py-0.5 rounded-md bg-red-600/90 text-[10px] font-bold text-white mb-2"
						>
							Generation {member.generation}
						</span>
						<h3 class="text-3xl font-black text-white leading-tight mb-1">
							{member.name}
						</h3>
						<p class="text-gray-300 font-medium text-lg">{member.nickname}</p>
					</div>

					<button
						class="absolute top-4 left-4 bg-black/20 hover:bg-black/40 text-white p-2 rounded-full backdrop-blur-sm transition-colors cursor-pointer md:hidden"
						on:click={onClose}
					>
						<X class="w-5 h-5" />
					</button>
				</div>

				<!-- Details (Right Side) -->
				<div class="p-6 space-y-6 relative bg-white dark:bg-zinc-800 flex flex-col justify-center">
					<!-- Desktop Close Button -->
					<button
						class="absolute top-4 right-4 text-gray-400 hover:text-black dark:hover:text-white transition-colors cursor-pointer hidden md:block"
						on:click={onClose}
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
							"{member.jiko}"
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
								{member.birthdate}
								<span class="text-xs text-gray-500 dark:text-gray-400 font-normal block">
									{calculateAge(member.birthdate)}
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
								{member.horoscope}
							</p>
						</div>
						<div
							class="bg-gray-50 dark:bg-zinc-900 p-3 rounded-xl border border-gray-100 dark:border-zinc-700"
						>
							<p class="text-[10px] font-bold text-gray-400 uppercase mb-1">
								{$t('member.bloodType')}
							</p>
							<p class="text-sm font-bold text-gray-800 dark:text-gray-200">
								{member.bloodType}
							</p>
						</div>
						<div
							class="bg-gray-50 dark:bg-zinc-900 p-3 rounded-xl border border-gray-100 dark:border-zinc-700"
						>
							<p class="text-[10px] font-bold text-gray-400 uppercase mb-1">
								{$t('member.height')}
							</p>
							<p class="text-sm font-bold text-gray-800 dark:text-gray-200">
								{member.height}
							</p>
						</div>
					</div>

					<!-- Socials -->
					<div
						class="flex items-center justify-center gap-2 pt-2 border-t border-gray-100 dark:border-zinc-700"
					>
						{#if member.socials.twitter}
							<a
								href={member.socials.twitter}
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
						{#if member.socials.instagram}
							<a
								href={member.socials.instagram}
								target="_blank"
								rel="noopener noreferrer"
								class="p-2 bg-gray-100 dark:bg-zinc-700 rounded-full text-gray-500 dark:text-gray-400 hover:bg-pink-100 dark:hover:bg-pink-900/30 hover:text-pink-600 transition-colors cursor-pointer"
							>
								<Instagram class="w-4 h-4" />
							</a>
						{/if}
						{#if member.socials.tiktok}
							<a
								href={member.socials.tiktok}
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
						{#if member.socials.idn_app}
							<a
								href={member.socials.idn_app}
								target="_blank"
								rel="noopener noreferrer"
								class="p-2 bg-gray-100 dark:bg-zinc-700 rounded-full text-gray-500 dark:text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/30 hover:text-red-500 transition-colors cursor-pointer"
								title="IDN App"
							>
								<Smartphone class="w-4 h-4" />
							</a>
						{/if}
						{#if member.socials.showroom}
							<a
								href={member.socials.showroom}
								target="_blank"
								rel="noopener noreferrer"
								class="p-2 bg-gray-100 dark:bg-zinc-700 rounded-full text-gray-500 dark:text-gray-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:text-blue-500 transition-colors cursor-pointer"
							>
								<Tv class="w-4 h-4" />
							</a>
						{/if}
						{#if member.href}
							<a
								href={member.href.startsWith('http')
									? member.href
									: `https://jkt48.com${member.href}`}
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
						on:click={onClose}
					>
						{$t('member.close')}
					</button>
				</div>
			{/if}
		</div>
	</div>
{/if}
