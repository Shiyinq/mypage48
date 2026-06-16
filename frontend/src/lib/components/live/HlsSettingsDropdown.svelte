<script lang="ts">
	import { Settings } from 'lucide-svelte';
	import { hlsSettings, HLS_MODES, type HlsLatencyMode } from '$lib/stores/hlsSettings.svelte';
	import { fade, fly } from 'svelte/transition';
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		variant?: 'multiview' | 'liveroom';
		showControls?: boolean;
		isOpen?: boolean;
	}

	let { variant = 'multiview', showControls = true, isOpen = $bindable(false) }: Props = $props();

	const { t } = useTranslation();
	let dropdownRef: HTMLDivElement | undefined = $state();
	let buttonRef: HTMLButtonElement | undefined = $state();
	let fixedStyle = $state('');

	// Auto-close dropdown when controls are hidden (single live auto-hide)
	$effect(() => {
		if (!showControls && isOpen) {
			isOpen = false;
		}
	});

	function toggle(event: Event) {
		event.stopPropagation();
		if (!isOpen && buttonRef && variant === 'liveroom') {
			const rect = buttonRef.getBoundingClientRect();
			fixedStyle = `position: fixed; bottom: ${window.innerHeight - rect.top + 12}px; left: ${rect.left + rect.width / 2}px; transform: translateX(-50%); z-index: 999999;`;
		}
		isOpen = !isOpen;
	}

	function portal(node: HTMLElement) {
		if (variant === 'liveroom') {
			document.body.appendChild(node);
			return {
				destroy() {
					if (node.parentNode) {
						node.parentNode.removeChild(node);
					}
				}
			};
		}
	}

	function setMode(mode: string) {
		hlsSettings.setMode(mode as HlsLatencyMode);
		isOpen = false;
	}

	function handleClickOutside(event: MouseEvent) {
		if (isOpen && dropdownRef && !dropdownRef.contains(event.target as Node)) {
			isOpen = false;
		}
	}

	function getModeLabel(key: string): string {
		if (key === 'realtime') return t('theater.live.video_stability.realtime');
		if (key === 'balanced') return t('theater.live.video_stability.balanced');
		if (key === 'stable') return t('theater.live.video_stability.stable');
		return HLS_MODES[key as HlsLatencyMode]?.label ?? key;
	}

	onMount(() => {
		document.addEventListener('click', handleClickOutside);
		return () => {
			document.removeEventListener('click', handleClickOutside);
		};
	});
</script>

<div class="relative inline-block text-left" bind:this={dropdownRef}>
	<button
		bind:this={buttonRef}
		onclick={toggle}
		class={variant === 'multiview'
			? 'p-2 rounded-lg text-slate-500 hover:bg-gray-100 dark:text-zinc-400 dark:hover:text-white dark:hover:bg-zinc-800 transition-all cursor-pointer flex items-center gap-2'
			: 'relative w-10 h-10 flex items-center justify-center hover:bg-white/10 text-white rounded-full transition-all flex-shrink-0 cursor-pointer'}
		title={t('theater.live.video_stability.title')}
	>
		<Settings class={variant === 'multiview' ? 'w-5 h-5' : 'w-[18px] h-[18px]'} />
	</button>

	{#if isOpen}
		<div
			use:portal
			in:fly={{ y: variant === 'multiview' ? -10 : 10, duration: 200 }}
			out:fade={{ duration: 150 }}
			style={variant === 'liveroom' ? fixedStyle : ''}
			class="{variant === 'multiview'
				? 'absolute right-0 mt-2 bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700/50 z-50'
				: 'bg-zinc-900 border border-white/10 shadow-2xl'} w-48 rounded-xl overflow-hidden"
		>
			<div class="py-1">
				<div
					class="px-4 py-2 text-xs font-bold uppercase tracking-wider {variant === 'multiview'
						? 'text-slate-500 dark:text-zinc-400 border-b border-slate-100 dark:border-zinc-700/50'
						: 'text-zinc-400 border-b border-white/10'}"
				>
					{t('theater.live.video_stability.title')}
				</div>
				{#each Object.keys(HLS_MODES) as key}
					<button
						onclick={(e) => {
							e.stopPropagation();
							setMode(key);
						}}
						class="w-full cursor-pointer text-left px-4 py-3 text-sm flex items-center gap-2 transition-colors {hlsSettings.mode ===
						key
							? variant === 'multiview'
								? 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-500 font-bold'
								: 'bg-red-500/10 text-red-500 font-bold'
							: variant === 'multiview'
								? 'text-slate-700 hover:bg-slate-50 dark:text-zinc-300 dark:hover:bg-zinc-700/50 dark:hover:text-white'
								: 'text-zinc-300 hover:bg-white/5 hover:text-white'}"
					>
						<div
							class="w-2 h-2 rounded-full {hlsSettings.mode === key
								? 'bg-red-500'
								: 'bg-transparent'}"
						></div>
						{getModeLabel(key)}
					</button>
				{/each}
			</div>
		</div>
	{/if}
</div>
