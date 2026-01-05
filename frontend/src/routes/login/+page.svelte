<script lang="ts">
	import { goto } from '$app/navigation';
	import { isAuthenticated, showToast } from '$lib/stores';
	import { authStore } from '$lib/stores/auth';
	import { Lock, Mail, ArrowRight, User } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import AuthLayout from '$lib/components/layouts/AuthLayout.svelte';

	const { t } = useTranslation();

	let email = '';
	let password = '';
	let isLoading = false;
	let error: string | null = null;

	const handleSubmit = async () => {
		isLoading = true;
		error = null;
		try {
			await authStore.login({ username: email, password });
			isAuthenticated.set(true);
			showToast($t('auth.login.welcomeBack'));
			goto('/');
		} catch (err) {
			const e = err as { detail?: string; message?: string };
			console.error(e);

			if (e.detail) {
				error = e.detail;
			} else if (e.message) {
				error = e.message;
			} else {
				error = $t('auth.login.failed');
			}

			showToast(error || $t('common.error'), 'error');
		} finally {
			isLoading = false;
		}
	};
</script>

<SEO title={$t('auth.login.title')} path="/login" description={$t('seo.login')} />

<AuthLayout title={$t('auth.login.title')} subtitle={$t('auth.login.subtitle')}>
	<form on:submit|preventDefault={handleSubmit} class="space-y-5">
		<div>
			<label
				for="email"
				class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
				>{$t('auth.login.emailLabel')}</label
			>
			<div class="relative">
				<div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
					<Mail class="w-5 h-5" />
				</div>
				<input
					type="email"
					id="email"
					required
					bind:value={email}
					class="w-full pl-12 pr-4 py-3.5 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none font-medium text-gray-900 dark:text-white transition-all placeholder-gray-400 dark:placeholder-zinc-600"
					placeholder={$t('auth.login.emailPlaceholder')}
				/>
			</div>
		</div>

		<div>
			<label
				for="password"
				class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
				>{$t('auth.login.passwordLabel')}</label
			>
			<div class="relative">
				<div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
					<Lock class="w-5 h-5" />
				</div>
				<input
					type="password"
					id="password"
					required
					bind:value={password}
					class="w-full pl-12 pr-4 py-3.5 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none font-medium text-gray-900 dark:text-white transition-all placeholder-gray-400 dark:placeholder-zinc-600"
					placeholder={$t('auth.login.passwordPlaceholder')}
				/>
			</div>
		</div>

		<div class="flex justify-end">
			<a
				href="/auth/forgot-password"
				class="text-xs font-bold text-red-600 hover:text-red-700 hover:underline"
			>
				{$t('auth.login.forgotPassword')}
			</a>
		</div>

		<button
			type="submit"
			disabled={isLoading}
			class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.02] transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
		>
			{#if isLoading}
				<span class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"
				></span>
			{:else}
				{$t('auth.login.signIn')} <ArrowRight class="w-5 h-5" />
			{/if}
		</button>
	</form>

	<div slot="footer">
		<p class="text-sm text-gray-500 dark:text-gray-400">{$t('auth.login.noAccount')}</p>
		<button
			on:click={() => goto('/register')}
			class="mt-2 text-red-600 font-bold text-sm hover:underline flex items-center justify-center gap-1 mx-auto cursor-pointer"
		>
			{$t('auth.login.registerCta')}
			<User class="w-4 h-4" />
		</button>
	</div>
</AuthLayout>
