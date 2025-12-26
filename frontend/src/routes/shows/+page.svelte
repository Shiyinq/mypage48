<script lang="ts">
	import { tickets } from '$lib/stores';
	import {
		ChevronLeft,
		Mic2,
		Calendar,
		History,
		DollarSign,
		Trophy,
		Armchair,
		Ticket as TicketIcon,
		MapPin,
		Trash2
	} from 'lucide-svelte';

	// Constants
	const SHOW_DATA = [
		{
			title: 'Pertaruhan Cinta',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1760105446/wwiaxahqs3ti0lhqdszz.jpg'
		},
		{
			title: 'Pajama Drive',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1717174034/xspjxcs9wwm9jxwhiy5q.jpg'
		},
		{
			title: 'Aturan Anti Cinta',
			image:
				'https://cdn.idntimes.com/content-images/post/20251115/50a27780-93e7-4e40-8474-60f6e0cca6da-251115200115.jpg'
		},
		{
			title: 'Sambil Menggandeng Erat Tanganku',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1743898507/nvw4gqjtdhje2ftxt9i1.jpg'
		},
		{
			title: 'Cara Meminum Ramune',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1702404446/nixg3rixpjpom3xa0ivf.jpg'
		},
		{
			title: 'Ingin Bertemu',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1697224788/uploads/w2zvghwk8tocey8e8xhv.jpg'
		},
		{
			title: 'KIRA KIRA GIRLS',
			image:
				'https://res.cloudinary.com/doig4w6cm/image/fetch/f_webp,q_80,ar_0.75,w_640,c_fill/https://res.cloudinary.com/haymzm4wp/image/upload/v1763233779/tanfbrrf8oexxmmfoouh.jpg'
		}
	];

	// State
	let selectedShowTitle: string | null = null;

	// Derived
	$: showCounts = $tickets.reduce(
		(acc, t) => {
			const title = t.event.title.trim();
			const matchedShow = SHOW_DATA.find((s) =>
				title.toLowerCase().includes(s.title.toLowerCase())
			);

			if (matchedShow) {
				acc[matchedShow.title] = (acc[matchedShow.title] || 0) + 1;
			} else {
				acc[title] = (acc[title] || 0) + 1;
			}
			return acc;
		},
		{} as Record<string, number>
	);

	$: maxAttendance = Math.max(...Object.values(showCounts), 1);

	// Detail View Data
	$: selectedShowData = selectedShowTitle
		? {
				info: SHOW_DATA.find((s) => s.title === selectedShowTitle),
				tickets: $tickets.filter((t) =>
					t.event.title.toLowerCase().includes((selectedShowTitle || '').toLowerCase())
				)
			}
		: null;

	$: if (selectedShowData) {
		selectedShowData.tickets.sort(
			(a, b) => new Date(a.event.date).getTime() - new Date(b.event.date).getTime()
		);
	}

	$: stats = selectedShowData
		? (() => {
				const t = selectedShowData.tickets;
				const first = t[0];
				const last = t[t.length - 1];
				const totalSpent = t.reduce((acc, curr) => acc + curr.price, 0);
				const avgPrice = t.length > 0 ? totalSpent / t.length : 0;

				const rowCounts = t.reduce(
					(acc, curr) => {
						const r = curr.seat.section.toUpperCase().charAt(0);
						acc[r] = (acc[r] || 0) + 1;
						return acc;
					},
					{} as Record<string, number>
				);
				const topRow = Object.entries(rowCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '-';

				return { first, last, avgPrice, topRow, totalSpent };
			})()
		: null;

	const selectShow = (title: string) => {
		selectedShowTitle = title;
		window.scrollTo({ top: 0, behavior: 'smooth' });
	};

	const deleteTicket = (id: string) => {
		if (confirm('Delete this ticket?')) {
			tickets.update((current) => current.filter((t) => t._id !== id));
		}
	};
</script>

<div class="max-w-6xl mx-auto p-4 pb-24 animate-fade-in">
	{#if selectedShowTitle && selectedShowData}
		<button
			on:click={() => (selectedShowTitle = null)}
			class="flex items-center text-gray-600 mb-6 hover:text-red-600 transition-colors font-medium cursor-pointer"
		>
			<ChevronLeft class="w-5 h-5 mr-1" />
			Back to Setlists
		</button>

		<!-- Header -->
		<div class="relative rounded-3xl overflow-hidden mb-8 shadow-lg group bg-gray-900 h-64 md:h-80">
			{#if selectedShowData.info}
				<img
					src={selectedShowData.info.image}
					alt={selectedShowTitle}
					class="absolute inset-0 w-full h-full object-cover transition-opacity duration-700"
				/>
				<div class="absolute inset-0 bg-gradient-to-r from-black/90 via-black/60 to-transparent" />
			{/if}
			<div
				class="relative z-10 p-8 md:p-12 flex flex-col md:flex-row items-start md:items-center gap-6 h-full justify-center md:justify-start"
			>
				<div
					class="p-4 rounded-2xl bg-red-600/20 backdrop-blur-md text-white border border-white/10 shadow-inner"
				>
					<Mic2 class="w-8 h-8" />
				</div>
				<div>
					<h2 class="text-3xl md:text-4xl font-black text-white leading-none mb-2 drop-shadow-lg">
						{selectedShowTitle}
					</h2>
					<p class="text-gray-200 font-medium text-lg">
						{selectedShowData.tickets.length} performances attended
					</p>
				</div>
			</div>
		</div>

		<!-- Stats Grid -->
		{#if stats && selectedShowData.tickets.length > 0}
			<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
				<!-- First Seen -->
				<div
					class="glass-panel p-4 rounded-2xl flex items-center gap-4 border-l-4 border-l-blue-400"
				>
					<div class="p-2 bg-blue-50 text-blue-500 rounded-lg">
						<Calendar class="w-5 h-5" />
					</div>
					<div>
						<p class="text-[10px] text-gray-400 font-bold uppercase tracking-wider">
							First Attended
						</p>
						<p class="font-bold text-gray-800 text-sm">
							{new Date(stats.first.event.date).toLocaleDateString('id-ID', {
								day: 'numeric',
								month: 'short',
								year: '2-digit'
							})}
						</p>
					</div>
				</div>

				<!-- Last Seen -->
				<div
					class="glass-panel p-4 rounded-2xl flex items-center gap-4 border-l-4 border-l-purple-400"
				>
					<div class="p-2 bg-purple-50 text-purple-500 rounded-lg">
						<History class="w-5 h-5" />
					</div>
					<div>
						<p class="text-[10px] text-gray-400 font-bold uppercase tracking-wider">
							Last Attended
						</p>
						<p class="font-bold text-gray-800 text-sm">
							{new Date(stats.last.event.date).toLocaleDateString('id-ID', {
								day: 'numeric',
								month: 'short',
								year: '2-digit'
							})}
						</p>
					</div>
				</div>

				<!-- Avg Price -->
				<div
					class="glass-panel p-4 rounded-2xl flex items-center gap-4 border-l-4 border-l-emerald-400"
				>
					<div class="p-2 bg-emerald-50 text-emerald-500 rounded-lg">
						<DollarSign class="w-5 h-5" />
					</div>
					<div>
						<p class="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Avg. Price</p>
						<p class="font-bold text-gray-800 text-sm">
							{new Intl.NumberFormat('id-ID', {
								style: 'currency',
								currency: 'IDR',
								maximumFractionDigits: 0,
								notation: 'compact'
							}).format(stats.avgPrice)}
						</p>
					</div>
				</div>

				<!-- Top Row -->
				<div
					class="glass-panel p-4 rounded-2xl flex items-center gap-4 border-l-4 border-l-orange-400"
				>
					<div class="p-2 bg-orange-50 text-orange-500 rounded-lg">
						<Armchair class="w-5 h-5" />
					</div>
					<div>
						<p class="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Top Row</p>
						<p class="font-bold text-gray-800 text-sm">Row {stats.topRow}</p>
					</div>
				</div>
			</div>
		{/if}

		<!-- Ticket List -->
		<div class="space-y-4">
			{#each selectedShowData.tickets as ticket (ticket._id)}
				<div class="glass-panel p-4 rounded-2xl flex gap-4 transition-all hover:bg-white/80">
					<div class="w-20 h-20 rounded-xl bg-gray-100 flex-shrink-0 overflow-hidden">
						{#if ticket.imageUrl}
							<img src={ticket.imageUrl} alt="" class="w-full h-full object-cover" />
						{:else}
							<div class="w-full h-full flex items-center justify-center text-gray-300">
								<TicketIcon class="w-8 h-8" />
							</div>
						{/if}
					</div>
					<div class="flex-1 min-w-0">
						<h3 class="font-bold text-gray-800 truncate">{ticket.event.title}</h3>
						<div class="text-xs text-gray-500 flex items-center gap-2 mt-1">
							<Calendar class="w-3 h-3" />
							{ticket.event.date}
						</div>
						<div class="text-xs text-gray-500 flex items-center gap-2 mt-0.5">
							<MapPin class="w-3 h-3" /> Row {ticket.seat.section}-{ticket.seat.number}
						</div>
						<div class="mt-2 font-bold text-red-600 text-sm">
							IDR {ticket.price.toLocaleString()}
						</div>
					</div>
					<div class="flex flex-col justify-center">
						<button
							on:click={() => deleteTicket(ticket._id)}
							class="p-2 text-gray-300 hover:text-red-600 transition-colors cursor-pointer"
							><Trash2 class="w-5 h-5" /></button
						>
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<!-- Main List -->
		<div class="flex items-center gap-3 mb-8">
			<div
				class="p-3 rounded-2xl bg-purple-50 text-purple-600 shadow-lg shadow-purple-100 border-2 border-white transform -rotate-6"
			>
				<Mic2 class="w-6 h-6" />
			</div>
			<div>
				<h2 class="text-2xl font-bold text-gray-800 w-fit relative">
					Theater Setlists
					<span
						class="absolute -bottom-1 left-0 w-full h-2 bg-purple-200/60 -z-10 transform -skew-x-12 rounded-sm"
					></span>
				</h2>
				<p class="text-sm text-gray-500">Select a show to view your attendance history</p>
			</div>
		</div>

		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
			{#each SHOW_DATA as show (show.title)}
				{@const count = showCounts[show.title] || 0}
				{@const percentage = (count / maxAttendance) * 100}
				{@const isMostWatched = count === maxAttendance && count > 0}

				<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
				<div
					on:click={() => selectShow(show.title)}
					class="relative overflow-hidden rounded-3xl h-64 cursor-pointer group shadow-md hover:shadow-xl transition-all duration-500 bg-gray-900"
				>
					<!-- Background Image -->
					<img
						src={show.image}
						alt={show.title}
						class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110 opacity-80"
						loading="lazy"
					/>

					<!-- Gradient Overlay -->
					<div
						class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent transition-opacity duration-300 group-hover:via-black/60"
					></div>

					<!-- Content -->
					<div class="relative z-10 flex flex-col h-full justify-between p-6">
						<div>
							<div class="flex justify-between items-start gap-2 mb-1">
								<h3 class="text-xl font-black text-white leading-tight drop-shadow-md line-clamp-2">
									{show.title}
								</h3>
								{#if isMostWatched}
									<span
										class="bg-yellow-500/90 backdrop-blur-sm text-white text-[10px] font-bold px-2 py-1 rounded-full shadow-sm flex items-center gap-1 flex-shrink-0 border border-white/20"
									>
										<Trophy class="w-3 h-3" /> Top
									</span>
								{/if}
							</div>
						</div>

						<div class="space-y-3">
							<!-- Stats Row -->
							<div class="flex justify-between items-end">
								<div
									class={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold transition-colors backdrop-blur-md border ${count > 0 ? 'bg-red-600 text-white border-red-500 shadow-lg shadow-red-900/20' : 'bg-white/20 text-gray-200 border-white/10'}`}
								>
									{count} Show{count !== 1 ? 's' : ''}
								</div>

								{#if count > 0}
									<span
										class="text-xs text-white/90 font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0"
									>
										View History <ChevronLeft class="w-3 h-3 rotate-180" />
									</span>
								{/if}
							</div>

							<!-- Progress Bar Visual -->
							<div>
								<div class="flex justify-end mb-1">
									<span class="text-[10px] text-gray-300 font-medium">
										{count > 0 ? `${percentage.toFixed(0)}% to top` : 'Not seen yet'}
									</span>
								</div>
								<div class="w-full bg-white/20 rounded-full h-1.5 overflow-hidden backdrop-blur-sm">
									<div
										class={`h-full rounded-full transition-all duration-1000 ease-out ${count > 0 ? 'bg-red-500 shadow-[0_0_10px_rgba(220,38,38,0.8)]' : 'bg-transparent'}`}
										style={`width: ${count > 0 ? percentage : 0}%`}
									></div>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
