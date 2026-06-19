<script lang="ts">
	import { TriangleAlert } from 'lucide-svelte';
	import { fade, scale } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		show?: boolean;
		isDeleting?: boolean;
		title?: string;
		description?: string;
		onCancel: () => void;
		onConfirm: () => void;
	}

	let {
		show = false,
		isDeleting = false,
		title,
		description,
		onCancel,
		onConfirm
	}: Props = $props();

	const { t } = useTranslation();
</script>

{#if show}
	<div
		class="fixed inset-0 z-[10005] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
		onclick={onCancel}
		onkeydown={(e) => e.key === 'Escape' && onCancel()}
		transition:fade={{ duration: 150 }}
		role="button"
		tabindex="-1"
		aria-label="Close confirmation modal"
	>
		<div
			class="bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl max-w-sm w-full p-6"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
			transition:scale={{ duration: 200, start: 0.95 }}
			role="dialog"
			aria-modal="true"
			tabindex="-1"
		>
			<div
				class="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-500 flex items-center justify-center mb-4 mx-auto"
			>
				<TriangleAlert class="w-6 h-6" />
			</div>
			<div class="text-center mb-6">
				<h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
					{title || t('history.deleteConfirm.title')}
				</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
					{description || t('history.deleteConfirm.description')}
				</p>
			</div>
			<div class="grid grid-cols-2 gap-3">
				<button
					onclick={onCancel}
					disabled={isDeleting}
					class="px-4 py-2.5 rounded-xl font-bold text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{t('common.cancel')}
				</button>
				<button
					onclick={onConfirm}
					disabled={isDeleting}
					class="px-4 py-2.5 rounded-xl font-bold text-white bg-red-600 hover:bg-red-700 shadow-lg shadow-red-200 dark:shadow-none transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
				>
					{#if isDeleting}
						<div
							class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
						></div>
						{t('common.loading')}
					{:else}
						{t('history.deleteConfirm.confirm')}
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}
