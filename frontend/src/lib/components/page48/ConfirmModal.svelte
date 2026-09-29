<script lang="ts">
	import { portal } from '$lib/actions/portal';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { fade } from 'svelte/transition';

	interface Props {
		title: string;
		message: string;
		confirmText: string;
		cancelText?: string;
		destructive?: boolean;
		onConfirm: () => void | Promise<void>;
		onCancel: () => void;
	}

	let {
		title,
		message,
		confirmText,
		cancelText,
		destructive = false,
		onConfirm,
		onCancel
	}: Props = $props();

	const { t } = useTranslation();

	let busy = $state(false);

	async function confirm() {
		if (busy) return;
		busy = true;
		try {
			await onConfirm();
		} finally {
			busy = false;
		}
	}
</script>

<div
	use:portal
	class="fixed inset-0 z-[10060] flex items-center justify-center p-4"
	transition:fade={{ duration: 150 }}
	role="dialog"
	aria-modal="true"
>
	<div
		class="absolute inset-0 bg-black/60 backdrop-blur-sm"
		onclick={onCancel}
		role="presentation"
	></div>

	<div
		class="relative w-full max-w-sm rounded-2xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 p-5 shadow-2xl"
	>
		<h3 class="text-base font-bold text-gray-900 dark:text-gray-100">{title}</h3>
		<p class="text-[14px] text-gray-500 dark:text-gray-400 mt-2 leading-relaxed">{message}</p>

		<div class="flex justify-end gap-2 mt-5">
			<button
				class="px-4 py-2 rounded-full border border-gray-200 dark:border-zinc-800 text-[13px] font-semibold text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
				onclick={onCancel}
				disabled={busy}
			>
				{cancelText ?? t('common.cancel')}
			</button>
			<button
				class={`px-4 py-2 rounded-full text-[13px] font-semibold transition-colors cursor-pointer disabled:opacity-50 ${
					destructive
						? 'bg-red-600 hover:bg-red-700 text-white'
						: 'bg-black dark:bg-white text-white dark:text-black hover:bg-gray-800 dark:hover:bg-gray-200'
				}`}
				onclick={confirm}
				disabled={busy}
			>
				{confirmText}
			</button>
		</div>
	</div>
</div>
