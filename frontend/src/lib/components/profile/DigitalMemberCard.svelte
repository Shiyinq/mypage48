<script lang="ts">
	import { Crown, QrCode } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { User } from '$lib/types';

	interface Props {
		profile?: User | null;
		loading?: boolean;
	}

	let { profile = null, loading = true }: Props = $props();

	const { t } = useTranslation();
</script>

<div class="relative group perspective-1000 w-full min-w-0">
	<!-- Card Container -->
	<div
		class="relative h-56 w-full rounded-3xl shadow-2xl transition-transform duration-500 group-hover:scale-[1.02] {profile?.ofcStatus ===
		'Active'
			? 'ring-2 ring-green-400/50 ring-offset-2 ring-offset-white'
			: ''} max-w-full"
	>
		<div class="absolute inset-0 rounded-3xl overflow-hidden">
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
			<div
				class="relative z-10 p-4 sm:p-6 h-full flex flex-col justify-between text-white overflow-hidden"
			>
				<!-- Top Row -->
				<div class="flex justify-between items-start gap-2 min-w-0">
					<div class="flex items-center gap-1.5 sm:gap-2 min-w-0 flex-shrink">
						<div
							class="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center flex-shrink-0"
						>
							<Crown class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-yellow-400" />
						</div>
						<div class="min-w-0">
							<p
								class="text-[10px] sm:text-[11px] font-bold text-red-400 tracking-widest uppercase truncate"
							>
								{$t('profile.memberCard.officialFanClub')}
							</p>
							<h3 class="font-black text-base sm:text-lg tracking-tight truncate">
								MYPAGE<span class="text-red-500">48</span>
							</h3>
						</div>
					</div>
					<div class="flex flex-col items-end gap-1 min-w-0">
						<!-- Member ID -->
						<div class="text-right min-w-0 w-full">
							<p class="text-[10px] sm:text-[11px] text-gray-400 font-bold truncate">
								{$t('profile.memberCard.memberId')}
							</p>
							<p class="font-mono font-bold text-shadow text-xs sm:text-base truncate">
								{#if loading}
									<span
										class="inline-block w-16 sm:w-20 h-3.5 sm:h-4 bg-white/20 rounded animate-pulse"
									></span>
								{:else}
									{profile?.memberId || 'N/A'}
								{/if}
							</p>
						</div>
						<!-- OFC Status Badge -->
						{#if loading}
							<div
								class="h-4 sm:h-5 w-12 sm:w-16 bg-white/20 rounded-full animate-pulse mt-1"
							></div>
						{:else}
							<div
								class="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-full backdrop-blur-md mt-1 {profile?.ofcStatus ===
								'Active'
									? 'bg-green-500/20 border border-green-400/30'
									: 'bg-white/10 border border-white/20'} flex-shrink"
							>
								<span
									class="w-1 h-1 sm:w-1.5 sm:h-1.5 rounded-full flex-shrink-0 {profile?.ofcStatus ===
									'Active'
										? 'bg-green-400 animate-pulse shadow-[0_0_6px_rgba(74,222,128,0.6)]'
										: 'bg-gray-400'}"
								></span>
								<span
									class="text-[10px] sm:text-[11px] font-bold uppercase tracking-wider {profile?.ofcStatus ===
									'Active'
										? 'text-green-300'
										: 'text-gray-400'} truncate"
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
				<div class="flex items-center gap-3 sm:gap-4 my-1 sm:my-2 opacity-80 min-w-0">
					<div
						class="w-8 h-6 sm:w-10 sm:h-8 rounded-md bg-gradient-to-br from-yellow-200 to-yellow-600 border border-yellow-600 shadow-inner flex items-center justify-center flex-shrink-0"
					>
						<div class="w-4 h-3 sm:w-6 sm:h-4 border border-yellow-800/30 rounded-sm"></div>
					</div>
					<!-- WifiIcon -->
					<svg
						viewBox="0 0 24 24"
						fill="currentColor"
						class="w-5 h-5 sm:w-6 sm:h-6 rotate-90 text-gray-500 flex-shrink-0"
					>
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
				<div class="flex justify-between items-end gap-2 min-w-0">
					<div class="min-w-0">
						<p class="text-[10px] sm:text-[11px] text-gray-400 font-bold uppercase mb-0.5 truncate">
							{$t('profile.memberCard.cardHolder')}
						</p>
						<p
							class="text-base sm:text-lg font-bold tracking-wide uppercase text-shadow-sm truncate"
						>
							{#if loading}
								<span class="inline-block w-32 sm:w-40 h-4 sm:h-5 bg-white/20 rounded animate-pulse"
								></span>
							{:else}
								{profile?.name || 'N/A'}
							{/if}
						</p>
					</div>
					<div class="bg-white p-1 rounded-lg flex-shrink-0">
						<QrCode class="w-6 h-6 sm:w-8 sm:h-8 text-black" />
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
