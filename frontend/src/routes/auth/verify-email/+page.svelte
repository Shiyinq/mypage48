<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	import { showToast } from '$lib/stores';
	import { CircleCheck, CircleX, LoaderCircle } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	let status: 'loading' | 'success' | 'error' = 'loading';
	let message = $t('auth.verifyEmail.loadingMessage');

	onMount(async () => {
		const token = $page.url.searchParams.get('token');

		if (!token) {
			status = 'error';
			message = $t('auth.verifyEmail.invalidLink');
			return;
		}

		try {
			await authStore.verifyEmail({ token });
			status = 'success';
			message = $t('auth.verifyEmail.successMessage');
			showToast($t('auth.verifyEmail.successMessage'), 'success');
			setTimeout(() => {
				goto('/login');
			}, 3000);
		} catch (err) {
			const e = err as { detail?: string; message?: string };
			console.error(e);
			status = 'error';
			message = e.detail || e.message || $t('auth.verifyEmail.failedMessage');
		}
	});
</script>

<SEO
	title={$t('auth.verifyEmail.loadingTitle')}
	path="/auth/verify-email"
	description={$t('seo.verifyEmail')}
/>

<div
	class="min-h-screen flex items-center justify-center p-4 bg-gray-50 dark:bg-zinc-950 relative overflow-hidden"
>
	<!-- Background decorations matching login/register -->
	<div class="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
		<div
			class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-red-500/10 blur-[100px] animate-pulse"
		></div>
		<div
			class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-500/10 blur-[100px] animate-pulse"
		></div>
	</div>

	<div class="w-full max-w-md">
		<div
			class="bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl p-8 rounded-3xl shadow-2xl border border-white/60 dark:border-zinc-800 text-center animate-fade-in"
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
					{$t('auth.verifyEmail.loadingTitle')}
				{:else if status === 'success'}
					{$t('auth.verifyEmail.successTitle')}
				{:else}
					{$t('auth.verifyEmail.errorTitle')}
				{/if}
			</h1>

			<p class="text-gray-500 dark:text-gray-400 font-medium mb-8">
				{message}
			</p>

			{#if status === 'error'}
				<button
					on:click={() => goto('/login')}
					class="w-full py-3 rounded-xl font-bold bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
				>
					{$t('auth.verifyEmail.backToLogin')}
				</button>
			{:else if status === 'success'}
				<button
					on:click={() => goto('/login')}
					class="w-full py-3 rounded-xl font-bold idol-gradient text-white shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.02] transition-all cursor-pointer"
				>
					{$t('auth.verifyEmail.goToLogin')}
				</button>
			{/if}
		</div>
	</div>
</div>
