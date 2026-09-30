<script lang="ts">
	import { Repeat2, Quote } from 'lucide-svelte';
	import { portal } from '$lib/actions/portal';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		isReposted: boolean;
		count: number;
		cursorClass?: string;
		/** Public visitors may hover but not open the menu. */
		disabled?: boolean;
		onRepost: () => void;
		onQuote: () => void;
	}

	let {
		isReposted,
		count,
		cursorClass = 'cursor-pointer',
		disabled = false,
		onRepost,
		onQuote
	}: Props = $props();

	const { t } = useTranslation();

	let open = $state(false);
	let x = $state(0);
	let y = $state(0);
	let btn: HTMLButtonElement | undefined = $state();

	function toggle(e: MouseEvent) {
		e.stopPropagation();
		if (disabled) return;
		if (open) {
			open = false;
			return;
		}
		if (btn) {
			const rect = btn.getBoundingClientRect();
			x = Math.max(8, Math.min(rect.left, window.innerWidth - 216));
			y = rect.bottom + 6;
		}
		open = true;
	}

	function run(action: () => void) {
		open = false;
		action();
	}
</script>

<button
	bind:this={btn}
	class={`pointer-events-auto flex items-center gap-1.5 p-2 rounded-full ${cursorClass} hover:bg-green-50 dark:hover:bg-green-950/40 hover:text-green-500 transition-all group/btn`}
	aria-label={t('page48.aria.repost')}
	aria-haspopup="menu"
	aria-expanded={open}
	aria-disabled={disabled}
	onclick={toggle}
>
	<Repeat2
		size={18}
		class={`transition-transform group-active/btn:scale-90 ${isReposted ? 'text-green-500' : ''}`}
	/>
	{#if count > 0}
		<span class={`text-[13px] font-medium ${isReposted ? 'text-green-500' : ''}`}>{count}</span>
	{/if}
</button>

{#if open}
	<div
		use:portal
		class="fixed inset-0 z-[10040]"
		onclick={() => (open = false)}
		role="presentation"
	>
		<div
			class="absolute w-52 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xl overflow-hidden"
			style={`left:${x}px; top:${y}px;`}
			onclick={(e) => e.stopPropagation()}
			role="presentation"
		>
			<button
				class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[14px] font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
				onclick={() => run(onRepost)}
			>
				<Repeat2 size={15} class={isReposted ? 'text-green-500' : ''} />
				{isReposted ? t('page48.repostMenu.undo') : t('page48.repostMenu.repost')}
			</button>
			<button
				class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[14px] font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
				onclick={() => run(onQuote)}
			>
				<Quote size={15} />
				{t('page48.repostMenu.quote')}
			</button>
		</div>
	</div>
{/if}
