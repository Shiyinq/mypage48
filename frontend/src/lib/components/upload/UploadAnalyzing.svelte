<script lang="ts">
	import { ScanLine } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();
</script>

<div
	class="h-[80vh] flex flex-col items-center justify-center text-gray-400 space-y-6 animate-fade-in"
>
	<div class="relative">
		<div class="w-20 h-20 border-4 border-red-100 border-t-red-600 rounded-full animate-spin"></div>
		<div class="absolute inset-0 flex items-center justify-center">
			<ScanLine class="w-8 h-8 text-red-600 animate-pulse" />
		</div>
	</div>
	<div class="hidden sm:block text-center">
		<h3 class="text-xl font-bold text-gray-800">{$t('upload.analyzingTitle')}</h3>
		<p class="text-sm text-gray-500 mt-1">{$t('upload.analyzingDescription')}</p>
	</div>
</div>
