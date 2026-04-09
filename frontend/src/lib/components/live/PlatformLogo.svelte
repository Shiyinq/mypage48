<script lang="ts">
	import { getLiveLogoUrl, getPlatformColor, getPlatformIcon } from '$lib/constants/live';

	export let platform: string;
	export let size: 'xs' | 'sm' | 'md' | 'lg' = 'sm';
	export let className: string = '';

	let logoError = false;

	const sizeMap = {
		xs: { container: 'h-4 min-w-[20px] px-1', img: 'h-1.5', text: 'text-[6px]' },
		sm: {
			container: 'h-5 sm:h-6 px-2 min-w-[28px]',
			img: 'h-1.5 sm:h-2',
			text: 'text-[7px] sm:text-[8px]'
		},
		md: { container: 'h-7 px-3 min-w-[36px]', img: 'h-2.5', text: 'text-[9px]' },
		lg: { container: 'h-10 px-4 min-w-[48px]', img: 'h-4', text: 'text-[11px]' }
	};

	$: activeSize = sizeMap[size];
	$: logoUrl = getLiveLogoUrl(platform);
	$: isShowroom = platform === 'showroom';

	$: bgColorClass =
		isShowroom && !logoError ? 'bg-[#121212]' : `bg-gradient-to-br ${getPlatformColor(platform)}`;
</script>

<div
	class="shrink-0 rounded-full flex items-center justify-center text-white border border-white/10 transition-all {bgColorClass} {activeSize.container} {className}"
>
	{#if !logoError}
		<img
			src={logoUrl}
			alt={platform}
			class="w-auto object-contain {activeSize.img} {!isShowroom ? 'brightness-0 invert' : ''}"
			on:error={() => (logoError = true)}
		/>
	{:else}
		<span class="font-bold uppercase tracking-widest {activeSize.text}">
			{getPlatformIcon(platform)}
		</span>
	{/if}
</div>
