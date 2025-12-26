<script lang="ts">
	import { tickets } from '$lib/stores';
	import { Heart, Crown, Camera, DollarSign, TrendingUp, User } from 'lucide-svelte';

	// --- DATA PROCESSING ---
	$: stats = (() => {
		const memberStats: Record<
			string,
			{ count: number; spend: number; lastDate: string; image?: string }
		> = {};
		let totalTwoShotSpend = 0;
		let totalTicketSpend = 0;
		let totalTwoShotCount = 0;

		$tickets.forEach((t) => {
			// Ticket Spending
			totalTicketSpend += t.price;

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
			totalTicketSpend,
			totalTwoShotCount
		};
	})();

	$: spendingData = [
		{ name: 'Theater Tickets', value: stats.totalTicketSpend, color: '#ef4444' }, // Red
		{ name: '2-Shot Collection', value: stats.totalTwoShotSpend, color: '#ec4899' } // Pink
	];

	$: totalSpending = stats.totalTicketSpend + stats.totalTwoShotSpend;
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

	// Donut Chart Helpers
	const size = 160;
	const strokeWidth = 20;
	const radius = (size - strokeWidth) / 2;
	const circumference = 2 * Math.PI * radius;

	$: chartSegments = (() => {
		let accumulatedAngle = 0; // in degrees? No, simpler to use dashoffset
		let accumulatedPercent = 0;
		return spendingData.map((d) => {
			const percent = totalSpending > 0 ? d.value / totalSpending : 0;
			const dashArray = percent * circumference;
			const dashOffset = -accumulatedPercent * circumference;
			accumulatedPercent += percent;
			return { ...d, percent, dashArray, dashOffset };
		});
	})();
</script>

<div class="max-w-6xl mx-auto p-4 pb-24 animate-fade-in">
	<!-- Header -->
	<div class="flex items-center gap-3 mb-8">
		<div
			class="p-3 rounded-2xl bg-pink-50 text-pink-600 shadow-lg shadow-pink-100 border-2 border-white transform -rotate-6"
		>
			<Heart class="w-6 h-6 fill-current" />
		</div>
		<div>
			<h2 class="text-2xl font-bold text-gray-800 leading-none relative w-fit">
				Top 2Shot
				<span
					class="absolute -bottom-1 left-0 w-full h-2 bg-pink-200/60 -z-10 transform -skew-x-12 rounded-sm"
				></span>
			</h2>
			<p class="text-sm text-gray-500 mt-1">Member analytics & spending breakdown</p>
		</div>
	</div>

	{#if stats.ranking.length === 0}
		<div
			class="flex flex-col items-center justify-center min-h-[400px] p-8 text-center border-2 border-dashed border-gray-200 rounded-3xl bg-gray-50/50"
		>
			<div class="w-20 h-20 bg-white rounded-full shadow-sm flex items-center justify-center mb-6">
				<Camera class="w-10 h-10 text-gray-300" />
			</div>
			<h3 class="text-xl font-bold text-gray-800 mb-2">No 2-Shot Data Yet</h3>
			<p class="text-sm text-gray-500 max-w-md mx-auto">
				Start adding 2-shot details when you create or edit a ticket to see your Oshi ranking!
			</p>
		</div>
	{:else}
		<div class="grid lg:grid-cols-3 gap-6">
			<!-- LEFT COL: Kami Oshi Card & Spending -->
			<div class="space-y-6 lg:col-span-1">
				<!-- KAMI OSHI CARD -->
				<div class="relative group perspective-1000">
					<div
						class="relative overflow-hidden bg-gradient-to-br from-red-500 via-pink-500 to-purple-600 rounded-3xl shadow-xl text-white p-6 transition-transform duration-500 hover:scale-[1.02]"
					>
						<!-- Background Pattern -->
						<div
							class="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-white via-transparent to-transparent"
						></div>
						<div
							class="absolute -right-10 -top-10 w-40 h-40 bg-white opacity-10 rounded-full blur-3xl"
						></div>

						<div class="relative z-10 flex flex-col items-center text-center">
							<div
								class="bg-yellow-400 text-yellow-900 text-[10px] font-black tracking-widest px-3 py-1 rounded-full mb-4 shadow-sm flex items-center gap-1 border border-yellow-200"
							>
								<Crown class="w-3 h-3 fill-current" /> KAMI-OSHI
							</div>

							<div
								class="w-32 h-32 rounded-full p-1.5 bg-white/20 backdrop-blur-sm border border-white/40 mb-4 relative"
							>
								<div class="w-full h-full rounded-full overflow-hidden bg-gray-800 relative">
									{#if kamiOshi.image}
										<img
											src={kamiOshi.image}
											alt={kamiOshi.name}
											class="w-full h-full object-cover"
										/>
									{:else}
										<div class="w-full h-full flex items-center justify-center bg-white/10">
											<User class="w-12 h-12 text-white/50" />
										</div>
									{/if}
								</div>
								<!-- Rank Badge -->
								<div
									class="absolute -bottom-2 -right-0 bg-yellow-400 text-yellow-900 w-8 h-8 flex items-center justify-center rounded-full font-black border-2 border-white shadow-lg text-sm"
								>
									#1
								</div>
							</div>

							<h3 class="text-2xl font-black mb-1">{kamiOshi.name}</h3>
							<p class="text-white/80 text-sm font-medium mb-6">Your most cherished member</p>

							<div
								class="grid grid-cols-2 gap-3 w-full bg-black/20 rounded-2xl p-3 backdrop-blur-md border border-white/10"
							>
								<div>
									<div class="text-xs text-white/60 uppercase font-bold mb-0.5">2-Shots</div>
									<div class="text-xl font-black">{kamiOshi.count}x</div>
								</div>
								<div>
									<div class="text-xs text-white/60 uppercase font-bold mb-0.5">Spent</div>
									<div class="text-sm font-black mt-1">
										{formatCompact(kamiOshi.spend)}
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- SPENDING BREAKDOWN -->
				<div class="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm">
					<h4 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
						<DollarSign class="w-4 h-4 text-green-500" /> Budget Split
					</h4>
					<div class="h-48 relative flex items-center justify-center">
						<!-- SVG Donut Chart -->
						<svg
							width={size}
							height={size}
							viewBox={`0 0 ${size} ${size}`}
							class="transform -rotate-90"
						>
							{#each chartSegments as segment}
								<circle
									cx={size / 2}
									cy={size / 2}
									r={radius}
									fill="none"
									stroke={segment.color}
									stroke-width={strokeWidth}
									stroke-dasharray={`${segment.dashArray} ${circumference}`}
									stroke-dashoffset={segment.dashOffset}
									class="transition-all duration-500"
								/>
							{/each}
						</svg>

						<!-- Total Center -->
						<div class="absolute inset-0 flex items-center justify-center pointer-events-none">
							<div class="text-center">
								<p class="text-[10px] text-gray-400 font-bold uppercase">Total</p>
								<p class="text-xs font-black text-gray-800">
									{formatCompact(totalSpending)}
								</p>
							</div>
						</div>
					</div>
					<div class="space-y-2 mt-4">
						{#each spendingData as d}
							<div class="flex items-center justify-between text-xs">
								<div class="flex items-center gap-2">
									<div class="w-2.5 h-2.5 rounded-full" style="background-color: {d.color}"></div>
									<span class="text-gray-600 font-medium">{d.name}</span>
								</div>
								<span class="font-bold text-gray-800">
									{formatCompact(d.value)}
								</span>
							</div>
						{/each}
					</div>
				</div>
			</div>

			<!-- RIGHT COL: Leaderboard -->
			<div class="lg:col-span-2">
				<div class="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
					<div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
						<div>
							<h3 class="font-bold text-gray-800 text-lg">Member Ranking</h3>
							<p class="text-xs text-gray-500">Based on your 2-shot history</p>
						</div>
						<div
							class="bg-pink-100 text-pink-600 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1"
						>
							<TrendingUp class="w-3 h-3" />
							{stats.totalTwoShotCount} Total Photos
						</div>
					</div>

					<div class="divide-y divide-gray-50">
						{#each stats.ranking as member, index}
							<div class="p-4 flex items-center gap-4 hover:bg-gray-50 transition-colors group">
								<!-- Rank Number -->
								<div
									class={`w-8 h-8 flex-shrink-0 flex items-center justify-center font-black text-sm rounded-full ${
										index === 0
											? 'bg-yellow-100 text-yellow-700'
											: index === 1
												? 'bg-gray-200 text-gray-600'
												: index === 2
													? 'bg-orange-100 text-orange-700'
													: 'text-gray-400'
									}`}
								>
									{index + 1}
								</div>

								<!-- Avatar -->
								<div
									class="w-12 h-12 rounded-full bg-gray-100 flex-shrink-0 overflow-hidden border border-gray-100"
								>
									{#if member.image}
										<img src={member.image} alt={member.name} class="w-full h-full object-cover" />
									{:else}
										<div class="w-full h-full flex items-center justify-center text-gray-300">
											<User class="w-5 h-5" />
										</div>
									{/if}
								</div>

								<!-- Info -->
								<div class="flex-1 min-w-0">
									<h4 class="font-bold text-gray-800 truncate">{member.name}</h4>
									<div class="flex items-center gap-3 mt-0.5">
										<span class="text-xs text-gray-500 font-medium flex items-center gap-1">
											<Camera class="w-3 h-3" />
											{member.count} Photos
										</span>
									</div>
								</div>

								<!-- Spend Bar Visual -->
								<div class="hidden sm:block w-24">
									<div class="text-[10px] text-gray-400 text-right font-bold mb-1">
										{formatCompact(member.spend)}
									</div>
									<div class="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
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
