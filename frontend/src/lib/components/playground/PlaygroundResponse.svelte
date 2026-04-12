<script lang="ts">
	import { CheckCircle2, XCircle, Copy, Clock, Database, Info } from 'lucide-svelte';
	import { showToast } from '$lib/stores';
	import { fade } from 'svelte/transition';
	import type { ExecutionResult } from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		response?: ExecutionResult | null;
		error?: any;
		duration?: number | null;
		width?: number | string;
	}

	let { response = null, error = null, duration = null, width = '35%' }: Props = $props();

	function copyToClipboard(text: string) {
		navigator.clipboard.writeText(text);
		showToast($t('playground.copied'), 'success');
	}

	let isSuccess = $derived(response && response.status >= 200 && response.status < 300);
	let statusText = $derived(
		response?.statusText || (isSuccess ? $t('common.success') : $t('common.error'))
	);

	let formattedJson = $derived(response?.data ? JSON.stringify(response.data, null, 2) : '');
	let errorJson = $derived(error ? JSON.stringify(error, null, 2) : '');
</script>

<div
	class="flex flex-col h-full bg-gray-50 dark:bg-zinc-900 border-l border-gray-100 dark:border-white/5 shrink-0 p-6 overflow-hidden"
	style="width: {typeof width === 'number' ? width + 'px' : width}"
>
	<div class="flex items-center justify-between mb-6">
		<div class="flex items-center gap-2 text-gray-900 dark:text-white">
			<Database class="w-5 h-5 text-red-500" />
			<h2 class="text-lg font-bold">{$t('playground.response')}</h2>
		</div>
		{#if duration}
			<div
				class="flex items-center gap-1.5 px-3 py-1 bg-white dark:bg-zinc-800 rounded-full border border-gray-100 dark:border-white/5 text-[10px] font-bold text-gray-500 dark:text-gray-400"
			>
				<Clock class="w-3 h-3" />
				{duration}ms
			</div>
		{/if}
	</div>

	{#if response || error}
		<div in:fade={{ duration: 200 }} class="flex-1 flex flex-col space-y-4 overflow-hidden">
			<!-- Status -->
			<div
				class="flex items-center gap-3 p-4 rounded-2xl border {isSuccess
					? 'bg-emerald-50 dark:bg-emerald-900/10 border-emerald-100 dark:border-emerald-900/20 text-emerald-700 dark:text-emerald-400'
					: 'bg-rose-50 dark:bg-rose-900/10 border-rose-100 dark:border-rose-900/20 text-rose-700 dark:text-rose-400'}"
			>
				{#if isSuccess}
					<CheckCircle2 class="w-5 h-5" />
				{:else}
					<XCircle class="w-5 h-5" />
				{/if}
				<div class="flex flex-col">
					<span class="text-sm font-black uppercase tracking-widest"
						>{response?.status || error?.status || 'Error'}</span
					>
					<span class="text-xs font-bold opacity-70">{statusText}</span>
				</div>
			</div>

			<!-- Body -->
			<div
				class="flex-1 flex flex-col bg-gray-900 dark:bg-zinc-950 rounded-3xl border border-white/5 overflow-hidden relative"
			>
				<div
					class="flex items-center justify-between px-4 py-3 bg-white/5 border-b border-white/5 backdrop-blur-md"
				>
					<span class="text-[10px] font-black uppercase text-gray-400 tracking-widest">Body</span>
					<button
						onclick={() => copyToClipboard(formattedJson || errorJson)}
						class="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white cursor-pointer"
					>
						<Copy class="w-3.5 h-3.5" />
					</button>
				</div>
				<div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
					<pre
						class="font-mono text-[11px] leading-relaxed {isSuccess
							? 'text-emerald-400'
							: 'text-rose-400'}">{formattedJson || errorJson || '// No content'}</pre>
				</div>
			</div>
		</div>
	{:else}
		<div class="flex-1 flex flex-col items-center justify-center text-center space-y-4 opacity-40">
			<div
				class="w-16 h-16 rounded-full bg-gray-100 dark:bg-zinc-800 flex items-center justify-center"
			>
				<Info class="w-6 h-6 text-gray-400" />
			</div>
			<p class="text-xs font-bold text-gray-500 uppercase tracking-widest leading-relaxed">
				{$t('playground.waitingResponse')}
			</p>
		</div>
	{/if}
</div>

<style>
	pre {
		white-space: pre-wrap;
		word-break: break-all;
	}
	.custom-scrollbar::-webkit-scrollbar {
		width: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.05);
		border-radius: 10px;
	}
</style>
