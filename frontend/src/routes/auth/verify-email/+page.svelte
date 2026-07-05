<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth.svelte';
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { getErrorMessage } from '$lib/utils/api';
	import { CircleCheck, CircleX, LoaderCircle } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import AppBackground from '$lib/components/common/AppBackground.svelte';

	const { t } = useTranslation();

	let status: 'loading' | 'success' | 'error' = $state('loading');
	let message = $state(t('auth.verifyEmail.loadingMessage'));

	onMount(async () => {
		const token = $page.url.searchParams.get('token');

		if (!token) {
			status = 'error';
			message = t('auth.verifyEmail.invalidLink');
			return;
		}

		try {
			await authStore.verifyEmail({ token });
			status = 'success';
			message = t('auth.verifyEmail.successMessage');
			showToast(t('auth.verifyEmail.successMessage'), 'success');
			setTimeout(() => {
				goto('/login');
			}, 10000);
		} catch (err) {
			const errorMsg = getErrorMessage(err);
			logger.error('Email verification failed', err, { context: 'VerifyEmailPage' });
			status = 'error';
			message = errorMsg || t('auth.verifyEmail.failedMessage');
		}
	});
</script>

<SEO
	title={t('auth.verifyEmail.loadingTitle')}
	path="/auth/verify-email"
	description={t('seo.verifyEmail')}
/>

<div
	class="min-h-screen flex items-center justify-center p-3 relative overflow-hidden py-4 sm:py-6 bg-gradient-to-b from-pink-50/20 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 font-sans selection:bg-red-500/20"
>
	<!-- Background Elements -->
	<AppBackground hideDecorationsOnMobile={true} />

	<div class="w-full max-w-md px-1">
		<div
			class="glass-panel p-5 sm:p-7 rounded-[2rem] shadow-sm border border-gray-200/50 dark:border-zinc-800/80 backdrop-blur-xl transition-all text-center"
		>
			<div class="flex justify-center mb-6">
				{#if status === 'loading'}
					<div
						class="w-16 h-16 rounded-full bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center"
					>
						<LoaderCircle class="w-8 h-8 text-blue-500" />
					</div>
				{:else if status === 'success'}
					<div
						class="w-16 h-16 rounded-full bg-green-50 dark:bg-green-900/20 flex items-center justify-center"
					>
						<CircleCheck class="w-8 h-8 text-green-500" />
					</div>
				{:else}
					<div
						class="w-16 h-16 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center"
					>
						<CircleX class="w-8 h-8 text-red-500" />
					</div>
				{/if}
			</div>

			<h1 class="text-2xl font-black text-gray-900 dark:text-white mb-2">
				{#if status === 'loading'}
					{t('auth.verifyEmail.loadingTitle')}
				{:else if status === 'success'}
					{t('auth.verifyEmail.successTitle')}
				{:else}
					{t('auth.verifyEmail.errorTitle')}
				{/if}
			</h1>

			<p class="text-gray-500 dark:text-gray-400 font-medium mb-8">
				{message}
			</p>

			{#if status === 'error'}
				<div
					class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50 p-4 rounded-2xl mb-8 text-left text-sm text-red-800 dark:text-red-200 leading-relaxed"
				>
					{t('auth.verifyEmail.resendInfo')}
				</div>

				<button
					onclick={() => goto('/login')}
					class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-sm hover:shadow-md hover:scale-[1.01] transition-all active:scale-95 flex items-center justify-center gap-2 cursor-pointer border border-white/20"
				>
					{t('auth.verifyEmail.backToLogin')}
				</button>
			{:else if status === 'success'}
				<button
					onclick={() => goto('/login')}
					class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-sm hover:shadow-md hover:scale-[1.01] transition-all active:scale-95 flex items-center justify-center gap-2 cursor-pointer border border-white/20"
				>
					{t('auth.verifyEmail.goToLogin')}
				</button>
			{/if}
		</div>
	</div>
</div>
