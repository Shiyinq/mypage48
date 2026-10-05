<script lang="ts">
	import { Pencil, Trash2, Flag, Pin, PinOff, Activity, Lock, Unlock } from 'lucide-svelte';
	import { portal } from '$lib/actions/portal';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		isOwner: boolean;
		/** Only meaningful on the author's own post. */
		isPinned?: boolean;
		/** Whether the post is visible only to its author. */
		isPrivate?: boolean;
		onEdit?: () => void;
		onDelete?: () => void;
		onReport?: () => void;
		onTogglePin?: () => void;
		/** Toggles the post between private and public (top-level posts only). */
		onTogglePrivate?: () => void;
		/** Opens the post's activity page (quotes / reposts / likes). */
		onViewActivity?: () => void;
	}

	let {
		isOwner,
		isPinned = false,
		isPrivate = false,
		onEdit,
		onDelete,
		onReport,
		onTogglePin,
		onTogglePrivate,
		onViewActivity
	}: Props = $props();

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
			x = Math.max(8, Math.min(rect.right - 192, window.innerWidth - 200));
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
	class="text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 cursor-pointer"
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
			class="absolute w-48 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xl overflow-hidden"
			style={`left:${x}px; top:${y}px;`}
			onclick={(e) => e.stopPropagation()}
			role="presentation"
		>
			{#if onViewActivity}
				<button
					class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[14px] font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
					onclick={() => run(onViewActivity)}
				>
					<Activity size={15} />
					{t('page48.activity.view')}
				</button>
			{/if}
			{#if isOwner}
				{#if onTogglePrivate}
					<button
						class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[14px] font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
						onclick={() => run(onTogglePrivate)}
					>
						{#if isPrivate}
							<Unlock size={15} />
							{t('page48.menu.makePublic')}
						{:else}
							<Lock size={15} />
							{t('page48.menu.makePrivate')}
						{/if}
					</button>
				{/if}
				{#if onTogglePin}
					<button
						class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[14px] font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
						onclick={() => run(onTogglePin)}
					>
						{#if isPinned}
							<PinOff size={15} />
							{t('page48.menu.unpin')}
						{:else}
							<Pin size={15} />
							{t('page48.menu.pin')}
						{/if}
					</button>
				{/if}
				<button
					class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[14px] font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
					onclick={() => run(onEdit)}
				>
					<Pencil size={15} />
					{t('page48.menu.edit')}
				</button>
				<button
					class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[14px] font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors cursor-pointer"
					onclick={() => run(onDelete)}
				>
					<Trash2 size={15} />
					{t('page48.menu.delete')}
				</button>
			{:else}
				<button
					class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[14px] font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
					onclick={() => run(onReport)}
				>
					<Flag size={15} />
					{t('page48.menu.report')}
				</button>
			{/if}
		</div>
	</div>
{/if}
