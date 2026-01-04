<script lang="ts">
	import type { Member } from '$lib/apis/members';

	export let member: Member;
</script>

<button
	class="group relative flex flex-col bg-white dark:bg-zinc-900 rounded-xl overflow-hidden border-2 border-pink-100 dark:border-pink-900/30 shadow-sm hover:shadow-lg hover:shadow-pink-500/10 hover:border-pink-300 dark:hover:border-pink-500/50 transition-all duration-300 cursor-pointer text-left"
	on:click
>
	<!-- Member Photo Container -->
	<div class="relative w-full aspect-[2/3] overflow-hidden bg-gray-100 dark:bg-zinc-800">
		{#if member.img}
			<img
				src={member.img}
				alt={member.name}
				class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
				loading="lazy"
			/>
			<!-- subtle gradient overlay at bottom for depth -->
			<div
				class="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"
			></div>
		{:else}
			<div
				class="w-full h-full bg-gradient-to-br from-pink-100 to-purple-100 dark:from-pink-900/30 dark:to-purple-900/30 flex items-center justify-center"
			>
				<span class="text-2xl font-bold text-pink-400">
					{member.nickname.charAt(0)}
				</span>
			</div>
		{/if}
	</div>

	<!-- Content Area -->
	<div
		class="flex-1 p-2.5 flex flex-col items-center justify-center bg-pink-50/50 dark:bg-zinc-900 group-hover:bg-gradient-to-b group-hover:from-white group-hover:to-pink-50/50 dark:group-hover:from-zinc-900 dark:group-hover:to-pink-900/10 transition-colors relative z-10"
	>
		<h3
			class="font-bold text-gray-900 dark:text-gray-100 text-sm tracking-tight group-hover:text-pink-600 dark:group-hover:text-pink-400 transition-colors"
		>
			{member.nickname}
		</h3>
		<p
			class="text-[10px] text-gray-400 dark:text-gray-500 font-medium text-center line-clamp-1 mt-0.5 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors"
		>
			{member.name}
		</p>
	</div>
</button>
