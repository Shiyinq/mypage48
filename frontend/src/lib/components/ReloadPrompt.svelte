<script lang="ts">
	import { useRegisterSW } from 'virtual:pwa-register/svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Sparkles } from 'lucide-svelte';

	const { t } = useTranslation();

	const { needRefresh, updateServiceWorker } = useRegisterSW({
		onRegistered(r: ServiceWorkerRegistration | undefined) {
			console.log('SW Registered:', r);
		},
		onRegisterError(error: unknown) {
			console.error('SW registration error', error);
		}
	});
</script>

{#if $needRefresh}
	<div
		class="fixed left-4 right-4 bottom-24 sm:left-auto sm:right-6 sm:bottom-6 sm:w-[360px] z-[10000] bg-white/95 dark:bg-zinc-900/95 backdrop-blur-xl p-5 rounded-2xl shadow-[0_10px_40px_rgba(0,0,0,0.1)] dark:shadow-[0_10px_40px_rgba(0,0,0,0.5)] border border-gray-200/50 dark:border-white/10 flex flex-col gap-4 animate-[slideInUp_0.4s_cubic-bezier(0.16,1,0.3,1)]"
	>
		<div class="flex items-start gap-4">
			<div class="bg-red-500/10 dark:bg-red-500/20 p-2.5 rounded-full shrink-0 mt-0.5">
				<Sparkles class="w-5 h-5 text-red-600 dark:text-red-500" />
			</div>
			<div class="flex flex-col gap-1">
				<h3 class="text-sm font-bold text-gray-900 dark:text-white leading-tight">
					{t('pwa.new_version')}
				</h3>
				<p class="text-xs text-gray-500 dark:text-zinc-400 leading-relaxed">
					{t('pwa.description')}
				</p>
			</div>
		</div>

		<div class="flex gap-2 w-full pt-1">
			<button
				onclick={() => ($needRefresh = false)}
				class="flex-1 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 py-2.5 px-4 rounded-xl text-xs font-bold transition-all cursor-pointer"
			>
				{t('pwa.later')}
			</button>
			<button
				onclick={() => updateServiceWorker(true)}
				class="flex-1 bg-red-600 hover:bg-red-700 text-white py-2.5 px-4 rounded-xl text-xs font-bold transition-all shadow-[0_4px_15px_rgba(220,38,38,0.25)] hover:shadow-[0_6px_20px_rgba(220,38,38,0.4)] active:scale-[0.98] cursor-pointer"
			>
				{t('pwa.reload')}
			</button>
		</div>
	</div>
{/if}
