<script lang="ts">
	import { fade } from 'svelte/transition';
	import { Play } from 'lucide-svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import PlatformLogo from './PlatformLogo.svelte';
	import LiveStats from './LiveStats.svelte';

	const { t } = useTranslation();

	export let stream: any;
	export let i: number = 0;
	export let variant: 'default' | 'theater' = 'default';

	const fallbackAvatar = 'https://placehold.co/640x960?text=NO%20IMAGE';
</script>

<a
	href={variant === 'theater' 
		? `/theater/live/${stream.platform}/${stream.room_id || stream.live_id}`
		: `/jkt48/live/${stream.platform}/${stream.room_id || stream.live_id}`}
	class="group relative aspect-[3/4] flex flex-col bg-white dark:bg-zinc-900 rounded-xl overflow-hidden shadow-xl shadow-slate-200/50 dark:shadow-none hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 cursor-pointer border border-slate-100 dark:border-zinc-800/50"
	in:fade={{ duration: 400, delay: i * 50 }}
>
	<!-- Member Photo Container -->
	<div class="relative w-full h-full overflow-hidden bg-gray-100 dark:bg-zinc-800">
		<img
			src={getExternalMediaUrl(stream.member?.img) || fallbackAvatar}
			alt={stream.member?.name}
			on:error={(e) => {
				if (e.currentTarget instanceof HTMLImageElement)
					e.currentTarget.src = fallbackAvatar;
			}}
			class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
		/>

		<!-- Frame Image Overlay -->
		<img
			src={stream.member?.member_type?.toLowerCase() === 'trainee'
				? 'https://jkt48.com/images/member/bg-member-trainee-frame-transparent.png'
				: 'https://jkt48.com/images/member/bg-member-item-frame-transparent.png'}
			alt="frame"
			class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
		/>

		<!-- Gradient Overlay -->
		<div
			class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
		></div>

		<!-- Platform & Viewers Badges -->
		<div
			class="absolute top-2 sm:top-3 left-2 sm:left-3 right-2 sm:right-3 flex items-center justify-between gap-1 z-30"
		>
			<LiveStats
				view_num={stream.view_num}
				variant="overlay"
				className="px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full bg-black/60 shadow-lg"
			/>

			<PlatformLogo
				platform={stream.platform}
				size="sm"
			/>
		</div>

		<!-- Content Area (Overlay) -->
		<div class="absolute bottom-0 left-0 right-0 p-4 flex flex-col justify-end z-30">
			<h3
				class="font-black text-white text-base leading-tight drop-shadow-md group-hover:text-red-500 transition-colors line-clamp-1 mb-0.5"
			>
				{stream.member?.name}
			</h3>
			<p class="text-[10px] text-gray-300 font-medium drop-shadow-sm line-clamp-1">
				{stream.title || $t('theater.live.multiview.live_status')}
			</p>
			<LiveStats
				start_at={stream.start_at}
				variant="compact"
				showLabel={true}
				className="mt-1.5"
			/>
		</div>

		<!-- Hover Play Button Indicator -->
		<div
			class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-500 bg-black/20 backdrop-blur-[2px] z-40"
		>
			<div
				class="w-16 h-16 rounded-full bg-red-600 text-white flex items-center justify-center shadow-2xl scale-50 group-hover:scale-100 transition-transform duration-500"
			>
				<Play fill="currentColor" size={28} class="ml-1" />
			</div>
		</div>
	</div>
</a>
