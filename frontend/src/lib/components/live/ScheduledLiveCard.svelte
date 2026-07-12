<script lang="ts">
	import { Calendar, ExternalLink } from 'lucide-svelte';
	import type { LiveStatus } from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatLiveDate } from '$lib/utils/time';

	const { t, locale } = useTranslation();

	interface Props {
		live: LiveStatus;
	}

	let { live }: Props = $props();

	function formatDateTime(isoString: string) {
		return formatLiveDate(isoString, locale.value);
	}
</script>

<a
	href="https://www.idn.app/jkt48-official/live/preview/{live.live_id}"
	target="_blank"
	rel="noopener noreferrer"
	class="relative overflow-hidden rounded-xl bg-white dark:bg-slate-900 shadow-sm border border-slate-200 dark:border-slate-800 transition-transform hover:-translate-y-1 group block"
>
	<!-- Background Image -->
	<div class="aspect-video w-full overflow-hidden relative">
		<img
			src={live.image || '/media/news/migrated/jkt48logo.jpg'}
			alt={live.title}
			class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
			loading="lazy"
			decoding="async"
		/>

		<!-- Gradient overlay to ensure text is readable -->
		<div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent"></div>

		<!-- Top badges -->
		<div class="absolute top-3 right-3 flex gap-2">
			<span
				class="bg-black/60 backdrop-blur-sm text-white text-[10px] font-bold px-2 py-1 rounded border border-white/10 uppercase tracking-wider"
			>
				{t('theater.live.scheduled', { default: 'Terjadwal' })}
			</span>
		</div>

		<!-- Content -->
		<div class="absolute bottom-0 left-0 right-0 p-4">
			<div class="flex items-center gap-2 mb-1">
				<img
					src={live.member.img || '/media/news/migrated/jkt48logo.jpg'}
					alt={live.member.name}
					class="w-5 h-5 rounded-full object-cover border border-white/20"
				/>
				<span class="text-white/80 text-xs font-medium uppercase tracking-wider"
					>{live.member.name}</span
				>
			</div>

			<h3
				class="text-white font-bold text-sm sm:text-base line-clamp-1 mb-2 group-hover:text-red-400 transition-colors"
			>
				{live.title}
			</h3>

			<div class="flex items-end justify-between">
				<div class="flex items-center gap-1.5 text-white/70 text-xs font-medium">
					<Calendar size={14} class="opacity-70" />
					<span>
						{#if live.scheduled_at}
							{formatDateTime(live.scheduled_at)}
						{:else if live.start_at}
							{formatDateTime(live.start_at)}
						{:else}
							TBA
						{/if}
					</span>
				</div>
				<div
					class="flex items-center gap-1.5 bg-red-600/90 hover:bg-red-500 transition-colors text-white px-2.5 py-1.5 rounded-md text-xs font-bold shadow-lg border border-red-500/50 backdrop-blur-sm"
				>
					<span>{t('theater.live.buyAtIdn', { default: 'Beli di IDN' })}</span>
					<ExternalLink size={14} class="opacity-90" />
				</div>
			</div>
		</div>
	</div>
</a>
