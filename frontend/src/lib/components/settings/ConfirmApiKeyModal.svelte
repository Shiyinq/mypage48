<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { AlertTriangle } from 'lucide-svelte';

	const { t } = useTranslation();
	const dispatch = createEventDispatcher<{ cancel: void; confirm: void }>();

	export let show = false;

	const handleCancel = () => {
		dispatch('cancel');
	};

	const handleConfirm = () => {
		dispatch('confirm');
	};
</script>

{#if show}
	<div
		class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
	>
		<div
			class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl animate-scale-in p-6"
		>
			<div class="text-center mb-6">
				<div
					class="w-14 h-14 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-amber-200 dark:shadow-amber-900/50"
				>
					<AlertTriangle class="w-7 h-7 text-white" />
				</div>
				<h3 class="text-xl font-bold text-gray-900 dark:text-gray-100">
					{$t('settings.developer.confirmTitle')}
				</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-2">
					{$t('settings.developer.confirmDescription')}
				</p>
			</div>

			<div class="flex gap-3">
				<button
					class="flex-1 py-3 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 rounded-xl font-bold hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors cursor-pointer"
					on:click={handleCancel}
				>
					{$t('common.cancel')}
				</button>
				<button
					class="flex-1 py-3 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 transition-colors cursor-pointer"
					on:click={handleConfirm}
				>
					{$t('common.confirm')}
				</button>
			</div>
		</div>
	</div>
{/if}
