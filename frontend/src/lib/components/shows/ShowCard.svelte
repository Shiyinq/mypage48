<script lang="ts">
	import { Trophy, ChevronLeft } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface ShowInfo {
		title: string;
		image: string;
	}

	export let show: ShowInfo;
	export let count: number = 0;
	export let maxAttendance: number = 1;
	export let onClick: () => void;

	const { t } = useTranslation();

	$: percentage = (count / maxAttendance) * 100;
	$: isMostWatched = count === maxAttendance && count > 0;
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div
	on:click={onClick}
	class="relative overflow-hidden rounded-3xl aspect-[2/3] cursor-pointer group shadow-md hover:shadow-xl transition-all duration-500 bg-gray-900"
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
				<h3 class="text-xl font-black text-white leading-tight drop-shadow-md line-clamp-4">
					{show.title}
				</h3>
				{#if isMostWatched}
					<span
						class="bg-yellow-500/90 backdrop-blur-sm text-white text-[10px] font-bold px-2 py-1 rounded-full shadow-sm flex items-center gap-1 flex-shrink-0 border border-white/20"
					>
						<Trophy class="w-3 h-3" />
						{$t('shows.top')}
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
					{count > 0
						? $t('theater.setlists.attendedCount', { count })
						: $t('theater.setlists.notAttended')}
				</div>

				{#if count > 0}
					<span
						class="text-xs text-white/90 font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0"
					>
						{$t('shows.viewHistory')}
						<ChevronLeft class="w-3 h-3 rotate-180" />
					</span>
				{/if}
			</div>

			<!-- Progress Bar Visual -->
			<div>
				<div class="flex justify-end mb-1">
					<span class="text-[10px] text-gray-300 font-medium">
						{count > 0 ? `${percentage.toFixed(0)}% ${$t('shows.toTop')}` : $t('shows.notSeen')}
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
