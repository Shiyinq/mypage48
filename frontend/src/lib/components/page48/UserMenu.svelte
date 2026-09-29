<script lang="ts">
	import { Flag } from 'lucide-svelte';
	import { portal } from '$lib/actions/portal';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		onReport?: () => void;
	}

	let { onReport }: Props = $props();

	const { t } = useTranslation();

	let open = $state(false);
	let x = $state(0);
	let y = $state(0);
	let btn: HTMLButtonElement | undefined = $state();

	function toggle(e: MouseEvent) {
		e.stopPropagation();
		if (open) {
			open = false;
			return;
		}
		if (btn) {
			const rect = btn.getBoundingClientRect();
			x = Math.max(8, Math.min(rect.right - 224, window.innerWidth - 232));
			y = rect.bottom + 6;
		}
		open = true;
	}

	function run(action?: () => void) {
		open = false;
		action?.();
	}
</script>

<button
	bind:this={btn}
	onclick={toggle}
	class="p-1 rounded-full text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
	aria-label={t('page48.aria.more')}
	aria-haspopup="menu"
	aria-expanded={open}
>
	<svg aria-hidden="true" viewBox="0 0 24 24" class="w-5 h-5 fill-current"
		><circle cx="12" cy="12" r="1.5"></circle><circle cx="19.5" cy="12" r="1.5"></circle><circle
			cx="4.5"
			cy="12"
			r="1.5"
		></circle></svg
	>
</button>

{#if open}
	<div
		use:portal
		class="fixed inset-0 z-[10040]"
		onclick={() => (open = false)}
		role="presentation"
	>
		<div
			class="absolute w-56 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xl overflow-hidden"
			style={`left:${x}px; top:${y}px;`}
			onclick={(e) => e.stopPropagation()}
			role="presentation"
		>
			<button
				class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[14px] font-medium whitespace-nowrap text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
				onclick={() => run(onReport)}
			>
				<Flag size={15} />
				{t('page48.reportUser')}
			</button>
		</div>
	</div>
{/if}
