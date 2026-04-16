<script lang="ts">
	import type { Member } from '$lib/apis/members';
	import { getExternalMediaUrl } from '$lib/utils/media';

	import { getMemberFrame } from '$lib/constants';
	import { OptimizedImage } from '$lib/components/common';

	interface Props {
		member: Member;
		onclick?: () => void;
	}

	let { member, onclick }: Props = $props();

	let frameImg = $derived(getMemberFrame(member.member_type));
</script>

<button
	class="group relative aspect-[3/4] flex flex-col bg-white dark:bg-zinc-900 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer text-left"
	{onclick}
>
	<!-- Member Photo Container -->
	<div class="relative w-full h-full overflow-hidden bg-gray-100 dark:bg-zinc-800">
		{#if member.img}
			<OptimizedImage
				src={getExternalMediaUrl(member.img)}
				alt={member.name}
				class="w-full h-full transition-transform duration-500 group-hover:scale-110"
			/>
		{:else}
			<div
				class="w-full h-full bg-gradient-to-br from-pink-100 to-purple-100 dark:from-pink-900/30 dark:to-purple-900/30 flex items-center justify-center"
			>
				<span class="text-4xl font-bold text-pink-400">
					{member.nickname.charAt(0)}
				</span>
			</div>
		{/if}

		<!-- Frame Image Overlay -->
		<img
			src={frameImg}
			alt="member frame"
			class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
		/>

		<!-- Gradient Overlay -->
		<div
			class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
		></div>

		<!-- Content Area (Overlay) -->
		<div class="absolute bottom-0 left-0 right-0 p-3 flex flex-col justify-end z-30">
			<h3 class="font-bold text-white text-base leading-tight drop-shadow-sm">
				{member.nickname}
			</h3>
			<p class="text-[10px] text-gray-300 font-medium line-clamp-1 mt-0.5">
				{member.name}
			</p>
		</div>
	</div>
</button>
