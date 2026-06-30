<script lang="ts">
	import { safeCrossfade } from '$lib/utils/transitions';
	import { cubicInOut } from 'svelte/easing';
	import type { Snippet } from 'svelte';

	const [send, receive] = safeCrossfade({
		duration: 300,
		easing: cubicInOut
	});

	interface NavItem {
		label: string;
		href: string;
		id?: string;
		activeHref?: string;
		exact?: boolean;
		match?: (currentPath: string) => boolean;
		activeClass?: string;
		disabled?: boolean;
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		[key: string]: any;
	}

	interface Props {
		items?: NavItem[];
		currentPath: string;
		className?: string;
		item?: Snippet<[{ item: NavItem; isActive: boolean }]>;
	}

	let { items = [], currentPath, className = '', item: itemSnippet }: Props = $props();
</script>

<ul
	class="items-center gap-0.5 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md border border-gray-100 dark:border-zinc-800 p-1 rounded-full shadow-sm overflow-x-auto md:overflow-visible flex whitespace-nowrap lg:gap-1 {className}"
>
	{#each items as entry (entry.href)}
		{@const isActive = entry.match
			? entry.match(currentPath)
			: entry.exact
				? currentPath === (entry.activeHref || entry.href)
				: (entry.activeHref || entry.href) === '/'
					? currentPath === '/'
					: currentPath.startsWith(entry.activeHref || entry.href)}
		<li>
			<a
				href={entry.disabled ? undefined : entry.href}
				class="relative px-2.5 lg:px-4 py-1.5 rounded-full text-[11px] font-black uppercase tracking-widest transition-all duration-200 flex items-center justify-center gap-1.5 {isActive
					? 'text-white'
					: 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white/80 dark:hover:bg-zinc-800'} {entry.disabled
					? 'pointer-events-none opacity-40 cursor-not-allowed'
					: ''}"
			>
				{#if isActive}
					<div
						class="absolute inset-0 {entry.activeClass ||
							'bg-red-600 shadow-red-500/20'} rounded-full shadow-lg z-0 transition-all duration-300"
						in:receive={{ key: 'nav-active-pill' }}
						out:send={{ key: 'nav-active-pill' }}
					></div>
				{/if}
				<span class="relative z-10 flex items-center gap-1.5">
					{#if itemSnippet}
						{@render itemSnippet({ item: entry, isActive })}
					{:else}
						{entry.label}
					{/if}
				</span>
			</a>
		</li>
	{/each}
</ul>
