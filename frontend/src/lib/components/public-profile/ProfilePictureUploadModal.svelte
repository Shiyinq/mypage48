<script lang="ts">
	import { X, LoaderCircle } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		previewImage: string;
		isUploading?: boolean;
		onclose?: () => void;
		onsave?: () => void;
	}

	let { previewImage, isUploading = false, onclose, onsave }: Props = $props();

	const { t } = useTranslation();

	function close() {
		onclose?.();
	}

	function save() {
		onsave?.();
	}

	// Handle escape key
	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') close();
	}
</script>

<div
	class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
	role="button"
	tabindex="-1"
	aria-label="Close dialog"
	onclick={close}
	onkeydown={handleKeydown}
>
	<div
		class="bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl max-w-md w-full overflow-hidden animate-[fadeIn_0.2s_ease-out]"
		onclick={(e) => e.stopPropagation()}
		onkeydown={(e) => e.stopPropagation()}
		role="dialog"
		aria-modal="true"
		aria-labelledby="preview-modal-title"
		tabindex="-1"
	>
		<!-- Header -->
		<div
			class="flex items-center justify-between p-4 border-b border-gray-100 dark:border-zinc-800"
		>
			<h3 id="preview-modal-title" class="text-lg font-bold text-gray-900 dark:text-white">
				{t('profile.profilePicture.previewTitle')}
			</h3>
			<button
				class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
				onclick={close}
			>
				<X class="w-5 h-5 text-gray-500" />
			</button>
		</div>

		<!-- Preview Image -->
		<div class="p-6 flex justify-center">
			<div
				class="w-48 h-48 rounded-full overflow-hidden border-4 border-gray-200 dark:border-zinc-700 shadow-lg"
			>
				<img src={previewImage} alt="Preview" class="w-full h-full object-cover" />
			</div>
		</div>

		<!-- Actions -->
		<div class="flex gap-3 p-4 border-t border-gray-100 dark:border-zinc-800">
			<button
				class="flex-1 py-3 px-4 rounded-xl font-bold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 transition-colors cursor-pointer disabled:cursor-not-allowed"
				onclick={close}
				disabled={isUploading}
			>
				{t('common.cancel')}
			</button>
			<button
				class="flex-1 py-3 px-4 rounded-xl font-bold text-white bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 transition-all disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed flex items-center justify-center gap-2"
				onclick={save}
				disabled={isUploading}
			>
				{#if isUploading}
					<LoaderCircle class="w-5 h-5 animate-spin" />
					{t('common.loading')}
				{:else}
					{t('common.save')}
				{/if}
			</button>
		</div>
	</div>
</div>
