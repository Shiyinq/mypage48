<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Key, Copy } from 'lucide-svelte';

	const { t } = useTranslation();

	interface Props {
		show?: boolean;
		apiKey?: string | null;
		oncopy?: () => void;
		onclose?: () => void;
	}

	let { show = false, apiKey = null, oncopy, onclose }: Props = $props();

	const handleCopy = () => {
		oncopy?.();
	};

	const handleClose = () => {
		onclose?.();
	};
</script>

{#if show}
	<div
		class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
	>
		<div
			class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-scale-in p-6"
		>
			<div class="text-center mb-6">
				<div
					class="w-14 h-14 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-green-200 dark:shadow-green-900/50"
				>
					<Key class="w-7 h-7 text-white" />
				</div>
				<h3 class="text-xl font-bold text-gray-900 dark:text-gray-100">
					{$t('settings.developer.generated')}
				</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-2">
					{$t('settings.developer.copyInfo')}
				</p>
			</div>

			<div
				class="bg-gray-50 dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700 mb-6 relative group"
			>
				<code class="text-sm font-mono text-gray-800 dark:text-gray-200 break-all pr-10"
					>{apiKey}</code
				>
				<button
					class="absolute top-3 right-3 p-2 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:border-gray-300 dark:hover:border-gray-500 transition-all shadow-sm cursor-pointer"
					onclick={handleCopy}
					title={$t('settings.developer.copied')}
				>
					<Copy class="w-4 h-4" />
				</button>
			</div>

			<button
				class="w-full py-3 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-xl font-bold hover:bg-black dark:hover:bg-white transition-colors cursor-pointer"
				onclick={handleClose}
			>
				{$t('settings.developer.savedKey')}
			</button>
		</div>
	</div>
{/if}
