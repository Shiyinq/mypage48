<script lang="ts">
	import { crossfade } from 'svelte/transition';
	import { cubicInOut } from 'svelte/easing';

	const [send, receive] = crossfade({
		duration: 300,
		easing: cubicInOut
	});

	export let items: Array<{
		label: string;
		href: string;
		id?: string;
		activeHref?: string;
		exact?: boolean;
		[key: string]: any;
	}> = [];
	export let currentPath: string;
	export let className = ''; // Standard hidden md:flex is default but can be overridden
</script>

<div
	class="items-center gap-0.5 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md border border-gray-100 dark:border-zinc-800 p-1 rounded-full shadow-sm overflow-x-auto md:overflow-visible flex whitespace-nowrap lg:gap-1 {className}"
>
	{#each items as item (item.href)}
		{@const isActive = item.exact
			? currentPath === (item.activeHref || item.href)
			: (item.activeHref || item.href) === '/'
				? currentPath === '/'
				: currentPath.startsWith(item.activeHref || item.href)}
		<a
			href={item.href}
			class="relative px-2.5 lg:px-4 py-1.5 rounded-full text-[11px] font-black uppercase tracking-widest transition-all duration-200 flex items-center justify-center gap-1.5 {isActive
				? 'text-white'
				: 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white/80 dark:hover:bg-zinc-800'}"
		>
			{#if isActive}
				<div
					class="absolute inset-0 {item.activeClass || 'bg-red-600 shadow-red-500/20'} rounded-full shadow-lg z-0 transition-all duration-300"
					in:receive={{ key: 'nav-active-pill' }}
					out:send={{ key: 'nav-active-pill' }}
				></div>
			{/if}
			<span class="relative z-10 flex items-center gap-1.5">
				<slot name="item" {item} {isActive}>
					{item.label}
				</slot>
			</span>
		</a>
	{/each}
</div>
