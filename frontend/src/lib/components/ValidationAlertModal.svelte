<script lang="ts">
	import { CircleAlert } from 'lucide-svelte';
	import { fade, scale } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let show: boolean = false;
	export let title: string = '';
	export let message: string = '';
	export let onClose: () => void;

	const { t } = useTranslation();

	function handleBackdropClick() {
		onClose();
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onClose();
	}
</script>

{#if show}
	<div
		class="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
		on:click={handleBackdropClick}
		on:keydown={handleKeydown}
		transition:fade={{ duration: 150 }}
		role="button"
		tabindex="-1"
		aria-label="Close dialog"
	>
		<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
		<div
			class="bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl max-w-sm w-full p-6"
			on:click|stopPropagation
			on:keydown|stopPropagation
			transition:scale={{ duration: 200, start: 0.95 }}
			role="dialog"
			aria-modal="true"
			aria-labelledby="validation-alert-title"
			tabindex="-1"
		>
			<!-- Icon -->
			<div
				class="w-14 h-14 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-500 flex items-center justify-center mb-4 mx-auto"
			>
				<CircleAlert class="w-7 h-7" />
			</div>

			<!-- Content -->
			<div class="text-center mb-6">
				<h3
					id="validation-alert-title"
					class="text-xl font-bold text-gray-900 dark:text-white mb-2"
				>
					{title || $t('validation.alert.title')}
				</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
					{message}
				</p>
			</div>

			<!-- Action -->
			<button
				on:click={onClose}
				class="w-full px-4 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 shadow-lg shadow-amber-200 dark:shadow-none transition-all cursor-pointer"
			>
				{$t('common.ok')}
			</button>
		</div>
	</div>
{/if}
