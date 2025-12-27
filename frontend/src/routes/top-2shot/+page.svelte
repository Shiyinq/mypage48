<script lang="ts">
	import { tickets } from '$lib/stores';
	import { Heart, Crown, Camera, TrendingUp, User } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	// --- DATA PROCESSING ---
	$: stats = (() => {
		const memberStats: Record<
			string,
			{ count: number; spend: number; lastDate: string; image?: string }
		> = {};
		let totalTwoShotSpend = 0;
		let totalTwoShotCount = 0;

		$tickets.forEach((t) => {
			// 2-Shot Stats
			if (t.two_shot?.member_name) {
				const name = t.two_shot.member_name.trim();
				const price = t.two_shot.price || 0;

				totalTwoShotSpend += price;
				totalTwoShotCount++;

				if (!memberStats[name]) {
					memberStats[name] = {
						count: 0,
						spend: 0,
						lastDate: t.event.date,
						image: t.two_shot.imageUrl
					};
				}

				memberStats[name].count += 1;
				memberStats[name].spend += price;

				// Update image to latest if available
				if (t.two_shot.imageUrl) {
					// Prefer latest image, or if current doesn't have one
					if (
						new Date(t.event.date) > new Date(memberStats[name].lastDate) ||
						!memberStats[name].image
					) {
						memberStats[name].image = t.two_shot.imageUrl;
						memberStats[name].lastDate = t.event.date;
					}
				}
			}
		});

		// Convert to array and sort
		const ranking = Object.entries(memberStats)
			.map(([name, data]) => ({ name, ...data }))
			.sort((a, b) => {
				if (b.count !== a.count) return b.count - a.count; // Sort by count
				return b.spend - a.spend; // Then by spend
			});

		return {
			ranking,
			totalTwoShotSpend,
			totalTwoShotCount
		};
	})();

	$: kamiOshi = stats.ranking[0];

	// Helper for currency formatting
	const formatCurrency = (val: number) =>
		new Intl.NumberFormat('id-ID', {
			style: 'currency',
			currency: 'IDR',
			maximumFractionDigits: 0
		}).format(val);

	const formatCompact = (val: number) =>
		new Intl.NumberFormat('id-ID', {
			style: 'currency',
			currency: 'IDR',
			notation: 'compact'
		}).format(val);
</script>

<svelte:head>
	<title>{$t('top2shot.title')} | MyPage48</title>
</svelte:head>

<div class="max-w-6xl mx-auto p-4 pb-24 animate-fade-in">
	<!-- Header -->
	<div class="flex items-center gap-3 mb-8">
		<div
			class="p-3 rounded-2xl bg-pink-50 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 shadow-lg shadow-pink-100 dark:shadow-pink-900/20 border-2 border-white dark:border-zinc-700 transform -rotate-6"
		>
			<Heart class="w-6 h-6 fill-current" />
		</div>
		<div>
			<h2 class="text-2xl font-bold text-themed leading-none relative w-fit">
				{$t('top2shot.title')}
				<span
					class="absolute -bottom-1 left-0 w-full h-2 bg-pink-200/60 dark:bg-pink-500/30 -z-10 transform -skew-x-12 rounded-sm"
				></span>
			</h2>
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{$t('top2shot.subtitle')}</p>
		</div>
	</div>

	{#if stats.ranking.length === 0}
		<div
			class="flex flex-col items-center justify-center min-h-[400px] p-8 text-center border-2 border-dashed border-gray-200 dark:border-zinc-700 rounded-3xl bg-gray-50/50 dark:bg-zinc-800/50"
		>
			<div
				class="w-20 h-20 bg-white dark:bg-zinc-700 rounded-full shadow-sm flex items-center justify-center mb-6"
			>
				<Camera class="w-10 h-10 text-gray-300 dark:text-gray-600" />
			</div>
			<h3 class="text-xl font-bold text-gray-800 dark:text-gray-200 mb-2">
				{$t('top2shot.noData')}
			</h3>
			<p class="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
				{$t('top2shot.noDataDesc')}
			</p>
		</div>
	{:else}
		<div class="grid lg:grid-cols-3 gap-6">
			<!-- LEFT COL: Kami Oshi Card & Spending -->
			<div class="space-y-6 lg:col-span-1">
				<!-- KAMI OSHI CARD -->
				<div class="relative group">
					<div
						class="relative overflow-hidden bg-white dark:bg-zinc-800 rounded-3xl shadow-sm border border-gray-100 dark:border-zinc-700 p-8 transition-all duration-300 hover:shadow-xl"
					>
						<!-- Decorative Header Background -->
						<div
							class="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-pink-50/80 to-transparent dark:from-pink-900/10 dark:to-transparent -z-0"
						></div>

						<div class="relative z-10 flex flex-col items-center text-center">
							<div
								class="bg-gradient-to-r from-amber-100 to-amber-200 dark:from-amber-900/40 dark:to-amber-800/40 text-amber-700 dark:text-amber-400 text-[10px] font-black tracking-widest px-4 py-1.5 rounded-full mb-6 shadow-sm flex items-center gap-1.5 border border-amber-200/50 dark:border-amber-700/30"
							>
								<Crown class="w-3.5 h-3.5 fill-current" />
								{$t('top2shot.kamiOshi')}
							</div>

							<div class="relative mb-6 group-hover:scale-105 transition-transform duration-500">
								<div
									class="w-36 h-36 rounded-full p-1.5 bg-white dark:bg-zinc-800 shadow-xl ring-1 ring-gray-100 dark:ring-zinc-700 relative z-10"
								>
									<div
										class="w-full h-full rounded-full overflow-hidden bg-gray-100 dark:bg-zinc-700 relative"
									>
										{#if kamiOshi.image}
											<img
												src={kamiOshi.image}
												alt={kamiOshi.name}
												class="w-full h-full object-cover"
											/>
										{:else}
											<div
												class="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-600"
											>
												<User class="w-16 h-16" />
											</div>
										{/if}
									</div>
								</div>
								<!-- Rank Badge -->
								<div
									class="absolute -bottom-2 -right-2 bg-yellow-400 text-yellow-900 w-10 h-10 flex items-center justify-center rounded-full font-black border-4 border-white dark:border-zinc-800 shadow-lg text-lg z-20"
								>
									#1
								</div>
							</div>

							<h3 class="text-2xl font-black text-gray-900 dark:text-white mb-1">
								{kamiOshi.name}
							</h3>
							<p
								class="text-pink-500 font-bold text-sm mb-8 bg-pink-50 dark:bg-pink-900/20 px-3 py-1 rounded-lg"
							>
								{$t('top2shot.cherished')}
							</p>

							<div class="grid grid-cols-2 gap-4 w-full">
								<div
									class="bg-gray-50 dark:bg-zinc-700/30 rounded-2xl p-4 border border-gray-100 dark:border-zinc-700/50"
								>
									<div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-bold mb-1">
										{$t('top2shot.stats2shots')}
									</div>
									<div class="text-2xl font-black text-gray-800 dark:text-gray-100">
										{kamiOshi.count}x
									</div>
								</div>
								<div
									class="bg-gray-50 dark:bg-zinc-700/30 rounded-2xl p-4 border border-gray-100 dark:border-zinc-700/50"
								>
									<div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-bold mb-1">
										{$t('top2shot.statsSpent')}
									</div>
									<div class="text-lg font-black text-gray-800 dark:text-gray-100 mt-1">
										{formatCompact(kamiOshi.spend)}
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- RIGHT COL: Leaderboard -->
			<div class="lg:col-span-2">
				<div
					class="bg-white dark:bg-zinc-800 rounded-3xl border border-gray-100 dark:border-zinc-700 shadow-sm overflow-hidden"
				>
					<div
						class="p-6 border-b border-gray-100 dark:border-zinc-700 flex justify-between items-center bg-gray-50/50 dark:bg-zinc-800/50"
					>
						<div>
							<h3 class="font-bold text-gray-800 dark:text-gray-200 text-lg">
								{$t('top2shot.rankingTitle')}
							</h3>
							<p class="text-xs text-gray-500 dark:text-gray-400">
								{$t('top2shot.rankingSubtitle')}
							</p>
						</div>
						<div
							class="bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1"
						>
							<TrendingUp class="w-3 h-3" />
							{stats.totalTwoShotCount}
							{$t('top2shot.totalPhotos')}
						</div>
					</div>

					<div class="divide-y divide-gray-50 dark:divide-zinc-700">
						{#each stats.ranking as member, index}
							<div
								class="p-4 flex items-center gap-4 hover:bg-gray-50 dark:hover:bg-zinc-700/50 transition-colors group"
							>
								<!-- Rank Number -->
								<div
									class={`w-8 h-8 flex-shrink-0 flex items-center justify-center font-black text-sm rounded-full ${
										index === 0
											? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
											: index === 1
												? 'bg-gray-200 dark:bg-zinc-700 text-gray-600 dark:text-gray-300'
												: index === 2
													? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
													: 'text-gray-400'
									}`}
								>
									{index + 1}
								</div>

								<!-- Avatar -->
								<div
									class="w-12 h-12 rounded-full bg-gray-100 dark:bg-zinc-700 flex-shrink-0 overflow-hidden border border-gray-100 dark:border-zinc-600"
								>
									{#if member.image}
										<img src={member.image} alt={member.name} class="w-full h-full object-cover" />
									{:else}
										<div
											class="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-500"
										>
											<User class="w-5 h-5" />
										</div>
									{/if}
								</div>

								<!-- Info -->
								<div class="flex-1 min-w-0">
									<h4 class="font-bold text-gray-800 dark:text-gray-200 truncate">{member.name}</h4>
									<div class="flex items-center gap-3 mt-0.5">
										<span
											class="text-xs text-gray-500 dark:text-gray-400 font-medium flex items-center gap-1"
										>
											<Camera class="w-3 h-3" />
											{member.count}
											{$t('top2shot.photos')}
										</span>
									</div>
								</div>

								<!-- Spend Bar Visual -->
								<div class="hidden sm:block w-24">
									<div class="text-[10px] text-gray-400 text-right font-bold mb-1">
										{formatCompact(member.spend)}
									</div>
									<div
										class="h-1.5 w-full bg-gray-100 dark:bg-zinc-700 rounded-full overflow-hidden"
									>
										<div
											class="h-full bg-pink-500 rounded-full"
											style="width: {(member.count / kamiOshi.count) * 100}%"
										></div>
									</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
