<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		exportStore,
		isExportLoading,
		isExportProcessing,
		isExportDownloading
	} from '$lib/stores/export.svelte';
	import { showToast } from '$lib/stores';
	import { Database, Download, LoaderCircle, CircleAlert } from 'lucide-svelte';

	const { t } = useTranslation();

	let pollInterval: ReturnType<typeof setInterval> | null = null;

	const pollStatus = async (background = false) => {
		const res = await exportStore.loadStatus(background);

		if (res.status === 'PROCESSING') {
			if (!pollInterval) {
				pollInterval = setInterval(() => pollStatus(true), 5000);
			}
		} else {
			if (res.status === 'FAILED') {
				showToast(res.message || $t('common.error'), 'error');
			}

			if (pollInterval) {
				clearInterval(pollInterval);
				pollInterval = null;
			}
		}
	};

	$effect(() => {
		pollStatus();
		return () => {
			if (pollInterval) {
				clearInterval(pollInterval);
				pollInterval = null;
			}
		};
	});

	const handleRequestExport = async () => {
		try {
			await exportStore.initiate();
			showToast($t('settings.exportData.requested'), 'success');
			pollStatus(true); // Start polling immediately in background
		} catch {
			showToast($t('common.error'), 'error');
		}
	};

	const handleDownload = async () => {
		try {
			const blob = await exportStore.download();

			const downloadUrl = window.URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = downloadUrl;
			link.download = 'mypage48_export.zip';
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			window.URL.revokeObjectURL(downloadUrl);

			// Refresh status to show IDLE/deleted
			setTimeout(() => {
				pollStatus();
			}, 2000);
		} catch {
			showToast($t('common.error'), 'error');
		}
	};

	let { status, expiresAt } = $derived(exportStore);
	let isExpired = $derived(expiresAt ? new Date(expiresAt) < new Date() : false);
</script>

<div class="glass-panel p-6 rounded-3xl animate-fade-in relative overflow-hidden group">
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
		<div class="flex items-start gap-4">
			<div
				class="p-3 rounded-2xl bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm mt-1"
			>
				<Database class="w-6 h-6" />
			</div>
			<div>
				<h3 class="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
					{$t('settings.exportData.title')}
					{#if status === 'PROCESSING'}
						<span class="inline-flex h-2 w-2 rounded-full bg-yellow-500 animate-pulse"></span>
					{/if}
				</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-md">
					{$t('settings.exportData.description')}
				</p>

				{#if expiresAt && status === 'COMPLETED' && !isExpired}
					<div
						class="mt-2 text-xs font-medium text-orange-500 flex items-center gap-1.5 bg-orange-50 dark:bg-orange-900/10 px-2 py-1 rounded-lg w-fit"
					>
						<CircleAlert class="w-3.5 h-3.5" />
						{$t('settings.exportData.expiresAt', { time: new Date(expiresAt).toLocaleString() })}
					</div>
				{/if}
			</div>
		</div>

		<div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
			{#if isExportLoading.value}
				<div
					class="h-12 w-full sm:w-32 bg-gray-100 dark:bg-gray-800 rounded-xl animate-pulse"
				></div>
			{:else if status === 'PROCESSING'}
				<div
					class="flex items-center justify-center gap-3 px-5 py-3 bg-gray-100 dark:bg-gray-800 rounded-xl text-gray-500 dark:text-gray-400 font-bold whitespace-nowrap"
				>
					<LoaderCircle class="w-5 h-5 animate-spin" />
					<span class="text-sm">{$t('settings.exportData.processing')}</span>
				</div>
			{:else if status === 'COMPLETED' && !isExpired}
				<button
					class="py-3.5 px-6 rounded-xl bg-red-600 text-white font-black uppercase text-xs tracking-widest hover:bg-red-700 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-red-500/30 hover:shadow-red-500/50 whitespace-nowrap disabled:opacity-70 disabled:cursor-not-allowed w-full sm:w-auto"
					onclick={handleDownload}
					disabled={isExportDownloading.value}
				>
					{#if isExportDownloading.value}
						<LoaderCircle class="w-4 h-4 animate-spin" />
					{:else}
						<Download class="w-4 h-4" />
					{/if}
					{$t('settings.exportData.download')}
				</button>
			{:else}
				<button
					class="py-3.5 px-6 rounded-xl bg-gray-900 dark:bg-zinc-800 text-white dark:text-gray-100 font-black uppercase text-xs tracking-widest hover:bg-black dark:hover:bg-zinc-700 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-gray-300 dark:shadow-zinc-900/50 whitespace-nowrap min-w-[180px] w-full sm:w-auto"
					onclick={handleRequestExport}
					disabled={isExportProcessing.value}
				>
					{#if isExportProcessing.value}
						<LoaderCircle class="w-4 h-4 animate-spin" />
					{:else}
						<CircleAlert class="w-4 h-4" />
					{/if}
					{$t('settings.exportData.request')}
				</button>
			{/if}
		</div>
	</div>
</div>
